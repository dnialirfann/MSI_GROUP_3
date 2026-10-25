import time
from collections import deque

import numpy as np
import serial
import matplotlib.pyplot as plt

# =====================================================================
# IMPROVEMENT 1: Serial configuration and bounded buffer
# deque(maxlen=35) keeps only the 35 most recent samples, which stops
# the plot from slowing down and becoming cluttered over time.
# =====================================================================
SERIAL_PORT = 'COM3' # macOS port; change to match your system
BAUD_RATE = 9600                       # must match Serial.begin() in the sketch
MAX_POINTS = 35

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)                          # the Uno resets when the port opens
ser.reset_input_buffer()

x_vals = deque(maxlen=MAX_POINTS)
y_vals = deque(maxlen=MAX_POINTS)

# =====================================================================
# IMPROVEMENT 2: Path visualisation
# The marker style is changed from 'ro' to 'ro-' so that consecutive
# samples are joined by a line and the motion path is clearly visible.
# Axis labels, a grid, a legend and a status box are also added.
# =====================================================================
plt.ion()
fig, ax = plt.subplots(figsize=(7, 7))
ax.set_xlim(-20000, 20000)
ax.set_ylim(-20000, 20000)
ax.set_title("Task 1: Real-Time MPU6050 Motion Tracking")
ax.set_xlabel("Acceleration X (raw LSB)")
ax.set_ylabel("Acceleration Y (raw LSB)")
ax.grid(True, linestyle='--', alpha=0.6)

line, = ax.plot([], [], 'ro-', linewidth=2, markersize=5, label='Hand path')
center_dot, = ax.plot([], [], 'bx', markersize=10, label='Circle centre')
status_box = ax.text(-18500, 17500, "Status: Collecting data...",
                     fontsize=11, fontweight='bold',
                     bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
ax.legend(loc='lower right')


# =====================================================================
# IMPROVEMENT 3: Circular gesture detection
# A window is classified as circular only if all four criteria hold:
# 1. Amplitude: X and Y spans both exceed 6000 LSB (rejects jitter).
# 2. Quadrant coverage: the path visits all four quadrants around
#    its centroid.
# 3. Radius consistency: std/mean of the distance from the centroid
#    is below 0.45 (rejects non-round shapes).
# 4. Rotation consistency: at least 70% of consecutive turns (2D cross
#    product sign) go in one direction (rejects random scatter).
# All thresholds are untested defaults and must be tuned on real data.
# =====================================================================
def check_circular_gesture(x_arr, y_arr):
    if len(x_arr) < 16:
        return False, 0, 0

    x = np.array(x_arr, dtype=float)
    y = np.array(y_arr, dtype=float)

    # Centroid of the movement
    cx, cy = np.mean(x), np.mean(y)

    # 1. Amplitude check
    span_x = np.max(x) - np.min(x)
    span_y = np.max(y) - np.min(y)
    if span_x < 6000 or span_y < 6000:
        return False, cx, cy

    # 2. Quadrant coverage
    dx = x - cx
    dy = y - cy
    q1 = np.any((dx > 0) & (dy > 0))
    q2 = np.any((dx < 0) & (dy > 0))
    q3 = np.any((dx < 0) & (dy < 0))
    q4 = np.any((dx > 0) & (dy < 0))
    if not (q1 and q2 and q3 and q4):
        return False, cx, cy

    # 3. Radius consistency
    radii = np.sqrt(dx ** 2 + dy ** 2)
    if (np.std(radii) / np.mean(radii)) >= 0.45:
        return False, cx, cy

    # 4. Rotation consistency
    cross = dx[:-1] * dy[1:] - dy[:-1] * dx[1:]
    ccw = np.sum(cross > 0)
    cw = np.sum(cross < 0)
    if max(ccw, cw) / max(ccw + cw, 1) < 0.7:
        return False, cx, cy

    return True, cx, cy


print("Tracking started. Move the sensor in a circle. Press Ctrl+C to exit.")

try:
    while plt.fignum_exists(fig.number):
        try:
            raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not raw_line:
                continue
            values = raw_line.split(',')

            # =============================================================
            # IMPROVEMENT 4: Corrected serial field check
            # The Arduino sketch sends 3 values (ax, ay, az), not 6 as the
            # starter code assumed (len(values) == 6), so every line was
            # being discarded and nothing was plotted.
            # =============================================================
            if len(values) < 3:
                continue

            x_vals.append(int(values[0]))
            y_vals.append(int(values[1]))

            # =============================================================
            # IMPROVEMENT 5: 3-point moving-average filter
            # Smooths the MPU6050 readings so the plotted line is less
            # jagged. The smoothed data is used for both plotting and
            # gesture detection, so the two stay consistent. Note that
            # mode='valid' returns two fewer points than the buffer.
            # =============================================================
            if len(x_vals) >= 3:
                kernel = np.ones(3) / 3
                smooth_x = np.convolve(np.array(x_vals), kernel, mode='valid')
                smooth_y = np.convolve(np.array(y_vals), kernel, mode='valid')
            else:
                smooth_x, smooth_y = np.array(x_vals), np.array(y_vals)

            line.set_data(smooth_x, smooth_y)

            detected, cx, cy = check_circular_gesture(smooth_x, smooth_y)
            if detected:
                center_dot.set_data([cx], [cy])
                status_box.set_text("Status: CIRCULAR MOTION DETECTED!")
                status_box.set_bbox(dict(boxstyle='round', facecolor='lightgreen', alpha=0.9))
            else:
                center_dot.set_data([], [])
                status_box.set_text("Status: Tracking motion...")
                status_box.set_bbox(dict(boxstyle='round', facecolor='wheat', alpha=0.8))

            plt.draw()
            plt.pause(0.02)

        except ValueError:
            # Ignore incomplete or corrupted serial lines (e.g. at start-up)
            continue

except KeyboardInterrupt:
    print("\nProgram terminated by user.")
finally:
    ser.close()
    plt.close('all')
    print("Serial connection closed.")