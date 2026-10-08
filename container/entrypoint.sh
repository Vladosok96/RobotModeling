#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/humble/setup.bash
source /opt/ur5e_ws/install/setup.bash
# A reused container can retain X server files after an interrupted shutdown.
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99
# An explicit virtual display makes the same image work on Windows and Linux.
Xvfb "$DISPLAY" -screen 0 1280x800x24 -ac -nolisten tcp &
xpid=$!
for attempt in {1..100}; do
  if xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then break; fi
  if ! kill -0 "$xpid" 2>/dev/null; then exit 1; fi
  sleep 0.1
done
xdpyinfo -display "$DISPLAY" >/dev/null
fluxbox >/tmp/fluxbox.log 2>&1 &
wm_pid=$!
# Raw VNC stays on container loopback; only the browser endpoint is published.
x11vnc -display "$DISPLAY" -localhost -rfbport 5900 -forever -shared -nopw \
  >/tmp/x11vnc.log 2>&1 &
vnc_pid=$!
websockify --web=/usr/share/novnc 8080 localhost:5900 &
web_pid=$!
python3 -c 'import os,signal,sys; signal.signal(signal.SIGINT,signal.SIG_DFL); os.execvp(sys.argv[1],sys.argv[1:])' "$@" &
ros_pid=$!
cleanup() {
  trap - INT TERM EXIT
  kill -INT "$ros_pid" 2>/dev/null || true
  for attempt in {1..150}; do
    kill -0 "$ros_pid" 2>/dev/null || break
    sleep 0.1
  done
  kill -TERM "$ros_pid" "$web_pid" "$vnc_pid" "$wm_pid" "$xpid" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT
echo 'UR5e desktop: http://localhost:8080/vnc.html?autoconnect=1&resize=scale'
set +e
wait -n "$ros_pid" "$web_pid" "$vnc_pid" "$wm_pid" "$xpid"
result=$?
exit "$result"
