# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


import os
import pathlib
import time

from isaac_ros_test import IsaacROSBaseTest

import launch
from launch_ros.actions import Node

from nvblox_msgs.msg import DistanceMapSlice, Mesh

import pytest
import rclpy

_TEST_CASE_NAMESPACE = 'nvblox_test'


"""
    POL test for the Isaac ROS Nvblox node.

    1. Plays a ros bag recorded with Isaac SIM
    2. Nvblox node consumes the data and produces 3d Mesh
       and Map slice which is used as a costmap.
    3. This test expect the data to be available on topic nvblox_node/mesh
       and nvblox_node/map_slice.
"""


@pytest.mark.rostest
def generate_test_description():
    nvblox_node = Node(
        package='nvblox_ros',
        executable='nvblox_node',
        namespace=IsaacROSNvBloxTest.generate_namespace(_TEST_CASE_NAMESPACE),
        parameters=[{'global_frame': 'odom'}, {'use_sim_time': True}],
        remappings=[('depth/image', 'left/depth'),
                    ('depth/camera_info', 'left/camera_info'),
                    ('color/image', 'left/rgb'),
                    ('color/camera_info', 'left/camera_info')],
        output='screen'
    )

    rosbag_play = launch.actions.ExecuteProcess(
        cmd=['ros2', 'bag', 'play', os.path.dirname(__file__) +
             '/test_cases/rosbags/nvblox_pol',
             '--remap',
             'cmd_vel:=' +
             IsaacROSNvBloxTest.generate_namespace(_TEST_CASE_NAMESPACE) + '/cmd_vel',
             'clock:=' +
             IsaacROSNvBloxTest.generate_namespace(_TEST_CASE_NAMESPACE) + '/clock',
             'left/depth:=' +
             IsaacROSNvBloxTest.generate_namespace(_TEST_CASE_NAMESPACE) + '/left/depth',
             'left/camera_info:=' +
             IsaacROSNvBloxTest.generate_namespace(_TEST_CASE_NAMESPACE) + '/left/camera_info',
             'left/rgb:=' +
             IsaacROSNvBloxTest.generate_namespace(_TEST_CASE_NAMESPACE) + '/left/rgb'],
        output='screen')

    return IsaacROSNvBloxTest.generate_test_description(
        [nvblox_node, rosbag_play])


class IsaacROSNvBloxTest(IsaacROSBaseTest):
    filepath = pathlib.Path(os.path.dirname(__file__))

    @ IsaacROSBaseTest.for_each_test_case('rosbags')
    def test_nvblox_node(self, test_folder):
        TIMEOUT = 60
        received_messages = {}
        self.generate_namespace_lookup(
            ['nvblox_node/mesh', 'nvblox_node/map_slice'], _TEST_CASE_NAMESPACE)
        subs = self.create_logging_subscribers(
            [('nvblox_node/mesh', Mesh), ('nvblox_node/map_slice', DistanceMapSlice)],
            received_messages,
            use_namespace_lookup=True, accept_multiple_messages=True)

        try:
            end_time = time.time() + TIMEOUT
            done = False

            while time.time() < end_time:
                rclpy.spin_once(self.node, timeout_sec=0.1)

            if len(received_messages['nvblox_node/mesh']) > 0 and \
                    len(received_messages['nvblox_node/map_slice']) > 0:
                done = True

            self.assertTrue(
                done, 'Didnt recieve output on nvblox_node/mesh or nvblox_node/map_slice topic')

        finally:
            [self.node.destroy_subscription(sub) for sub in subs]
