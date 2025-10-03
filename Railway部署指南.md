# 🚂 Railway部署指南 - 零基础版

## 为什么选择Railway？
- ✅ 完全免费开始使用
- ✅ 不需要服务器知识
- ✅ 一键部署
- ✅ 自动提供HTTPS网址
- ✅ 支持我们的Python应用

## 📋 部署步骤（10分钟完成）

### 第1步：注册Railway账号
1. 打开浏览器，访问：https://railway.app
2. 点击右上角 "Login" 
3. 选择 "Login with GitHub" （如果没有GitHub账号，先注册一个）
4. 授权Railway访问您的GitHub

### 第2步：创建新项目
1. 登录后，点击 "New Project"
2. 选择 "Deploy from GitHub repo"
3. 点击 "Deploy now"

### 第3步：上传代码
有两种方式：

**方式A：GitHub上传（推荐）**
1. 在GitHub创建新仓库
2. 将所有项目文件上传到GitHub仓库
3. 在Railway中连接该仓库

**方式B：直接上传**
1. 将所有文件打包成ZIP
2. 在Railway中选择 "Upload Zip"
3. 上传ZIP文件

### 第4步：添加数据库
1. 在项目面板中点击 "New Service"
2. 选择 "Database" → "Add Redis"
3. Redis会自动配置和连接

### 第5步：配置环境变量
1. 点击您的Web服务
2. 进入 "Variables" 标签
3. Railway会自动设置大部分变量

### 第6步：部署
1. 所有配置完成后，Railway会自动开始部署
2. 等待3-5分钟完成构建
3. 完成后会显示您的网站网址

## 🌐 获取访问网址
部署成功后：
1. 在项目面板找到您的Web服务
2. 点击 "Settings" → "Networking"
3. 会看到类似这样的网址：`https://yourapp.up.railway.app`

## 💰 费用说明
- **免费额度**：每月$5美元免费额度
- **用量计算**：按实际使用时间计费
- **预估成本**：轻度使用每月$0-3美元

## 🆘 如果遇到问题
1. **构建失败**：检查文件是否完整上传
2. **无法访问**：等待5分钟让部署完成
3. **功能异常**：检查Redis数据库是否已添加

## 📞 需要帮助？
如果任何步骤有问题，告诉我您在第几步遇到困难，我会详细指导您！