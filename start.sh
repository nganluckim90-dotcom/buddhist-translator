#!/bin/bash

# 佛经粤语翻译系统启动脚本

echo "🙏 佛经粤语翻译系统启动脚本"
echo "=================================="

# 检查Python版本
echo "📋 检查Python环境..."
python_version=$(python3 --version 2>&1)
echo "Python版本: $python_version"

# 检查是否安装了pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 未安装，请先安装pip3"
    exit 1
fi

# 安装Python依赖
echo "📦 安装Python依赖..."
pip3 install -r requirements.txt

# 检查Redis是否运行
echo "🔍 检查Redis服务..."
if ! pgrep -x "redis-server" > /dev/null; then
    echo "⚠️  Redis未运行，尝试启动Redis..."
    if command -v redis-server &> /dev/null; then
        redis-server --daemonize yes
        echo "✅ Redis已启动"
    else
        echo "❌ Redis未安装，请安装Redis或使用Docker方式运行"
        echo "Ubuntu/Debian: sudo apt-get install redis-server"
        echo "MacOS: brew install redis"
        echo "或者使用Docker: docker run -d -p 6379:6379 redis:alpine"
    fi
fi

# 创建必要的目录
echo "📁 创建必要目录..."
mkdir -p temp temp/audio static templates logs

# 启动应用
echo "🚀 启动应用服务器..."
echo "访问地址: http://localhost:8000"
echo "按 Ctrl+C 停止服务"
echo "=================================="

python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload