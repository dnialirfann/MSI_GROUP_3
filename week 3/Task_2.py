import serial, time
from collections import deque
import matplotlib.pyplot as plt

ser = serial.Serial('COM3', 9600, timeout=1)   # change COMx
time.sleep(2)                                    # Arduino resets on open
ser.reset_input_buffer()

pots = deque(maxlen=200)
angles = deque(maxlen=200)

def on_key(event):
    if event.key == 'q':
        ser.write(b'q')
        print("Stop sent to Arduino")
    elif event.key == 'r':
        ser.write(b'r')
        print("Resume sent to Arduino")

plt.ion()
fig, ax = plt.subplots()
fig.canvas.mpl_connect('key_press_event', on_key)

try:
    while plt.fignum_exists(fig.number):
        while ser.in_waiting:
            line = ser.readline().decode(errors='ignore').strip()
            try:
                pot, angle = map(int, line.split(','))
            except ValueError:
                continue                          # skip partial/bad lines
            pots.append(pot)
            angles.append(angle)
            print(f"Pot: {pot}  Servo angle: {angle} deg")

        ax.clear()
        ax.plot(pots, label="Pot value (0-1023)")
        ax.plot(angles, label="Servo angle (deg)")
        ax.set_xlabel("Sample")
        ax.legend(loc="upper left")
        plt.pause(0.05)
except KeyboardInterrupt:
    pass
finally:
    ser.write(b'q')
    ser.close()
    plt.ioff()
    plt.show()
    print("Serial connection closed.")