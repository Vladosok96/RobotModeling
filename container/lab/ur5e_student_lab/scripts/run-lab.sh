#!/usr/bin/env bash
set -eo pipefail
workspace=${UR5E_WORKSPACE:-"$HOME/ur5e_ws"}
source /opt/ros/humble/setup.bash
source "$workspace/install/setup.bash"
if grep -qi microsoft /proc/sys/kernel/osrelease && [[ -z ${WEBOTS_HOME:-} ]]; then
  export WEBOTS_HOME=/mnt/c/Users/vlaDick/.local/Webots-R2023b
fi
exec ros2 launch ur5e_student_lab lab.launch.py demo:=true "$@"
