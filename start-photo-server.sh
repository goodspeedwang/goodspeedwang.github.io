#!/bin/bash

MOUNT_POINT="/Volumes/Home1"
SERVER_PORT=8080
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="$MOUNT_POINT/Photo/other/weiyun/Photo/girl"

cd "$TARGET_DIR" || exit 1

# 复制 photo.html（静默）
cp "$SCRIPT_DIR/photo.html" . 2>/dev/null

echo "🚀 启动 HTTP 服务器 (端口 $SERVER_PORT)..."
python3 -m http.server $SERVER_PORT &
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
