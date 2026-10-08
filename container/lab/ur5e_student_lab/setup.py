from pathlib import Path
from setuptools import find_packages, setup

name = 'ur5e_student_lab'
data_files = [
    ('share/ament_index/resource_index/packages', ['resource/' + name]),
    ('share/' + name, ['package.xml', 'README.md', 'THIRD_PARTY.md', 'ASSETS.tsv', 'LICENSE']),
]
for folder in ('launch', 'config', 'webots', 'scripts'):
    for path in sorted(Path(folder).rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            data_files.append(('share/' + name + '/' + str(path.parent), [str(path)]))

setup(
    name=name, version='0.1.0', packages=find_packages(exclude=['tests']),
    data_files=data_files, install_requires=['setuptools'], zip_safe=False,
    tests_require=['pytest'],
    maintainer='Student robotics laboratory', maintainer_email='lab@example.com',
    description='UR5e Webots / ROS 2 Humble laboratory', license='Apache-2.0',
    entry_points={'console_scripts': ['joint_demo = ur5e_student_lab.demo:main']},
)
