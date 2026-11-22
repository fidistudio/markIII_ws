from launch import LaunchDescription
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    robot_description = Command(
        [
            "xacro ",
            PathJoinSubstitution(
                [FindPackageShare("markIII_description"), "urdf", "markIII.urdf.xacro"]
            ),
        ]
    )

    return LaunchDescription(
        [
            # JOINT STATE PUBLISHER GUI
            Node(
                package="joint_state_publisher_gui",
                executable="joint_state_publisher_gui",
                name="joint_state_publisher_gui",
                output="screen",
            ),
            # ROBOT STATE PUBLISHER
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                output="screen",
                parameters=[{"robot_description": robot_description}],
            ),
            # RVIZ2
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz2",
                output="screen",
                arguments=[
                    "-d",
                    PathJoinSubstitution(
                        [
                            FindPackageShare("markIII_description"),
                            "rviz",
                            "view_bot.rviz",
                        ]
                    ),
                ],
            ),
        ]
    )
