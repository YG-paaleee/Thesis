import serial

# Configuration
PORT = "COM4"  # Change this to match your Node V1 COM port
BAUD = 115200
OUTPUT_FILE = "empirical_telemetry_dataset.csv"
TARGET_VECTORS = 300  # Minimum required feature vectors

print(f"Connecting to Node V1 on {PORT} at {BAUD} baud...")

try:
  ser = serial.Serial(PORT, BAUD, timeout=1)
except Exception as e:
  print(f"Error opening serial port: {e}")
  exit(1)

vector_count = 0
header_written = False

print(
    f"Listening for telemetry stream. Target: {TARGET_VECTORS} valid data"
    " rows..."
)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
  while vector_count < TARGET_VECTORS:
    line = ser.readline().decode("utf-8", errors="ignore").strip()
    if line:
      # Print to console for real-time monitoring
      print(line)

      # Write incoming line to CSV
      f.write(line + "\n")
      f.flush()

      # Increment counter only for valid data rows (ignoring header or debug logs)
      if (
          "Timestamp" not in line and "," in line
      ):  # Assumes firmware outputs comma-separated fields
        vector_count += 1
        print(
            f"Progress: [{vector_count}/{TARGET_VECTORS}] vectors captured.",
            end="\r",
        )

ser.close()
print(
    f"\n[SUCCESS] Target reached! Captured {vector_count} feature vectors into"
    f" '{OUTPUT_FILE}'."
)