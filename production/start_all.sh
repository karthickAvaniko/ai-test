#!/bin/bash
# One command to start everything — runs on pod start
source /workspace/venv/bin/activate
mkdir -p /workspace/production/logs

# Start supervisor (manages both vLLM + Gateway with auto-restart)
exec supervisord -c /workspace/production/supervisord.conf
