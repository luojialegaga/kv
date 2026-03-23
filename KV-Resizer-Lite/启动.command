#!/bin/bash

echo "=========================================="
echo "  KV Resizer Lite"
echo "  精简版 - 只保留核心出图功能"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 需要安装 Python 3"
    exit 1
fi

# 检查依赖
if ! python3 -c "import flask" 2>/dev/null; then
    echo "正在安装 Flask..."
    pip3 install flask requests -q
fi

echo "启动服务..."
echo ""

python3 app.py
