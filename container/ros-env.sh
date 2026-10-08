#!/usr/bin/env bash
set -e
source /opt/ros/humble/setup.bash
source /opt/ur5e_ws/install/setup.bash
exec "$@"
