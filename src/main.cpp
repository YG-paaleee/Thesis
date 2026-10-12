#include <Arduino.h>
#include <WiFi.h>
#include <DNSServer.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>
#include <RadioLib.h>
#include <SPI.h>
#include <esp_system.h>
#include <time.h>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>

#include "captive_portal.h"
#include "admin_dashboard.h"
#include "aes_crypto.h"
#include "min_heap.h"
#include "network_core.h"

// ---------------------------------------------------------
// Network & Node Configuration (Barangay San Miguel Testbed)
// ---------------------------------------------------------
const char *AP_SSID = "EMERGENCY-HUB-01";
const byte DNS_PORT = 53;
const uint8_t MAX_AP_CLIENTS = 25; // Connect-Queue-Disconnect Cap (Section 1.1 Limitations)

IPAddress apIP(192, 168, 4, 1);
IPAddress netMsk(255, 255, 255, 0);

DNSServer dnsServer;
AsyncWebServer server(80);

// Global Dual-Key Binary Min-Heap Priority Queue (Section 3.2)
PriorityMinHeap priorityQueue;
SemaphoreHandle_t priorityQueueMutex = nullptr;
SemaphoreHandle_t liveIncidentMutex = nullptr;
constexpr size_t LIVE_INCIDENT_CAPACITY = 10;

struct LiveIncident {
    uint16_t messageId;
    uint8_t priority;
    uint8_t packetType;
    uint8_t originNode;
    int32_t latencyMs;
    uint32_t receivedAtMs;
    char path[64];
    char location[84];
    char message[201];
};

LiveIncident liveIncidents[LIVE_INCIDENT_CAPACITY] = {};
size_t liveIncidentWriteIndex = 0;
size_t liveIncidentCount = 0;

volatile uint16_t globalMessageCounter = 1000;
portMUX_TYPE messageCounterMux = portMUX_INITIALIZER_UNLOCKED;

constexpr uint8_t LORA_NSS_PIN = 8;
constexpr uint8_t LORA_DIO1_PIN = 14;
constexpr uint8_t LORA_RESET_PIN = 12;
constexpr uint8_t LORA_BUSY_PIN = 13;
constexpr uint8_t LORA_SCK_PIN = 9;
constexpr uint8_t LORA_MISO_PIN = 11;
constexpr uint8_t LORA_MOSI_PIN = 10;
constexpr float LORA_FREQUENCY_MHZ = 915.0f;
constexpr uint8_t PACKET_HEADER_SIZE = 1;
constexpr size_t FRAME_PREFIX_SIZE = 8;
constexpr size_t FRAME_AUTH_TAG_SIZE = 32;
constexpr size_t FRAME_OVERHEAD_SIZE = FRAME_PREFIX_SIZE + FRAME_AUTH_TAG_SIZE;
constexpr size_t ACK_PACKET_SIZE = FRAME_OVERHEAD_SIZE;
constexpr size_t MAX_LORA_PACKET_SIZE = 250;
constexpr uint8_t INITIAL_TTL = 15;
constexpr uint32_t HEARTBEAT_INTERVAL_MS = 30000UL;
constexpr uint8_t BATTERY_ADC_PIN = 1;
constexpr uint8_t BATTERY_ADC_ENABLE_PIN = 37;
constexpr float BATTERY_DIVIDER_RATIO = 4.9f;
constexpr uint32_t DTN_RETENTION_MS = 1800000UL;
constexpr uint32_t ACK_TIMEOUT_GUARD_MS = 2500UL;
constexpr uint32_t DTN_FULL_RETRY_MS = 1000UL;
constexpr uint8_t NODE_ID = 1;
constexpr uint8_t HUB_NODE_ID = 1;

constexpr uint8_t PACKET_TYPE_SOS = 0;
constexpr uint8_t PACKET_TYPE_HEARTBEAT = 1;
constexpr uint8_t PACKET_TYPE_TELEMETRY = 2;
constexpr uint8_t PACKET_TYPE_ACK = 3;

constexpr uint8_t MAC_MIN_BACKOFF_EXPONENT = 1;
constexpr uint8_t MAC_MAX_BACKOFF_EXPONENT = 5;
constexpr uint8_t MAC_MAX_CAD_RETRIES = 6;
constexpr uint16_t MAC_SLOT_TIME_MS = 20;
constexpr uint16_t MAC_DEFER_TIME_MS = 1000;

uint8_t adjacencyMatrix[NETWORK_NODE_COUNT][NETWORK_NODE_COUNT] = {
    {0, 1, 1, 1, 0, 0},
    {1, 0, 0, 1, 1, 0},
    {1, 0, 0, 0, 1, 1},
    {1, 1, 0, 0, 0, 0},
    {0, 1, 1, 0, 0, 1},
    {0, 0, 1, 0, 1, 0}
};

SX1262 radio = new Module(LORA_NSS_PIN, LORA_DIO1_PIN, LORA_RESET_PIN, LORA_BUSY_PIN);
 DtnBuffer dtnBuffer;
bool radioReady = false;
volatile bool radioTxDone = false;
volatile bool radioRxPending = false;
bool radioTxInFlight = false;
bool radioAckTxInFlight = false;
bool radioAwaitingAck = false;
bool radioTxFromDtn = false;
uint16_t radioTxMessageId = 0;
uint8_t radioTxOriginNode = 0;
uint8_t radioTxNextHop = 0;
size_t radioTxPacketLen = 0;
uint32_t radioAckDeadlineMs = 0;
EmergencyMessage activeTxMessage{};
uint8_t macBackoffExponent = MAC_MIN_BACKOFF_EXPONENT;
uint8_t macBusyRetries = 0;
uint16_t macBackoffMessageId = 0;
bool macBackoffActive = false;
uint32_t nextMacAttemptAt = 0;
uint8_t radioPacket[MAX_LORA_PACKET_SIZE];
uint8_t ackPacket[ACK_PACKET_SIZE];
uint32_t nextHeartbeatAtMs = 0;
bool csvHeaderPrinted = false;

void resetMacBackoff();

uint16_t allocateMessageId() {
    portENTER_CRITICAL(&messageCounterMux);
    uint16_t id = ++globalMessageCounter;
    portEXIT_CRITICAL(&messageCounterMux);
    return id;
}

bool queuePush(const EmergencyMessage &msg) {
    if (!priorityQueueMutex || xSemaphoreTake(priorityQueueMutex, pdMS_TO_TICKS(1000)) != pdTRUE) return false;
    bool result = priorityQueue.push(msg);
    xSemaphoreGive(priorityQueueMutex);
    return result;
}

bool queuePeek(EmergencyMessage &msg) {
    if (!priorityQueueMutex || xSemaphoreTake(priorityQueueMutex, pdMS_TO_TICKS(100)) != pdTRUE) return false;
    bool result = priorityQueue.peek(msg);
    xSemaphoreGive(priorityQueueMutex);
    return result;
}

bool queueRemoveById(uint16_t id) {
    if (!priorityQueueMutex || xSemaphoreTake(priorityQueueMutex, pdMS_TO_TICKS(100)) != pdTRUE) return false;
    bool result = priorityQueue.removeById(id);
    xSemaphoreGive(priorityQueueMutex);
    return result;
}

size_t queueSize() {
    if (!priorityQueueMutex || xSemaphoreTake(priorityQueueMutex, pdMS_TO_TICKS(100)) != pdTRUE) return 0;
    size_t result = priorityQueue.size();
    xSemaphoreGive(priorityQueueMutex);
    return result;
}

void appendPathNode(char *path, size_t pathSize, uint8_t nodeId) {
    const size_t used = strlen(path);
    if (used >= pathSize) return;
    snprintf(path + used, pathSize - used, "%sV%u", used ? " -> " : "", nodeId);
}

void buildIncidentPath(uint8_t originNode, uint8_t sourceNode, char *path, size_t pathSize) {
    if (!path || pathSize == 0) return;
    path[0] = '\0';

    uint8_t currentNode = originNode;
    appendPathNode(path, pathSize, currentNode);
    for (uint8_t hop = 0; currentNode != sourceNode && hop < NETWORK_NODE_COUNT; hop++) {
        uint8_t nextNode = 0;
        if (!dijkstraNextHop(adjacencyMatrix, currentNode, sourceNode, nextNode) ||
            nextNode == currentNode) {
            path[0] = '\0';
            appendPathNode(path, pathSize, originNode);
            if (sourceNode != originNode) appendPathNode(path, pathSize, sourceNode);
            currentNode = sourceNode;
            break;
        }
        currentNode = nextNode;
        appendPathNode(path, pathSize, currentNode);
    }

    if (currentNode != NODE_ID) appendPathNode(path, pathSize, NODE_ID);
}

int32_t calculateIncidentLatencyMs(uint32_t transmittedAtSeconds) {
    const time_t now = time(nullptr);
    if (transmittedAtSeconds == 0 || now < 1700000000 ||
        (uint64_t)now < transmittedAtSeconds) return -1;
    const uint64_t elapsedMs = ((uint64_t)now - transmittedAtSeconds) * 1000ULL;
    return elapsedMs <= INT32_MAX ? (int32_t)elapsedMs : -1;
}

void recordLiveIncident(uint16_t messageId, uint8_t priority, uint8_t packetType,
                        uint8_t originNode, uint8_t sourceNode, uint32_t transmittedAtSeconds,
                        const char *location, const char *message) {
    if (!liveIncidentMutex ||
        xSemaphoreTake(liveIncidentMutex, pdMS_TO_TICKS(100)) != pdTRUE) return;

    LiveIncident &incident = liveIncidents[liveIncidentWriteIndex];
    incident.messageId = messageId;
    incident.priority = priority;
    incident.packetType = packetType;
    incident.originNode = originNode;
    incident.latencyMs = calculateIncidentLatencyMs(transmittedAtSeconds);
    incident.receivedAtMs = millis();
    buildIncidentPath(originNode, sourceNode, incident.path, sizeof(incident.path));
    snprintf(incident.location, sizeof(incident.location), "%s", location ? location : "Unspecified");
    snprintf(incident.message, sizeof(incident.message), "%s", message ? message : "");

    liveIncidentWriteIndex = (liveIncidentWriteIndex + 1) % LIVE_INCIDENT_CAPACITY;
    if (liveIncidentCount < LIVE_INCIDENT_CAPACITY) liveIncidentCount++;
    xSemaphoreGive(liveIncidentMutex);
}

bool serializeLoRaPacket(const EmergencyMessage &msg, uint8_t nextHopNode,
                         uint8_t *out, size_t capacity, size_t &outLen) {
    outLen = 0;
    if (!out || msg.priority < 1 || msg.priority > 3 || msg.ttl > 15 ||
        msg.packetType > PACKET_TYPE_TELEMETRY || nextHopNode < 1 ||
        nextHopNode > NETWORK_NODE_COUNT || msg.destinationNode < 1 ||
        msg.destinationNode > NETWORK_NODE_COUNT || msg.originNode < 1 ||
        msg.originNode > NETWORK_NODE_COUNT || msg.encryptedLen == 0 ||
        msg.encryptedLen > sizeof(msg.encryptedData) || capacity < FRAME_OVERHEAD_SIZE ||
        (size_t)msg.encryptedLen + FRAME_OVERHEAD_SIZE > capacity ||
        (size_t)msg.encryptedLen + FRAME_OVERHEAD_SIZE > MAX_LORA_PACKET_SIZE) {
        return false;
    }

    out[0] = (uint8_t)(((msg.priority & 0x03) << 6) | ((msg.ttl & 0x0F) << 2) |
                       (msg.packetType & 0x03));
    out[1] = NODE_ID;
    out[2] = nextHopNode;
    out[3] = msg.destinationNode;
    out[4] = msg.originNode;
    out[5] = (uint8_t)(msg.id >> 8);
    out[6] = (uint8_t)(msg.id & 0xFF);
    out[7] = macBusyRetries;
    memcpy(out + FRAME_PREFIX_SIZE, msg.encryptedData, msg.encryptedLen);
    outLen = FRAME_PREFIX_SIZE + msg.encryptedLen;
    if (!AESCrypto::authenticateFrame(out, outLen, out + outLen)) {
        outLen = 0;
        return false;
    }
    outLen += FRAME_AUTH_TAG_SIZE;
    return true;
}

void onRadioPacketSent() {
    radioTxDone = true;
}

void onRadioPacketReceived() {
    radioRxPending = true;
}

bool deadlineReached(uint32_t now, uint32_t deadline) {
    return (int32_t)(now - deadline) >= 0;
}

float readBatteryVoltage() {
    analogReadResolution(12);
    pinMode(BATTERY_ADC_ENABLE_PIN, OUTPUT);
    digitalWrite(BATTERY_ADC_ENABLE_PIN, HIGH);
    delay(10);

    uint32_t millivoltSum = 0;
    constexpr uint8_t SAMPLE_COUNT = 4;
    for (uint8_t sample = 0; sample < SAMPLE_COUNT; sample++) {
        millivoltSum += analogReadMilliVolts(BATTERY_ADC_PIN);
    }

    digitalWrite(BATTERY_ADC_ENABLE_PIN, LOW);
    pinMode(BATTERY_ADC_PIN, INPUT);
    return ((float)millivoltSum / SAMPLE_COUNT) * BATTERY_DIVIDER_RATIO / 1000.0f;
}

void printRxTelemetryCsv(const uint8_t *packet, size_t packetLen,
                         float rssi, float snr, float batteryVoltage) {
    if (!csvHeaderPrinted) {
        Serial.println("Timestamp,MessageID,PacketType,OriginNode,RSSI,SNR,Battery,MAC_Retries");
        csvHeaderPrinted = true;
    }

    uint16_t messageId = 0;
    uint8_t packetType = 0;
    uint8_t originNode = 0;
    uint8_t macRetries = 0;
    if (packet && packetLen >= FRAME_PREFIX_SIZE) {
        packetType = packet[0] & 0x03;
        originNode = packet[4];
        messageId = ((uint16_t)packet[5] << 8) | packet[6];
        macRetries = packet[7];
    }

    Serial.printf("%lu,%u,%u,%u,%.2f,%.2f,%.3f,%u\n",
                  (unsigned long)millis(), messageId, packetType, originNode,
                  rssi, snr, batteryVoltage, macRetries);
}

bool queueHeartbeat() {
    if (!radioReady) return false;

    EmergencyMessage message{};
    message.id = allocateMessageId();
    message.priority = 3;
    message.timestamp_tx = millis() / 1000;
    message.originNode = NODE_ID;
    message.destinationNode = HUB_NODE_ID;
    message.ttl = INITIAL_TTL;
    message.packetType = PACKET_TYPE_HEARTBEAT;
    message.expiresAtMs = millis() + DTN_RETENTION_MS;
    message.retryExponent = MAC_MIN_BACKOFF_EXPONENT;
    snprintf(message.location, sizeof(message.location), "V%u", NODE_ID);
    snprintf(message.payload, sizeof(message.payload), "HEARTBEAT");

    JsonDocument payloadDoc;
    payloadDoc["id"] = message.id;
    payloadDoc["k"] = message.priority;
    payloadDoc["src"] = message.originNode;
    payloadDoc["dst"] = message.destinationNode;
    payloadDoc["ts"] = message.timestamp_tx;
    payloadDoc["loc"] = message.location;
    payloadDoc["msg"] = message.payload;

    char plaintext[128];
    size_t plaintextLen = serializeJson(payloadDoc, plaintext, sizeof(plaintext));
    size_t encryptedLen = 0;
    if (plaintextLen == 0 ||
        !AESCrypto::encrypt(plaintext, plaintextLen, message.encryptedData,
                            encryptedLen, MAX_LORA_PACKET_SIZE - FRAME_OVERHEAD_SIZE)) {
        return false;
    }
    message.encryptedLen = (uint8_t)encryptedLen;
    return queuePush(message);
}

void serviceHeartbeat() {
    const uint32_t now = millis();
    if (!deadlineReached(now, nextHeartbeatAtMs)) return;

    do {
        nextHeartbeatAtMs += HEARTBEAT_INTERVAL_MS;
    } while (deadlineReached(now, nextHeartbeatAtMs));

    queueHeartbeat();
}

void completeDataAcknowledgment() {
    if (radioTxFromDtn) {
        dtnBuffer.remove(radioTxMessageId, radioTxOriginNode);
    } else {
        queueRemoveById(radioTxMessageId);
    }
    Serial.printf("[LORA ACK] Next hop V%u acknowledged packet #%04u.\n",
                  radioTxNextHop, radioTxMessageId);
    radioAwaitingAck = false;
    resetMacBackoff();
}

bool startLinkAck(uint8_t destinationNode, uint8_t originNode, uint16_t messageId) {
    ackPacket[0] = (uint8_t)((PACKET_TYPE_ACK & 0x03));
    ackPacket[1] = NODE_ID;
    ackPacket[2] = destinationNode;
    ackPacket[3] = destinationNode;
    ackPacket[4] = originNode;
    ackPacket[5] = (uint8_t)(messageId >> 8);
    ackPacket[6] = (uint8_t)(messageId & 0xFF);
    ackPacket[7] = 0;
    if (!AESCrypto::authenticateFrame(ackPacket, FRAME_PREFIX_SIZE,
                                      ackPacket + FRAME_PREFIX_SIZE)) return false;

    radioTxDone = false;
    int16_t state = radio.startTransmit(ackPacket, sizeof(ackPacket));
    if (state != RADIOLIB_ERR_NONE) {
        Serial.printf("[LORA ACK] Start failed with code %d.\n", state);
        radio.startReceive();
        return false;
    }
    radioAckTxInFlight = true;
    return true;
}

void handleReceivedPacket(const uint8_t *packet, size_t packetLen) {
    if (!packet || packetLen < FRAME_OVERHEAD_SIZE || packetLen > MAX_LORA_PACKET_SIZE ||
        !AESCrypto::verifyFrame(packet, packetLen - FRAME_AUTH_TAG_SIZE,
                                packet + packetLen - FRAME_AUTH_TAG_SIZE)) return;

    const uint8_t header = packet[0];
    const uint8_t priority = header >> 6;
    const uint8_t ttl = (header >> 2) & 0x0F;
    const uint8_t packetType = header & 0x03;
    const uint8_t sourceNode = packet[1];
    const uint8_t nextHopNode = packet[2];
    const uint8_t destinationNode = packet[3];
    const uint8_t originNode = packet[4];
    const uint16_t messageId = ((uint16_t)packet[5] << 8) | packet[6];

    if (sourceNode < 1 || sourceNode > NETWORK_NODE_COUNT ||
        nextHopNode != NODE_ID || destinationNode < 1 ||
        destinationNode > NETWORK_NODE_COUNT || originNode < 1 ||
        originNode > NETWORK_NODE_COUNT || sourceNode == NODE_ID ||
        adjacencyMatrix[sourceNode - 1][NODE_ID - 1] == 0) return;

    if (packetType == PACKET_TYPE_ACK) {
        if (packetLen != ACK_PACKET_SIZE || priority != 0 || ttl != 0 ||
            !radioAwaitingAck || sourceNode != radioTxNextHop ||
            destinationNode != NODE_ID || originNode != radioTxOriginNode ||
            messageId != radioTxMessageId) return;
        completeDataAcknowledgment();
        return;
    }

    uint8_t expectedNextHop = 0;
    if (packetType > PACKET_TYPE_TELEMETRY || priority < 1 || priority > 3 ||
        ttl == 0 || packetLen <= FRAME_OVERHEAD_SIZE ||
        !dijkstraNextHop(adjacencyMatrix, sourceNode, destinationNode, expectedNextHop) ||
        expectedNextHop != NODE_ID) return;

    char plaintext[256];
    size_t plaintextLen = 0;
    const size_t encryptedLen = packetLen - FRAME_OVERHEAD_SIZE;
    if (!AESCrypto::decrypt(packet + FRAME_PREFIX_SIZE, encryptedLen,
                            plaintext, plaintextLen, sizeof(plaintext))) {
        if (packetType != PACKET_TYPE_HEARTBEAT) {
            Serial.printf("[LORA RX] Authentication/decryption failed for packet #%04u.\n", messageId);
        }
        return;
    }

    JsonDocument doc;
    if (deserializeJson(doc, plaintext, plaintextLen) ||
        (uint16_t)(doc["id"] | 0) != messageId ||
        (uint8_t)(doc["k"] | 0) != priority ||
        (uint8_t)(doc["src"] | 0) != originNode ||
        (uint8_t)(doc["dst"] | 0) != destinationNode) {
        if (packetType != PACKET_TYPE_HEARTBEAT) {
            Serial.printf("[LORA RX] Invalid inner message for packet #%04u.\n", messageId);
        }
        return;
    }

    recordLiveIncident(messageId, priority, packetType, originNode, sourceNode,
                       doc["ts"] | 0UL, doc["loc"] | "Unspecified",
                       doc["msg"] | "");

    if (destinationNode == NODE_ID) {
        if (packetType != PACKET_TYPE_HEARTBEAT) {
            Serial.printf("[LORA RX] Delivered packet #%04u at V%u: %s\n",
                          messageId, NODE_ID, (const char *)(doc["msg"] | ""));
        }
        startLinkAck(sourceNode, originNode, messageId);
        return;
    }

    if (ttl <= 1) {
        if (packetType != PACKET_TYPE_HEARTBEAT) {
            Serial.printf("[LORA RX] Packet #%04u reached TTL limit at V%u.\n", messageId, NODE_ID);
        }
        startLinkAck(sourceNode, originNode, messageId);
        return;
    }

    EmergencyMessage forwarded{};
    forwarded.id = messageId;
    forwarded.priority = priority;
    forwarded.timestamp_tx = doc["ts"] | (millis() / 1000);
    forwarded.originNode = originNode;
    forwarded.destinationNode = destinationNode;
    forwarded.ttl = ttl - 1;
    forwarded.packetType = packetType;
    forwarded.expiresAtMs = millis() + DTN_RETENTION_MS;
    forwarded.retryExponent = MAC_MIN_BACKOFF_EXPONENT;
    const char *location = doc["loc"] | "Unspecified";
    const char *message = doc["msg"] | "";
    strncpy(forwarded.location, location, sizeof(forwarded.location) - 1);
    strncpy(forwarded.payload, message, sizeof(forwarded.payload) - 1);
    forwarded.encryptedLen = (uint8_t)encryptedLen;
    memcpy(forwarded.encryptedData, packet + FRAME_PREFIX_SIZE, encryptedLen);

    if (!queuePush(forwarded)) {
        if (packetType != PACKET_TYPE_HEARTBEAT) {
            Serial.printf("[LORA RX] Forward queue full; packet #%04u was not acknowledged.\n", messageId);
        }
        return;
    }
    startLinkAck(sourceNode, originNode, messageId);
}

void serviceRadioRx() {
    if (!radioReady || !radioRxPending || radioAckTxInFlight || radioTxInFlight) return;
    radioRxPending = false;
    size_t packetLen = radio.getPacketLength();
    if (packetLen == 0 || packetLen > sizeof(radioPacket)) {
        radio.startReceive();
        return;
    }

    int16_t state = radio.readData(radioPacket, packetLen);
    if (state == RADIOLIB_ERR_NONE) {
        const float rssi = radio.getRSSI();
        const float snr = radio.getSNR();
        const float batteryVoltage = readBatteryVoltage();
        printRxTelemetryCsv(radioPacket, packetLen, rssi, snr, batteryVoltage);
        handleReceivedPacket(radioPacket, packetLen);
    } else {
        Serial.printf("[LORA RX] Read failed with code %d.\n", state);
    }
    if (!radioAckTxInFlight) radio.startReceive();
}

uint32_t nextDtnBackoff(uint8_t exponent, uint8_t &nextExponent) {
    if (exponent < MAC_MIN_BACKOFF_EXPONENT) exponent = MAC_MIN_BACKOFF_EXPONENT;
    if (exponent > MAC_MAX_BACKOFF_EXPONENT) exponent = MAC_MAX_BACKOFF_EXPONENT;
    const uint32_t slotCount = 1U << exponent;
    const uint32_t backoffMs = (esp_random() % slotCount) * MAC_SLOT_TIME_MS;
    nextExponent = exponent < MAC_MAX_BACKOFF_EXPONENT ? exponent + 1 : exponent;
    return backoffMs;
}

void deferDtnMessage(const EmergencyMessage &message, uint32_t now) {
    uint8_t nextExponent = message.retryExponent;
    const uint32_t delayMs = nextDtnBackoff(message.retryExponent, nextExponent);
    dtnBuffer.defer(message.id, message.originNode, now + delayMs, nextExponent);
}

void retainUnacknowledgedMessage(uint32_t now) {
    bool retryInQueue = false;
    if (radioTxFromDtn) {
        deferDtnMessage(activeTxMessage, now);
    } else if (dtnBuffer.store(activeTxMessage, now)) {
        queueRemoveById(activeTxMessage.id);
        deferDtnMessage(activeTxMessage, now);
        Serial.printf("[DTN] Stored packet #%04u after ACK timeout (%u/%u bytes).\n",
                      activeTxMessage.id, (unsigned int)dtnBuffer.usedBytes(),
                      (unsigned int)DtnBuffer::B_MAX_BYTES);
    } else {
        retryInQueue = true;
        Serial.println("[DTN] Buffer full; leaving the unacknowledged packet in the priority queue.");
    }
    radioAwaitingAck = false;
    resetMacBackoff();
    if (retryInQueue) nextMacAttemptAt = now + DTN_FULL_RETRY_MS;
}

void resetMacBackoff() {
    macBackoffActive = false;
    macBusyRetries = 0;
    macBackoffExponent = MAC_MIN_BACKOFF_EXPONENT;
    nextMacAttemptAt = 0;
}

void serviceRadioMac() {
    if (!radioReady) return;

    if (radioAckTxInFlight) {
        if (!radioTxDone) return;
        radioTxDone = false;
        int16_t finishState = radio.finishTransmit();
        radioAckTxInFlight = false;
        if (finishState != RADIOLIB_ERR_NONE) {
            Serial.printf("[LORA ACK] Completion error %d.\n", finishState);
        }
        radio.startReceive();
        return;
    }

    if (radioTxInFlight) {
        if (!radioTxDone) return;
        radioTxDone = false;
        int16_t finishState = radio.finishTransmit();
        radioTxInFlight = false;
        if (finishState == RADIOLIB_ERR_NONE) {
            radio.startReceive();
            radioAwaitingAck = true;
            const uint32_t ackAirTimeMs = (uint32_t)(radio.getTimeOnAir(ACK_PACKET_SIZE) / 1000);
            radioAckDeadlineMs = millis() + ackAirTimeMs + ACK_TIMEOUT_GUARD_MS;
            Serial.printf("[LORA TX] Packet #%04u sent (%u bytes); waiting for next-hop ACK.\n",
                          radioTxMessageId, (unsigned int)radioTxPacketLen);
        } else {
            Serial.printf("[LORA TX] Completion error %d for packet #%04u; retaining it in DTN.\n",
                          finishState, radioTxMessageId);
            radio.startReceive();
            radioAwaitingAck = true;
            radioAckDeadlineMs = millis();
        }
        return;
    }

    if (radioAwaitingAck) {
        if (deadlineReached(millis(), radioAckDeadlineMs)) retainUnacknowledgedMessage(millis());
        else return;
    }

    if ((int32_t)(millis() - nextMacAttemptAt) < 0) return;

    EmergencyMessage queuedMessage{};
    EmergencyMessage dtnMessage{};
    const bool haveQueuedMessage = queuePeek(queuedMessage);
    const bool haveDtnMessage = dtnBuffer.peekDue(millis(), dtnMessage);
    const bool fromDtn = haveDtnMessage && (!haveQueuedMessage ||
        dtnMessage.priority < queuedMessage.priority ||
        (dtnMessage.priority == queuedMessage.priority &&
         dtnMessage.timestamp_tx <= queuedMessage.timestamp_tx));
    const bool haveMessage = haveQueuedMessage || haveDtnMessage;
    if (!haveMessage) {
        resetMacBackoff();
        return;
    }
    EmergencyMessage msg = fromDtn ? dtnMessage : queuedMessage;
    if (msg.destinationNode == NODE_ID) {
        if (fromDtn) dtnBuffer.remove(msg.id, msg.originNode);
        else queueRemoveById(msg.id);
        resetMacBackoff();
        return;
    }
    if (deadlineReached(millis(), msg.expiresAtMs)) {
        if (fromDtn) dtnBuffer.remove(msg.id, msg.originNode);
        else queueRemoveById(msg.id);
        Serial.printf("[DTN] Expired packet #%04u before transmission.\n", msg.id);
        resetMacBackoff();
        return;
    }

    uint8_t nextHopNode = 0;
    if (!dijkstraNextHop(adjacencyMatrix, NODE_ID, msg.destinationNode, nextHopNode) ||
        nextHopNode == NODE_ID) {
        const uint32_t now = millis();
        if (fromDtn) {
            deferDtnMessage(msg, now);
        } else if (dtnBuffer.store(msg, now)) {
            queueRemoveById(msg.id);
            deferDtnMessage(msg, now);
        } else {
            nextMacAttemptAt = now + DTN_FULL_RETRY_MS;
        }
        Serial.printf("[ROUTE] No path from V%u to V%u for packet #%04u.\n",
                      NODE_ID, msg.destinationNode, msg.id);
        return;
    }
    if (!macBackoffActive || macBackoffMessageId != msg.id) {
        macBackoffActive = true;
        macBackoffMessageId = msg.id;
        macBusyRetries = 0;
        macBackoffExponent = MAC_MIN_BACKOFF_EXPONENT;
        nextMacAttemptAt = 0;
    }

    int16_t cadState = radio.scanChannel();
    if (cadState == RADIOLIB_CHANNEL_FREE) {
        size_t packetLen = 0;
        if (!serializeLoRaPacket(msg, nextHopNode, radioPacket, sizeof(radioPacket), packetLen)) {
            Serial.printf("[LORA TX] Packet #%04u is invalid or exceeds the %u-byte MTU; dropping it.\n",
                          msg.id, (unsigned int)MAX_LORA_PACKET_SIZE);
            if (fromDtn) dtnBuffer.remove(msg.id, msg.originNode);
            else queueRemoveById(msg.id);
            resetMacBackoff();
            radio.startReceive();
            return;
        }

        radioTxDone = false;
        radioTxMessageId = msg.id;
        radioTxOriginNode = msg.originNode;
        radioTxNextHop = nextHopNode;
        activeTxMessage = msg;
        radioTxFromDtn = fromDtn;
        radioTxPacketLen = packetLen;
        int16_t txState = radio.startTransmit(radioPacket, packetLen);
        if (txState == RADIOLIB_ERR_NONE) {
            radioTxInFlight = true;
            Serial.printf("[LORA TX] Started packet #%04u, %u bytes, header 0x%02X.\n",
                          msg.id, (unsigned int)packetLen, radioPacket[0]);
        } else {
            Serial.printf("[LORA TX] Start error %d for packet #%04u; retrying later.\n", txState, msg.id);
            radio.startReceive();
            resetMacBackoff();
            if (fromDtn) deferDtnMessage(msg, millis());
            else nextMacAttemptAt = millis() + MAC_DEFER_TIME_MS;
        }
        return;
    }

    if (cadState != RADIOLIB_PREAMBLE_DETECTED) {
        Serial.printf("[LORA CAD] Scan error %d; retaining queued packet #%04u.\n", cadState, msg.id);
        radio.startReceive();
        resetMacBackoff();
        if (fromDtn) deferDtnMessage(msg, millis());
        else nextMacAttemptAt = millis() + MAC_DEFER_TIME_MS;
        return;
    }

    macBusyRetries++;
    if (macBusyRetries >= MAC_MAX_CAD_RETRIES) {
        Serial.printf("[LORA CAD] Channel remained busy after %u scans; deferring packet #%04u.\n",
                      MAC_MAX_CAD_RETRIES, msg.id);
        radio.startReceive();
        resetMacBackoff();
        if (fromDtn) deferDtnMessage(msg, millis());
        else nextMacAttemptAt = millis() + MAC_DEFER_TIME_MS;
        return;
    }

    uint32_t slotCount = 1U << macBackoffExponent;
    uint32_t slots = esp_random() % slotCount;
    uint32_t backoffMs = slots * MAC_SLOT_TIME_MS;
    if (macBackoffExponent < MAC_MAX_BACKOFF_EXPONENT) macBackoffExponent++;
    nextMacAttemptAt = millis() + backoffMs;
    radio.startReceive();
    if (fromDtn) {
        uint8_t nextExponent = macBackoffExponent;
        dtnBuffer.defer(msg.id, msg.originNode, nextMacAttemptAt, nextExponent);
    }
    Serial.printf("[LORA CAD] Busy; TBEB retry %u/%u in %lu ms.\n",
                  macBusyRetries, MAC_MAX_CAD_RETRIES, (unsigned long)backoffMs);
}

void setupWebServerRoutes() {
    // 1. Captive Portal UI (Root)
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
        request->send_P(200, "text/html", CAPTIVE_PORTAL_HTML);
    });

    // 2. Admin / Main Hub Dashboard (Stationary Hub V1 at Barangay Hall)
    server.on("/admin", HTTP_GET, [](AsyncWebServerRequest *request) {
        request->send_P(200, "text/html", ADMIN_DASHBOARD_HTML);
    });

    server.on("/api/live_incidents", HTTP_GET, [](AsyncWebServerRequest *request) {
        if (!liveIncidentMutex ||
            xSemaphoreTake(liveIncidentMutex, pdMS_TO_TICKS(100)) != pdTRUE) {
            request->send(503, "application/json", "{\"error\":\"Incident buffer busy\"}");
            return;
        }

        JsonDocument document;
        JsonArray incidents = document.to<JsonArray>();
        const size_t oldestIndex = (liveIncidentWriteIndex + LIVE_INCIDENT_CAPACITY -
                                    liveIncidentCount) % LIVE_INCIDENT_CAPACITY;
        for (size_t i = 0; i < liveIncidentCount; i++) {
            const LiveIncident &incident = liveIncidents[(oldestIndex + i) % LIVE_INCIDENT_CAPACITY];
            JsonObject row = incidents.add<JsonObject>();
            row["id"] = incident.messageId;
            row["priority"] = incident.priority;
            row["packetType"] = incident.packetType;
            row["originNode"] = incident.originNode;
            char originLabel[5];
            snprintf(originLabel, sizeof(originLabel), "V%u", incident.originNode);
            row["origin"] = originLabel;
            row["route"] = incident.path;
            if (incident.latencyMs >= 0) row["latencyMs"] = incident.latencyMs;
            else row["latencyMs"] = nullptr;
            row["location"] = incident.location;
            row["message"] = incident.message;
            row["crypto"] = "AES-128-CBC + HMAC-SHA-256";
            row["rxTime"] = incident.receivedAtMs;
        }
        xSemaphoreGive(liveIncidentMutex);

        AsyncResponseStream *response = request->beginResponseStream("application/json");
        serializeJson(document, *response);
        request->send(response);
    });

    // Android, Windows, and Chrome captive portal probes
    server.on("/generate_204", HTTP_GET, [](AsyncWebServerRequest *request) { request->redirect("/"); });
    server.on("/gen_204", HTTP_GET, [](AsyncWebServerRequest *request) { request->redirect("/"); });
    server.on("/ncsi.txt", HTTP_GET, [](AsyncWebServerRequest *request) { request->redirect("/"); });

    // Apple iOS/macOS Captive Network Assistant (CNA) probe
    server.on("/hotspot-detect.html", HTTP_GET, [](AsyncWebServerRequest *request) { request->redirect("/"); });

    // 3. Emergency Submission Endpoint (Intake & Security Pipeline)
    server.on("/api/submit", HTTP_POST, [](AsyncWebServerRequest *request) {}, NULL,
        [](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total) {
            JsonDocument doc;
            DeserializationError err = deserializeJson(doc, data, len);

            if (err) {
                request->send(400, "application/json", "{\"status\":\"error\",\"message\":\"Malformed JSON payload\"}");
                return;
            }

            // Step A: Community Access Credential Verification (Section 4.3 Anti-Spoofing)
            const char *credential = doc["credential"] | "";
            if (!AESCrypto::verifyCommunityCredential(credential)) {
                Serial.println("[SECURITY ALERT] Rejected submission: Invalid community credential!");
                request->send(403, "application/json", "{\"status\":\"error\",\"message\":\"Invalid Community Passcode. Access Denied.\"}");
                return;
            }
            if (!radioReady) {
                request->send(503, "application/json", "{\"status\":\"error\",\"message\":\"LoRa radio is unavailable. Message was not queued.\"}");
                return;
            }

            // Step B: Extract Message Data
            int priorityVal = doc["priority"] | 1;
            uint8_t priority = (priorityVal >= 1 && priorityVal <= 3) ? (uint8_t)priorityVal : 1;
            const char *location = doc["location"] | "Unspecified";
            const char *message = doc["message"] | "";

            EmergencyMessage msg{};
            msg.id = allocateMessageId();
            msg.priority = priority;
            msg.timestamp_tx = (uint32_t)(doc["timestamp"] | (millis() / 1000));
            msg.originNode = NODE_ID;
            msg.destinationNode = HUB_NODE_ID;
            msg.ttl = INITIAL_TTL;
            msg.packetType = priority == 1 ? PACKET_TYPE_SOS : PACKET_TYPE_TELEMETRY;
            msg.expiresAtMs = millis() + DTN_RETENTION_MS;
            msg.retryExponent = MAC_MIN_BACKOFF_EXPONENT;
            strncpy(msg.location, location, sizeof(msg.location) - 1);
            msg.location[sizeof(msg.location) - 1] = '\0';
            strncpy(msg.payload, message, sizeof(msg.payload) - 1);
            msg.payload[sizeof(msg.payload) - 1] = '\0';

            // Step C: AES-128 CBC Encryption (Section 3.7 & 4.3)
            char plainToEncrypt[256];
            JsonDocument payloadDoc;
            payloadDoc["id"] = msg.id;
            payloadDoc["k"] = msg.priority;
            payloadDoc["src"] = msg.originNode;
            payloadDoc["dst"] = msg.destinationNode;
            payloadDoc["ts"] = msg.timestamp_tx;
            payloadDoc["loc"] = msg.location;
            payloadDoc["msg"] = msg.payload;
            size_t plainLen = serializeJson(payloadDoc, plainToEncrypt, sizeof(plainToEncrypt));

            size_t encLen = 0;
            bool encryptSuccess = plainLen > 0 && AESCrypto::encrypt(plainToEncrypt, plainLen,
                                                    msg.encryptedData, encLen,
                                                    MAX_LORA_PACKET_SIZE - FRAME_OVERHEAD_SIZE);
            if (!encryptSuccess) {
                Serial.println("[ERROR] Message encryption failed; submission rejected.");
                request->send(500, "application/json", "{\"status\":\"error\",\"message\":\"Message could not be encrypted. Please try again.\"}");
                return;
            }
            msg.encryptedLen = (uint8_t)encLen;

            // Step D: Insert into Dual-Key Binary Min-Heap Priority Queue (Section 3.2)
            bool queueSuccess = queuePush(msg);
            if (!queueSuccess) {
                Serial.println("[ERROR] Priority queue is full; submission rejected.");
                request->send(503, "application/json", "{\"status\":\"error\",\"message\":\"The message queue is full. Please try again shortly.\"}");
                return;
            }

            // Step E: Serial Telemetry Output
            Serial.println("\n=======================================================");
            Serial.println("  [+] EMERGENCY MESSAGE ACCEPTED & QUEUED");
            Serial.println("=======================================================");
            Serial.printf("  Ref ID        : #%04d\n", msg.id);
            Serial.printf("  Priority      : k=%u (%s)\n", msg.priority,
                          msg.priority == 1 ? "MEDICAL SOS (Highest)" : (msg.priority == 2 ? "GENERAL EMERGENCY" : "ROUTINE/INFO"));
            Serial.printf("  Location      : %s\n", msg.location);
            Serial.printf("  Message Text  : %s\n", msg.payload);
            Serial.printf("  Security      : %s (Encrypted Payload: %u bytes)\n",
                          "AES-128-CBC + HMAC-SHA-256 OK", msg.encryptedLen);
            Serial.printf("  Min-Heap State: %s (Current Queue Size: %u)\n",
                          "Inserted at O(log n)", (unsigned int)queueSize());
            Serial.printf("  Connected Stns: %u / %u max\n", WiFi.softAPgetStationNum(), MAX_AP_CLIENTS);
            Serial.println("=======================================================\n");

            // Step F: Immediate JSON Response with Connect-Queue-Disconnect Header
            char responseJson[96];
            snprintf(responseJson, sizeof(responseJson), "{\"status\":\"queued\",\"ref\":\"#%04d\",\"priority\":%u,\"queueSize\":%u}",
                     msg.id, msg.priority, (unsigned int)queueSize());

            AsyncWebServerResponse *response = request->beginResponse(200, "application/json", responseJson);
            response->addHeader("Connection", "close"); // Instruct client to close connection to free socket
            request->send(response);
        }
    );

    // Fallback: Redirect any other URL to Captive Portal
    server.onNotFound([](AsyncWebServerRequest *request) {
        request->redirect("/");
    });
}

void setup() {
    Serial.begin(115200);
    delay(1500);
    nextHeartbeatAtMs = millis() + HEARTBEAT_INTERVAL_MS;

    priorityQueueMutex = xSemaphoreCreateMutex();
    if (!priorityQueueMutex) {
        Serial.println("[ERROR] Could not create priority queue mutex.");
    }
    liveIncidentMutex = xSemaphoreCreateMutex();
    if (!liveIncidentMutex) {
        Serial.println("[ERROR] Could not create live incident buffer mutex.");
    }

    SPI.begin(LORA_SCK_PIN, LORA_MISO_PIN, LORA_MOSI_PIN, LORA_NSS_PIN);
    int16_t radioState = radio.begin(LORA_FREQUENCY_MHZ, 125.0, 12, 5,
                                     RADIOLIB_SX126X_SYNC_WORD_PRIVATE, 10, 8, 1.8, false);
    if (radioState == RADIOLIB_ERR_NONE) {
        radioState = radio.setDio2AsRfSwitch(true);
    }
    if (radioState == RADIOLIB_ERR_NONE) {
        radio.setPacketSentAction(onRadioPacketSent);
        radio.setPacketReceivedAction(onRadioPacketReceived);
        radioState = radio.startReceive();
        if (radioState == RADIOLIB_ERR_NONE) {
            radioReady = true;
            Serial.println("[LoRa] SX1262 ready: 915 MHz, SF12, BW125, CR4/5, asynchronous RX.");
        }
    } else {
        Serial.printf("[LoRa] SX1262 initialization failed with code %d.\n", radioState);
    }

    Serial.println("\n-------------------------------------------------------");
    Serial.println("  Barangay San Miguel Offline LoRa Mesh Architecture");
    Serial.println("  Interfaces & Security Subsystem Initializing...");
    Serial.println("-------------------------------------------------------");

    // Configure Wi-Fi SoftAP with 25-client cap
    WiFi.mode(WIFI_AP);
    WiFi.softAPConfig(apIP, apIP, netMsk);
    WiFi.softAP(AP_SSID, NULL, 1, 0, MAX_AP_CLIENTS);

    Serial.printf("[WiFi SoftAP] SSID: '%s'\n", AP_SSID);
    Serial.printf("[WiFi SoftAP] Gateway IP: %s\n", apIP.toString().c_str());
    Serial.printf("[WiFi SoftAP] Client Connection Cap: %u stations\n", MAX_AP_CLIENTS);

    // Initialize Captive DNS Server
    dnsServer.setErrorReplyCode(DNSReplyCode::NoError);
    dnsServer.start(DNS_PORT, "*", apIP);
    Serial.println("[DNS Server]  Captive DNS running on Port 53");

    // Initialize Web Server (Captive Portal + Admin Dashboard)
    setupWebServerRoutes();
    server.begin();
    Serial.println("[Web Server]  HTTP Server active on Port 80");
    Serial.println("[Web Server]  - Captive Portal: http://192.168.4.1/");
    Serial.println("[Web Server]  - Admin Dashboard: http://192.168.4.1/admin");
    Serial.println("-------------------------------------------------------");
    Serial.println("[STATUS] Ready for Emergency Message Intake & Security Processing.");
}

void loop() {
    // Process DNS captive portal requests
    dnsServer.processNextRequest();

    serviceHeartbeat();
    serviceRadioRx();
    serviceRadioMac();
    const size_t expiredDtn = dtnBuffer.purgeExpired(millis());
    if (expiredDtn > 0) Serial.printf("[DTN] Purged %u expired packet(s).\n", (unsigned int)expiredDtn);
}
