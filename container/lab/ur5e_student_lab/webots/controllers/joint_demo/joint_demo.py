"""Local Webots check of the same trajectory engine, without ROS installation."""
from pathlib import Path
import csv
import json
import math
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from ur5e_student_lab.trajectory import JOINT_NAMES, MAX_SPEED, Trajectory, demo_points
from controller import Robot

robot = Robot()
dt = int(robot.getBasicTimeStep())
motors = [robot.getDevice(name) for name in JOINT_NAMES]
sensors = [robot.getDevice(name + '_sensor') for name in JOINT_NAMES]
for motor, sensor in zip(motors, sensors):
    motor.setVelocity(MAX_SPEED)
    sensor.enable(dt)
if robot.step(dt) == -1:
    raise SystemExit(1)
initial = tuple(sensor.getValue() for sensor in sensors)
if not all(math.isfinite(q) for q in initial):
    raise RuntimeError('Joint sensors returned invalid values')
for motor, q in zip(motors, initial):
    motor.setPosition(q)
trajectory = Trajectory(initial, demo_points(initial))
start = robot.getTime() + 1.0
excursions = [0.0] * 6
output = Path(os.environ.get('UR5E_DEMO_OUTPUT', str(Path(__file__).with_name('demo-result.json'))))
output.parent.mkdir(parents=True, exist_ok=True)
result_written = False
with output.with_suffix('.csv').open('w', newline='', encoding='utf-8') as stream:
    writer = csv.writer(stream)
    writer.writerow(['time', *JOINT_NAMES])
    while robot.step(dt) != -1:
        elapsed = robot.getTime() - start
        measured = tuple(sensor.getValue() for sensor in sensors)
        if not result_written:
            writer.writerow([elapsed, *measured])
            excursions = [max(old, abs(q - origin)) for old, q, origin
                           in zip(excursions, measured, initial)]
            for motor, q in zip(motors, trajectory.sample(elapsed)):
                motor.setPosition(q)
            if elapsed >= trajectory.duration + 1.5:
                error = max(abs(q - origin) for q, origin in zip(measured, initial))
                moved = sum(value > 0.04 for value in excursions)
                result = {'passed': error < 0.08 and moved >= 3,
                          'moved_joints': moved, 'max_return_error_rad': error,
                          'excursions_rad': excursions, 'final_positions': measured}
                output.write_text(json.dumps(result, indent=2), encoding='utf-8')
                stream.flush()
                print(json.dumps(result), flush=True)
                result_written = True
