"""Publish one trajectory and verify measured motion and return to the initial pose."""
import math
import time
import os
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

from .trajectory import JOINT_NAMES, demo_points


class JointDemo(Node):
    def __init__(self):
        super().__init__('ur5e_joint_demo')
        self.publisher = self.create_publisher(JointTrajectory, '/ur5e/joint_trajectory', 10)
        self.subscription = self.create_subscription(
            JointState, '/joint_states', self.receive, qos_profile_sensor_data)
        self.current = None
        self.sim_time = None
        self.initial = None
        self.started = None
        self.excursions = [0.0] * 6
        self.done = False
        self.success = False
        self.get_logger().info('Waiting for UR5e joint feedback and command subscriber...')

    def receive(self, message):
        if len(message.name) != len(message.position) or not set(JOINT_NAMES).issubset(message.name):
            return
        current = tuple(message.position[message.name.index(name)] for name in JOINT_NAMES)
        if not all(math.isfinite(q) for q in current):
            return
        self.current = current
        self.sim_time = message.header.stamp.sec + message.header.stamp.nanosec / 1e9
        if self.initial is not None:
            self.excursions = [max(old, abs(q - initial)) for old, q, initial
                               in zip(self.excursions, current, self.initial)]

    def update(self):
        if self.current is None:
            return
        if self.started is None:
            if self.publisher.get_subscription_count() == 0 or self.sim_time < 1.0:
                return
            self.initial = self.current
            message = JointTrajectory()
            message.joint_names = list(JOINT_NAMES)
            for seconds, positions in demo_points(self.initial):
                point = JointTrajectoryPoint()
                point.positions = list(positions)
                point.time_from_start.sec = int(seconds)
                message.points.append(point)
            self.publisher.publish(message)
            self.started = self.sim_time
            self.get_logger().info('Sent 9 s trajectory: shoulder, elbow and wrists, then return')
        elif self.sim_time - self.started >= 10.5:
            error = max(abs(q - initial) for q, initial in zip(self.current, self.initial))
            moving = sum(excursion > 0.04 for excursion in self.excursions)
            self.success = error < 0.08 and moving >= 3
            self.done = True
            log = self.get_logger().info if self.success else self.get_logger().error
            log(f'{"PASS" if self.success else "FAIL"}: {moving} joints moved; '
                f'max return error = {error:.4f} rad')


def main(args=None):
    rclpy.init(args=args)
    node = JointDemo()
    timeout = float(os.environ.get('UR5E_DEMO_TIMEOUT', '60'))
    deadline = time.monotonic() + timeout
    try:
        while rclpy.ok() and not node.done and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.05)
            node.update()
        if not node.done:
            node.get_logger().error(f'No completed motion within {timeout:g} wall seconds; check driver and Webots Play')
        return 0 if node.success else 1
    except KeyboardInterrupt:
        return 130
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    raise SystemExit(main())
