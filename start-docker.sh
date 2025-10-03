#!/bin/bash

# Docker部署脚本

echo "🐳 佛经粤语翻译系统 - Docker部署"
echo "=================================="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    echo "安装指南: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    echo "安装指南: https://docs.docker.com/compose/install/"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要目录..."
mkdir -p temp temp/audio logs

# 构建并启动服务
echo "🔨 构建Docker镜像..."
docker-compose build

echo "🚀 启动服务..."
docker-compose up -d

echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 服务状态:"
docker-compose ps

echo "=================================="
echo "✅ 部署完成！"
echo ""
echo "🌐 访问地址:"
echo "  - 主服务: http://localhost"
echo "  - 直接访问: http://localhost:8000"
echo "  - 负载均衡: http://localhost:8080"
echo ""
echo "📋 管理命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  查看状态: docker-compose ps"
echo ""
echo "📈 监控:"
echo "  - Redis: redis-cli -h localhost -p 6379"
echo "  - 健康检查: curl http://localhost/health"
echo "=================================="