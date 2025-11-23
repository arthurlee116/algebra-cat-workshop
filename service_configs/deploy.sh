#!/bin/bash
set -e  # 遇到错误立即停止

echo "🚀 Starting deployment..."

# 1. 进入项目目录并更新代码
cd /home/ubuntu/math
echo "📦 Pulling latest code..."
git fetch origin main
git reset --hard origin/main  # 强制重置到最新代码，避免冲突

# 2. 后端处理
echo "🐍 Updating Backend..."
cd backend
source .venv/bin/activate
pip install -r requirements.txt

# 3. 前端处理
echo "⚛️ Updating Frontend..."
cd ../frontend
npm install
echo "🏗️ Building Frontend..."
npm run build

# 4. 重启服务
echo "🔄 Restarting Services..."
sudo systemctl restart math-backend
sudo systemctl restart math-frontend

echo "✅ Deployment finished successfully!"
