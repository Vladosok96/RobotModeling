"""Exercise ROS command boundaries using fake messages and Webots devices.

These tests check plugin logic; they do not exercise DDS or the ROS runtime.
"""
import importlib
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from ur5e_student_lab.trajectory import HOME, JOINT_NAMES


class Message:
    def __init__(self):
        self.header = SimpleNamespace(stamp=SimpleNamespace(sec=0, nanosec=0))


class Device:
    def __init__(self, position):
        self.position = position
        self.target = None

    def enable(self, timestep):
        pass

    def setVelocity(self, speed):
        pass

    def getValue(self):
        return self.position

    def setPosition(self, target):
        self.target = target


class DriverTests(unittest.TestCase):
    def setUp(self):
        self.published = []
        logger = SimpleNamespace(info=lambda _: None, warning=lambda _: None)
        node = SimpleNamespace(
            create_publisher=lambda *args: SimpleNamespace(publish=self.published.append),
            create_subscription=lambda *args: None,
            create_service=lambda *args: None, get_logger=lambda: logger,
        )
        modules = {
            'rclpy': SimpleNamespace(ok=lambda: True, create_node=lambda _: node,
                                     spin_once=lambda *args, **kwargs: None),
            'rclpy.qos': SimpleNamespace(qos_profile_sensor_data=object()),
            'sensor_msgs': SimpleNamespace(),
            'sensor_msgs.msg': SimpleNamespace(JointState=Message),
            'trajectory_msgs': SimpleNamespace(),
            'trajectory_msgs.msg': SimpleNamespace(JointTrajectory=Message),
            'std_srvs': SimpleNamespace(),
            'std_srvs.srv': SimpleNamespace(Trigger=object()),
        }
        self.module_patch = patch.dict(sys.modules, modules)
        self.module_patch.start()
        sys.modules.pop('ur5e_student_lab.driver', None)
        module = importlib.import_module('ur5e_student_lab.driver')
        self.devices = {}
        for name, q in zip(JOINT_NAMES, HOME):
            self.devices[name] = Device(q)
            self.devices[name + '_sensor'] = Device(q)
        self.now = 0.016
        robot = SimpleNamespace(getBasicTimeStep=lambda: 16,
                                getDevice=self.devices.get, getTime=lambda: self.now)
        self.driver = module.UR5eDriver()
        self.driver.init(SimpleNamespace(robot=robot), {})
        self.driver.step()

    def tearDown(self):
        sys.modules.pop('ur5e_student_lab.driver', None)
        self.module_patch.stop()

    def command(self, shift=0.1, seconds=3):
        return SimpleNamespace(
            header=SimpleNamespace(stamp=SimpleNamespace(sec=0, nanosec=0)),
            joint_names=list(JOINT_NAMES),
            points=[SimpleNamespace(positions=[q + shift for q in HOME],
                                    velocities=[], accelerations=[], effort=[],
                                    time_from_start=SimpleNamespace(sec=seconds, nanosec=0))],
        )

    def test_invalid_command_does_not_replace_motion(self):
        self.driver.command(self.command())
        active = self.driver.active
        self.driver.command(self.command(shift=1, seconds=0))
        self.assertIs(self.driver.active, active)

    def test_stop_holds_measured_pose_and_clears_trajectory(self):
        self.driver.command(self.command())
        response = self.driver.stop(None, SimpleNamespace(success=False, message=''))
        self.assertTrue(response.success)
        self.assertIsNone(self.driver.active)
        self.assertEqual(tuple(self.devices[name].target for name in JOINT_NAMES), HOME)

    def test_commands_reach_motors_and_feedback_is_measured(self):
        self.driver.command(self.command())
        self.now += 1.5
        self.driver.step()
        targets = tuple(self.devices[name].target for name in JOINT_NAMES)
        for target, initial in zip(targets, HOME):
            self.assertAlmostEqual(target, initial + 0.05)
        self.assertEqual(self.published[-1].position, list(HOME))
        self.assertEqual(self.published[-1].name, list(JOINT_NAMES))
