"""Start an independent Webots scene, ROS driver and optional joint demonstration."""
from pathlib import Path
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, OpaqueFunction, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from webots_ros2_driver.webots_controller import WebotsController
from webots_ros2_driver.webots_launcher import WebotsLauncher
from webots_ros2_driver import utils as webots_utils
from webots_ros2_driver import webots_launcher as launcher_module


def start(context):
    # Docker Desktop and Docker in WSL share a Microsoft kernel, but Webots
    # runs inside this Linux container. Force local IPC instead of Windows TCP.
    if os.environ.get('UR5E_NATIVE_WEBOTS') == '1':
        webots_utils.is_wsl = lambda: False
        launcher_module.is_wsl = lambda: False
    # 2023.1.0 assumes the DNS server is the Windows host. Custom DNS in WSL
    # breaks that assumption; the default gateway is the actual host address.
    if webots_utils.is_wsl():
        webots_utils.get_wsl_ip_address = webots_utils.get_host_ip
    package = Path(get_package_share_directory('ur5e_student_lab'))
    port = LaunchConfiguration('port').perform(context)
    if not port.isdecimal() or not 1024 <= int(port) <= 65535:
        raise ValueError('port must be an integer in 1024..65535')
    webots = WebotsLauncher(
        world=str(package / 'webots/worlds/ur5e_lab.wbt'),
        mode='realtime', port=port, ros2_supervisor=True,
        gui=LaunchConfiguration('gui'),
    )
    driver = WebotsController(
        robot_name='UR5e', port=port,
        parameters=[{'robot_description': str(package / 'config/ur5e_driver.urdf')}],
        respawn=False,
    )
    demo = Node(
        package='ur5e_student_lab', executable='joint_demo', output='screen',
        parameters=[{'use_sim_time': True}], condition=IfCondition(LaunchConfiguration('demo')),
    )
    return [webots, webots._supervisor, driver, demo,
            RegisterEventHandler(OnProcessExit(
                target_action=webots, on_exit=[EmitEvent(event=Shutdown(reason='Webots closed'))]))]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('demo', default_value='false', description='Run one joint motion example'),
        DeclareLaunchArgument('gui', default_value='true', description='Render the Webots window'),
        DeclareLaunchArgument('port', default_value='1240', description='Webots controller port'),
        OpaqueFunction(function=start),
    ])
