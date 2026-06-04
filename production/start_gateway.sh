#!/bin/bash
source /workspace/venv/bin/activate
cd /workspace/production

nohup python -m uvicorn main:app \
  --host 0.0.0.0 \
  --port 2222 \
  --workers 4 \
  --loop asyncio \
  --timeout-keep-alive 300 \
  --access-log \
  --log-level info \
  > /workspace/production/logs/gateway.log 2>&1 &

echo $! > /workspace/production/logs/gateway.pid
echo "✅ Gateway started PID: $(cat /workspace/production/logs/gateway.pid)"
