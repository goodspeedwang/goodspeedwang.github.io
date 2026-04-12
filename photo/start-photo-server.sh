#!/bin/bash
SERVER_PORT=8080
TARGET_DIR="/Volumes/Home1/Photo/other/weiyun/Photo/girl"
SERVER_DIR="/Users/goodspeedwang/Document/code/private/goodspeedwang.github.io/photo/server.py"

echo "🚀 启动 HTTP 服务器 (端口 $SERVER_PORT)..."
python3 $SERVER_DIR $SERVER_PORT $TARGET_DIR &
SERVER_PID=$!
sleep 1

# 打开浏览器
open "http://localhost:$SERVER_PORT/photo.html"

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
