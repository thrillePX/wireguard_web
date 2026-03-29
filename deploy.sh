#!/bin/bash
set -e

echo "======================================"
echo "  WireGuard Manager - Docker Deploy"
echo "======================================"

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 docker-compose 是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装"
    exit 1
fi

# 使用 docker compose 或 docker-compose
if docker compose version &> /dev/null; then
    COMPOSE="docker compose"
else
    COMPOSE="docker-compose"
fi

echo ""
echo "📦 正在构建 Docker 镜像..."
$COMPOSE build

echo ""
echo "🚀 正在启动服务..."
$COMPOSE up -d

echo ""
echo "✅ 部署完成！"
echo ""
echo "   前端地址: http://localhost:3000"
echo "   后端地址: http://localhost:5001"
echo ""
echo "======================================"
echo ""
echo "常用命令:"
echo "  查看日志:   $COMPOSE logs -f"
echo "  停止服务:   $COMPOSE down"
echo "  重启服务:   $COMPOSE restart"
echo "  重新构建:   $COMPOSE up -d --build"
echo ""
