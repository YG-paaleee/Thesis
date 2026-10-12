#ifndef MIN_HEAP_H
#define MIN_HEAP_H

#include <Arduino.h>

// Message Structure matching Thesis Section 4.4.3
struct EmergencyMessage {
    uint16_t id;             // 2-byte Message ID
    uint8_t  priority;       // k=1 (Medical SOS), k=2 (General Emergency), k=3 (Routine/Info)
    uint32_t timestamp_tx;   // Unix transmission timestamp (seconds or ms)
    uint8_t  originNode;     // Node ID (1=V1 Main Hub, 2..5=V2..V5 Mini Hubs, 6=V6 Edge Node)
    uint8_t  destinationNode;
    uint8_t  ttl;
    uint8_t  packetType;
    uint32_t expiresAtMs;
    uint32_t nextRetryAtMs;
    uint8_t  retryExponent;
    char     location[84];   // Landmark/location string
    char     payload[201];   // Emergency message text (<=200 UTF-8 bytes)
    uint8_t  encryptedLen;   // Length of authenticated encrypted packet (IV + ciphertext + HMAC)
    uint8_t  encryptedData[256];
};

// Dual-Key Binary Min-Heap Priority Queue (Section 3.2)
// Memory-deterministic static array allocated in SRAM
class PriorityMinHeap {
private:
    static const size_t MAX_CAPACITY = 32; // Deterministic static capacity for ESP32 SRAM
    EmergencyMessage heap[MAX_CAPACITY];
    size_t currentSize;

    inline int parent(int i) const { return (i - 1) / 2; }
    inline int leftChild(int i) const { return 2 * i + 1; }
    inline int rightChild(int i) const { return 2 * i + 2; }

    // Dual-Key Comparison: Primary = Priority (k), Secondary = Timestamp (t_tx)
    // Returns true if msgA has strictly higher priority (should be closer to root) than msgB
    bool isHigherPriority(const EmergencyMessage &a, const EmergencyMessage &b) const {
        if (a.priority < b.priority) return true;
        if (a.priority == b.priority) {
            return a.timestamp_tx <= b.timestamp_tx;
        }
        return false;
    }

    void swapNodes(int i, int j) {
        EmergencyMessage temp = heap[i];
        heap[i] = heap[j];
        heap[j] = temp;
    }

    void heapifyUp(int index) {
        while (index > 0 && isHigherPriority(heap[index], heap[parent(index)])) {
            swapNodes(index, parent(index));
            index = parent(index);
        }
    }

    void heapifyDown(int index) {
        int smallest = index;
        int left = leftChild(index);
        int right = rightChild(index);

        if (left < (int)currentSize && isHigherPriority(heap[left], heap[smallest])) {
            smallest = left;
        }
        if (right < (int)currentSize && isHigherPriority(heap[right], heap[smallest])) {
            smallest = right;
        }

        if (smallest != index) {
            swapNodes(index, smallest);
            heapifyDown(smallest);
        }
    }

public:
    PriorityMinHeap() : currentSize(0) {}

    size_t size() const { return currentSize; }
    bool isEmpty() const { return currentSize == 0; }
    bool isFull() const { return currentSize >= MAX_CAPACITY; }

    // Insertion: O(log n)
    bool push(const EmergencyMessage &msg) {
        if (isFull()) {
            // Eviction policy (Section 3.3 / 4.4.3): If full, find and drop lowest priority (k=3)
            int lowestIndex = -1;
            uint8_t lowestPriority = 0;
            for (size_t i = 0; i < currentSize; i++) {
                if (heap[i].priority >= lowestPriority) {
                    lowestPriority = heap[i].priority;
                    lowestIndex = i;
                }
            }
            if (lowestIndex != -1 && lowestPriority > msg.priority) {
                // Replace lowest priority with incoming higher priority message
                heap[lowestIndex] = msg;
                heapifyUp(lowestIndex);
                heapifyDown(lowestIndex);
                return true;
            }
            return false; // Queue saturated with equal/higher priority traffic
        }

        heap[currentSize] = msg;
        heapifyUp(currentSize);
        currentSize++;
        return true;
    }

    // Extraction: O(log n) - Root index 0 always contains the highest priority element
    bool pop(EmergencyMessage &outMsg) {
        if (isEmpty()) return false;

        outMsg = heap[0];
        heap[0] = heap[currentSize - 1];
        currentSize--;

        if (currentSize > 0) {
            heapifyDown(0);
        }
        return true;
    }

    bool removeById(uint16_t id) {
        for (size_t i = 0; i < currentSize; i++) {
            if (heap[i].id != id) continue;

            currentSize--;
            if (i < currentSize) {
                heap[i] = heap[currentSize];
                if (i > 0 && isHigherPriority(heap[i], heap[parent((int)i)])) {
                    heapifyUp((int)i);
                } else {
                    heapifyDown((int)i);
                }
            }
            return true;
        }
        return false;
    }

    // Peek root without removing
    bool peek(EmergencyMessage &outMsg) const {
        if (isEmpty()) return false;
        outMsg = heap[0];
        return true;
    }

    void clear() {
        currentSize = 0;
    }
};

#endif
