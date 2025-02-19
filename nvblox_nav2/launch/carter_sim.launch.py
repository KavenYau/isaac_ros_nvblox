# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    use_sim_time = LaunchConfiguration('use_sim_time', default='True')

    param_dir = LaunchConfiguration(
        'params_file',
        default=os.path.join(
            get_package_share_directory(
                'nvblox_nav2'), 'params', 'carter_nav2.yaml'
        ),
    )

    nvblox_param_dir = LaunchConfiguration(
        'nvblox_params_file',
        default=os.path.join(
            get_package_share_directory('nvblox_nav2'), 'params', 'nvblox.yaml'
        ),
    )

    nav2_bringup_launch_dir = os.path.join(
        get_package_share_directory('nav2_bringup'), 'launch')

    rviz_config_dir = os.path.join(get_package_share_directory(
        'nvblox_nav2'), 'config', 'carter_nvblox_nav2.rviz')

    lifecycle_nodes = ['map_server']

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'params_file', default_value=param_dir,
                description='Full path to param file to load'),
            DeclareLaunchArgument(
                'use_sim_time', default_value='True',
                description='Use simulation (Omniverse Isaac Sim) clock if true'),
            DeclareLaunchArgument(
                'run_rviz', default_value='True',
                description='Whether to start RVIZ'),
            DeclareLaunchArgument(
                'run_nav2', default_value='True',
                description='Whether to run nav2'),
            Node(
                package='nav2_lifecycle_manager', executable='lifecycle_manager',
                name='lifecycle_manager_map', output='screen',
                parameters=[{'use_sim_time': use_sim_time},
                            {'autostart': True},
                            {'node_names': lifecycle_nodes}],
                condition=IfCondition(LaunchConfiguration('run_nav2'))),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(nav2_bringup_launch_dir, 'rviz_launch.py')),
                launch_arguments={'namespace': '', 'use_namespace': 'False',
                                  'autostart': 'True',
                                  'rviz_config': rviz_config_dir}.items(),
                condition=IfCondition(LaunchConfiguration('run_rviz')),),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        nav2_bringup_launch_dir, 'navigation_launch.py')),
                launch_arguments={'use_sim_time': use_sim_time,
                                  'params_file': param_dir, 'autostart': 'True'}.items(),
                condition=IfCondition(
                    LaunchConfiguration('run_nav2')),
            ),
            Node(
                package='nvblox_ros', executable='nvblox_node',
                parameters=[nvblox_param_dir, {'use_sim_time': use_sim_time}],
                output='screen',
                remappings=[('depth/image', '/left/depth'),
                            ('depth/camera_info', '/left/camera_info'),
                            ('color/image', '/left/rgb'),
                            ('color/camera_info', '/left/camera_info'), ]),
            Node(
                package='tf2_ros', executable='static_transform_publisher',
                parameters=[{'use_sim_time': use_sim_time}],
                output='screen',
                arguments=['0.0', '0.0', '-0.3', '0.0', '0.0', '0.0', 'map',
                           'odom'],
                condition=IfCondition(
                    LaunchConfiguration('run_nav2'))),
        ])
