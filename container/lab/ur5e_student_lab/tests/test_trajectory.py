import math
import unittest
from ur5e_student_lab.trajectory import HOME, JOINT_NAMES, Trajectory, demo_points


class TrajectoryTests(unittest.TestCase):
    def test_demo_returns_to_start_and_moves_multiple_joints(self):
        trajectory = Trajectory(HOME, demo_points(HOME))
        self.assertEqual(trajectory.sample(0), HOME)
        self.assertEqual(trajectory.sample(12), HOME)
        self.assertGreater(sum(abs(a - b) > 0.04 for a, b in zip(trajectory.sample(3), HOME)), 2)

    def test_named_joint_reordering(self):
        target = tuple(q + 0.1 for q in HOME)
        trajectory = Trajectory(HOME, [(3, tuple(reversed(target)))], tuple(reversed(JOINT_NAMES)))
        self.assertEqual(trajectory.sample(3), target)

    def test_rejects_invalid_commands(self):
        cases = [[], [(0, HOME)], [(1, HOME), (1, HOME)],
                 [(1, [float('nan')] * 6)], [(1, [math.inf] * 6)],
                 [(1, [7.0] * 6)], [(1, HOME[:5])], [(0.1, [q + 1 for q in HOME])]]
        for points in cases:
            with self.subTest(points=points), self.assertRaises(ValueError):
                Trajectory(HOME, points)
        with self.assertRaises(ValueError):
            Trajectory(HOME, [(1, HOME)], [JOINT_NAMES[0]] * 6)

    def test_interpolated_speed_stays_within_bound(self):
        trajectory = Trajectory(HOME, demo_points(HOME))
        previous = trajectory.sample(0)
        for i in range(1, 901):
            current = trajectory.sample(i * 0.01)
            self.assertLessEqual(max(abs(a - b) / 0.01 for a, b in zip(current, previous)), 0.6)
            previous = current


if __name__ == '__main__':
    unittest.main()
