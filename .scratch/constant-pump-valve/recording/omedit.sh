#!/usr/bin/env bash
exec podman run --rm --name omedit --security-opt label=disable --userns=keep-id --device /dev/dri \
  -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=:99 -e XDG_RUNTIME_DIR=/tmp \
  -v /tmp/claude-1000/-home-kslabolepszy-Dokumenty-GitHub-fish-sim-v0/5d5a578f-cf4a-46f8-b15b-ca9d4f529d38/scratchpad/rec/omhome:/home/u -e HOME=/home/u -e USER=kslabolepszy \
  -v /home/kslabolepszy/Dokumenty/GitHub/fish-sim-v0-wt/openmodelica:/work -w /work \
  docker.io/openmodelica/openmodelica:v1.27.1-gui \
  OMEdit /work/FishRobot/package.mo "$@"
