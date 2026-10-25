"""
RFID access control with circular-motion check.

Flow: tap card -> prompt "do a circular motion" -> record accelerometer X-Y
      -> circle detected? unlock : stay locked

Arduino receives:  'A' -> unlock (servo 180, green LED)
                   'D' -> lock   (servo 90, red LED)
Arduino sends:     ax,ay,az,gx,gy,gz  (one line per reading, first two used)

By default ONE Arduino on PORT does both jobs (sends accelerometer data and
accepts A/D). If the accelerometer is on a different board, set ACCEL_PORT.

Install:  pip install pyserial matplotlib numpy
"""

import time
import numpy as np
import serial
from serial.tools import list_ports
import matplotlib.pyplot as plt

# ---------- Settings ----------
PORT = "COM3"          # Arduino with servo/LEDs (Arduino IDE > Tools > Port)
ACCEL_PORT = None      # None = accelerometer data comes from the same Arduino as PORT
BAUD = 9600
UNLOCK_SECONDS = 5     # how long the door stays unlocked before re-locking

ALLOWED = {
    "0013069760",      # keep as strings so leading zeros are preserved
}

COUNTDOWN = 3          # seconds before recording starts
RECORD_SECONDS = 3.0   # time allowed to draw the circle
MAX_ATTEMPTS = 3       # circle attempts per card tap

SMOOTH = 5
MIN_ANGLE_DEG = 300    # must sweep at least this much to count as a circle
MAX_RADIUS_VARIATION = 0.45   # lower = stricter
MIN_RADIUS = 200      # minimum motion size (tune for your sensor's units)
# ------------------------------


def open_port(port):
    try:
        return serial.Serial(port, BAUD, timeout=1)
    except serial.SerialException as e:
        print(f"Could not open {port}: {e}")
        print("Available ports:")
        for p in list_ports.comports():
            print(f"  {p.device} - {p.description}")
        print("Close the Arduino Serial Monitor and check the port settings.")
        raise SystemExit(1)


def read_xy(ser):
    """Return (x, y) from one line, or None if the line isn't sensor data."""
    try:
        parts = ser.readline().decode(errors="ignore").strip().split(",")
        if len(parts) < 2:
            return None
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None


def moving_average(a, n):
    if len(a) < n:
        return a
    return np.convolve(a, np.ones(n) / n, mode="valid")


def detect_circle(xs, ys):
    x = moving_average(np.array(xs), SMOOTH)
    y = moving_average(np.array(ys), SMOOTH)
    if len(x) < 20:
        return False, "Not enough data"

    x = x - x.mean()   # remove gravity/offset
    y = y - y.mean()
    radius = np.hypot(x, y)
    mean_r = radius.mean()
    if mean_r < MIN_RADIUS:
        return False, f"Motion too small (radius {mean_r:.0f} < {MIN_RADIUS})"

    angle = np.unwrap(np.arctan2(y, x))
    swept = np.degrees(abs(angle[-1] - angle[0]))
    variation = radius.std() / mean_r
    direction = "counter-clockwise" if angle[-1] > angle[0] else "clockwise"

    info = f"swept {swept:.0f} deg, radius variation {variation:.2f}, {direction}"
    return (swept >= MIN_ANGLE_DEG and variation <= MAX_RADIUS_VARIATION), info


def gesture_check(accel, fig, ax, line):
    """Prompt the user, record, plot live; return True if a circle was made."""
    print("\nGet ready to move the sensor in a circle...")
    for n in range(COUNTDOWN, 0, -1):
        ax.set_title(f"Get ready... {n}")
        fig.canvas.draw_idle()
        plt.pause(1)

    accel.reset_input_buffer()
    ax.set_title("DO A CIRCULAR MOTION NOW!")
    print(">>> Do a circular motion now! <<<")
    fig.canvas.draw_idle()
    plt.pause(0.01)

    xs, ys = [], []
    start = time.time()
    while time.time() - start < RECORD_SECONDS:
        point = read_xy(accel)
        if point is None:
            continue
        xs.append(point[0])
        ys.append(point[1])
        if len(xs) % 3 == 0:
            line.set_data(xs, ys)
            ax.relim()
            ax.autoscale_view()
            plt.pause(0.001)

    line.set_data(xs, ys)
    ax.relim()
    ax.autoscale_view()

    ok, info = detect_circle(xs, ys)
    result = "Circle detected!" if ok else "No circle detected"
    print(f"{result} ({info})")
    ax.set_title(f"{result}\n{info}")
    fig.canvas.draw_idle()
    plt.pause(1)
    return ok


def main():
    arduino = open_port(PORT)
    accel = arduino if ACCEL_PORT in (None, PORT) else open_port(ACCEL_PORT)
    time.sleep(2)  # Arduino resets when the port opens; wait for it to boot

    arduino.write(b"D")  # start locked

    plt.ion()
    fig, ax = plt.subplots()
    line, = ax.plot([], [], "b-")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_aspect("equal", adjustable="datalim")

    print(f"Connected on {PORT}. Click this window, then tap a card. Ctrl+C to quit.")

    try:
        while True:
            uid = input("Tap card: ").strip()
            if not uid:
                continue

            if uid not in ALLOWED:
                print(f"[{uid}] Access denied")
                arduino.write(b"D")
                continue

            print(f"[{uid}] Card accepted. Now verify with a circular motion.")

            granted = False
            for attempt in range(1, MAX_ATTEMPTS + 1):
                print(f"Attempt {attempt} of {MAX_ATTEMPTS}")
                if gesture_check(accel, fig, ax, line):
                    granted = True
                    break

            if granted:
                print("Access granted")
                arduino.write(b"A")
                if UNLOCK_SECONDS > 0:
                    time.sleep(UNLOCK_SECONDS)
                    arduino.write(b"D")
                    print("Locked again")
            else:
                print("Gesture failed. Access denied")
                arduino.write(b"D")
    except KeyboardInterrupt:
        print("\nExiting, locking...")
        arduino.write(b"D")
    finally:
        arduino.close()
        if accel is not arduino:
            accel.close()


if __name__ == "__main__":
    main()
