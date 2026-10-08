"""Python plugin loaded by webots_ros2_driver for the external UR5e controller."""
import math
import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory
from std_srvs.srv import Trigger

from .trajectory import JOINT_NAMES, MAX_SPEED, Trajectory


class UR5eDriver:
    def init(self, webots_node, properties):
        self.robot = webots_node.robot
        self.timestep = int(self.robot.getBasicTimeStep())
        self.motors = [self.robot.getDevice(name) for name in JOINT_NAMES]
        self.sensors = [self.robot.getDevice(name + '_sensor') for name in JOINT_NAMES]
        for motor, sensor in zip(self.motors, self.sensors):
            sensor.enable(self.timestep)
            motor.setVelocity(MAX_SPEED)
        if not rclpy.ok():
            rclpy.init(args=None)
        self.node = rclpy.create_node('ur5e_joint_driver')
        self.publisher = self.node.create_publisher(JointState, '/joint_states', qos_profile_sensor_data)
        self.subscription = self.node.create_subscription(
            JointTrajectory, '/ur5e/joint_trajectory', self.command, 10)
        self.stop_service = self.node.create_service(Trigger, '/ur5e/stop', self.stop)
        self.active = None
        self.start_time = 0.0
        self.previous = None
        self.previous_time = None
        self.last_publish = -1.0
        self.initialized = False
        self.node.get_logger().info('UR5e ready: /ur5e/joint_trajectory, /joint_states, /ur5e/stop')

    def positions(self):
        return tuple(sensor.getValue() for sensor in self.sensors)

    def command(self, message):
        try:
            if not self.initialized:
                raise ValueError('Wait for the first /joint_states message')
            if message.header.stamp.sec or message.header.stamp.nanosec:
                raise ValueError('Use a zero header timestamp: execution starts on receipt')
            points = []
            for point in message.points:
                if point.velocities or point.accelerations or point.effort:
                    raise ValueError('This laboratory driver accepts positions only')
                duration = point.time_from_start
                if duration.sec < 0 or not 0 <= duration.nanosec < 1_000_000_000:
                    raise ValueError('Invalid time_from_start')
                points.append((duration.sec + duration.nanosec / 1e9, point.positions))
            candidate = Trajectory(self.positions(), points, list(message.joint_names))
            # Only replace the active trajectory after the whole new command is validated.
            self.active = candidate
            self.start_time = self.robot.getTime()
            self.node.get_logger().info(f'Accepted trajectory: {candidate.duration:.1f} s')
        except (ValueError, TypeError) as error:
            self.node.get_logger().warning(f'Rejected trajectory: {error}')

    def stop(self, request, response):
        current = self.positions()
        if not all(math.isfinite(q) for q in current):
            response.success = False
            response.message = 'Joint sensors are not ready'
            return response
        self.active = None
        for motor, q in zip(self.motors, current):
            motor.setPosition(q)
        response.success = True
        response.message = 'Trajectory stopped; holding measured joint positions'
        return response

    def step(self):
        now = self.robot.getTime()
        current = self.positions()
        if not all(math.isfinite(q) for q in current):
            return
        if not self.initialized:
            for motor, q in zip(self.motors, current):
                motor.setPosition(q)
            self.initialized = True
        rclpy.spin_once(self.node, timeout_sec=0)
        if self.active:
            elapsed = now - self.start_time
            for motor, q in zip(self.motors, self.active.sample(elapsed)):
                motor.setPosition(q)
            if elapsed >= self.active.duration:
                self.active = None
                self.node.get_logger().info('Trajectory targets completed')
        if now - self.last_publish >= 0.032 - 1e-9:
            message = JointState()
            nanoseconds = round(now * 1e9)
            message.header.stamp.sec, message.header.stamp.nanosec = divmod(nanoseconds, 1_000_000_000)
            message.name = list(JOINT_NAMES)
            message.position = list(current)
            if self.previous is not None and now > self.previous_time:
                message.velocity = [(q - previous) / (now - self.previous_time)
                                    for q, previous in zip(current, self.previous)]
            else:
                message.velocity = [0.0] * 6
            self.publisher.publish(message)
            self.previous, self.previous_time = current, now
            self.last_publish = now
