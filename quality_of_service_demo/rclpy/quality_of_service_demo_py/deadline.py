# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import sys

from quality_of_service_demo_py.common_nodes import Listener
from quality_of_service_demo_py.common_nodes import Talker

import rclpy
from rclpy.duration import Duration
from rclpy.event_handler import PublisherEventCallbacks
from rclpy.event_handler import SubscriptionEventCallbacks
from rclpy.executors import ExternalShutdownException
from rclpy.executors import SingleThreadedExecutor
from rclpy.logging import get_logger
from rclpy.qos import QoSProfile


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'deadline', type=int,
        help='Duration in positive integer milliseconds of the Deadline QoS setting.')
    parser.add_argument(
        '--publish-for', type=int, default=5000,
        help='Duration in positive integer milliseconds to publish until pausing the talker.')
    parser.add_argument(
        '--pause-for', type=int, default=1000,
        help='Duration in positive integer milliseconds to pause the talker before beginning '
             'to publish again.')
    return parser.parse_args()


def main(args=None):
    try:
        parsed_args = parse_args()

        with rclpy.init(args=args):
            topic = 'qos_deadline_chatter'
            deadline = Duration(seconds=parsed_args.deadline / 1000.0)

            qos_profile = QoSProfile(
                depth=10,
                deadline=deadline)

            def sub_deadline_event(event):
                count = event.total_count
                delta = event.total_count_change
                get_logger('listener').info(
                    f'Requested deadline missed - total {count} delta {delta}')

            subscription_callbacks = SubscriptionEventCallbacks(deadline=sub_deadline_event)
            listener = Listener(topic, qos_profile, event_callbacks=subscription_callbacks)

            def pub_deadline_event(event):
                count = event.total_count
                delta = event.total_count_change
                get_logger('talker').info(f'Offered deadline missed - total {count} delta {delta}')

            publisher_callbacks = PublisherEventCallbacks(deadline=pub_deadline_event)
            talker = Talker(topic, qos_profile, event_callbacks=publisher_callbacks)

            publish_for_seconds = parsed_args.publish_for / 1000.0
            pause_for_seconds = parsed_args.pause_for / 1000.0
            pause_timer = talker.create_timer(  # noqa: F841
                publish_for_seconds,
                lambda: talker.pause_for(pause_for_seconds))

            executor = SingleThreadedExecutor()
            executor.add_node(listener)
            executor.add_node(talker)
            executor.spin()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass

    return 0


if __name__ == '__main__':
    sys.exit(main())
