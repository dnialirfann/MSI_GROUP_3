import serial

# Replace 'COMx' with your Arduino's port (e.g. 'COM3')
ser = serial.Serial('COM3', 9600)

try:
    while True:
        line = ser.readline().decode().strip()
        if line.isdigit():                  # ignore blank or broken lines
            pot_value = int(line)
            if pot_value >= 512:            # half or more
                print("Potentiometer Value:", pot_value, "-> LED ON")
            else:
                print("Potentiometer Value:", pot_value, "-> LED OFF")
except KeyboardInterrupt:
    ser.close()
    print("Serial connection closed.")