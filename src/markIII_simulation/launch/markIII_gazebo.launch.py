import os
from os.path import join

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg_ros_gz_sim = get_package_share_directory("ros_gz_sim")
    pkg_sim = get_package_share_directory("markIII_simulation")

    world_file = LaunchConfiguration(
        "world_file", default=join(pkg_sim, "worlds", "warehouse_world.sdf")
    )

    robot_description_file = join(pkg_sim, "urdf", "markIII_sim.urdf.xacro")
    bridge_config = join(pkg_sim, "config", "ros_gz_bridge.yaml")

    robot_description = {
        "robot_description": xacro.process_file(robot_description_file).toxml()
    }

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            join(pkg_ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={"gz_args": [world_file, " -r"]}.items(),
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", join(pkg_sim, "rviz", "robot_view.rviz")],
        parameters=[{"use_sim_time": True}],
    )

    spawn = Node(
        package="ros_gz_sim",
        executable="create",
        parameters=[{"name": "markIII", "topic": "robot_description"}],
        output="screen",
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[{"config_file": bridge_config}],
        output="screen",
    )

    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
        output="screen",
    )

    # Remapeos para que los tópicos sean /cmd_vel y /odom, igual que en el robot real
    diff_drive_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "diff_drive_controller",
            "--controller-manager",
            "/controller_manager",
            "--controller-ros-args",
            "-r /diff_drive_controller/cmd_vel:=/cmd_vel "
            "-r /diff_drive_controller/odom:=/odom",
        ],
        output="screen",
    )

    # Cadena: spawn -> joint_state_broadcaster -> diff_drive_controller
    load_jsb = RegisterEventHandler(
        OnProcessExit(target_action=spawn, on_exit=[joint_state_broadcaster])
    )
    load_diff = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_broadcaster, on_exit=[diff_drive_controller]
        )
    )

    return LaunchDescription(
        [
            gazebo,
            robot_state_publisher,
            spawn,
            bridge,
            load_jsb,
            load_diff,
            rviz,
        ]
    )
