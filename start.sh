#!/bin/bash

echo "正在启动 WireGuard 管理面板..."

# 启动后端（需要 sudo 权限来管理网络接口）
echo "启动后端服务（需要 sudo 权限）..."
sudo python3 app.py &
BACKEND_PID=$!

# 等待后端启动
sleep 2

# 启动前端
cd ../frontend
echo "启动前端服务..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ WireGuard 管理面板已启动！"
echo "   前端界面: http://localhost:3000"
echo "   后端 API: http://localhost:5001"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
