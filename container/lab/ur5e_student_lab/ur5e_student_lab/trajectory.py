"""ROS-independent joint trajectory validation and smooth interpolation.

Each segment uses 3u²-2u³, with zero velocity at its endpoints.
Angles are radians; times are simulation seconds.
"""
import math

JOINT_NAMES = (
    'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
    'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint',
)
HOME = (-0.392663289113, -1.965166763601, 1.799579124285,
        -1.405304983075, -1.570894794132, -1.962614772082)
MAX_SPEED = 0.6
POSITION_LIMIT = 2 * math.pi


def demo_points(start):
    """Small excursions of shoulder, elbow and wrist, then return."""
    offsets = ((0.20, 0.10, -0.10, 0.15, 0.0, 0.15),
               (-0.15, -0.08, 0.08, -0.10, 0.0, -0.15),
               (0.0,) * 6)
    return [(3.0 * (i + 1), tuple(q + dq for q, dq in zip(start, offset)))
            for i, offset in enumerate(offsets)]


class Trajectory:
    def __init__(self, start, points, joint_names=JOINT_NAMES):
        if len(joint_names) != 6 or set(joint_names) != set(JOINT_NAMES):
            raise ValueError('Specify each of the six UR5e joints exactly once')
        if len(start) != 6 or not all(math.isfinite(q) for q in start):
            raise ValueError('Joint sensors are not ready')
        if not points or len(points) > 100:
            raise ValueError('A trajectory must contain 1..100 points')
        order = [joint_names.index(name) for name in JOINT_NAMES]
        self.points = [(0.0, tuple(start))]
        for duration, positions in points:
            if len(positions) != 6:
                raise ValueError('Each point must have six positions')
            positions = tuple(positions[i] for i in order)
            previous_time, previous = self.points[-1]
            if not math.isfinite(duration) or duration <= previous_time:
                raise ValueError('Point times must be finite, positive and strictly increasing')
            if not all(math.isfinite(q) and abs(q) <= POSITION_LIMIT for q in positions):
                raise ValueError('Joint positions must be finite and within +/-2*pi')
            if max(1.5 * abs(q - old) / (duration - previous_time)
                   for q, old in zip(positions, previous)) > MAX_SPEED + 1e-9:
                raise ValueError('Trajectory exceeds 0.6 rad/s; increase segment duration')
            self.points.append((float(duration), positions))

    @property
    def duration(self):
        return self.points[-1][0]

    def sample(self, elapsed):
        if elapsed <= 0:
            return self.points[0][1]
        for (t0, q0), (t1, q1) in zip(self.points, self.points[1:]):
            if elapsed <= t1:
                u = (elapsed - t0) / (t1 - t0)
                blend = u * u * (3 - 2 * u)
                return tuple(a + blend * (b - a) for a, b in zip(q0, q1))
        return self.points[-1][1]
