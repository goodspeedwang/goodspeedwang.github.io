#!/bin/bash
SERVER_PORT=8080
TARGET_DIR="/Volumes/Home1/Photo/other/weiyun/Photo/girl"
SERVER_DIR="/Users/goodspeedwang/Document/code/private/goodspeedwang.github.io/photo"

echo "🚀 启动 HTTP 服务器 (端口 $SERVER_PORT)..."
# 先杀掉占用端口的旧进程
lsof -ti:$SERVER_PORT | xargs kill -9 2>/dev/null || true
python3 $SERVER_DIR/server.py $SERVER_PORT $TARGET_DIR &
SERVER_PID=$!
sleep 1

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  服务运行中: http://localhost:$SERVER_PORT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "按 Ctrl+C 停止..."

cleanup() {
    echo ""
    echo "🛑 停止服务..."
    kill $SERVER_PID 2>/dev/null
    echo "✅ 已停止"
    exit 0
}

trap cleanup INT TERM
wait
