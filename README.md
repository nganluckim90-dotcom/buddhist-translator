# 🙏 佛经粤语翻译系统

将佛经文言文实时翻译成最地道的广州粤语大白话，并提供粤语朗读功能的智能翻译系统。

## ✨ 主要功能

- 📄 **文档上传**: 支持 TXT、DOC、DOCX 格式，可处理几十MB的大文件
- 🔄 **实时翻译**: 文言文智能翻译成广州粤语大白话，保留佛教术语
- 🎵 **粤语朗读**: 广州本地口音的语音合成功能
- ⚡ **流式处理**: 大文件分片处理，确保流畅不卡顿
- 🌐 **Web界面**: 现代化响应式界面，支持移动设备
- 👥 **高并发**: 支持1000用户同时在线使用
- 📱 **无需注册**: 即开即用，保护用户隐私

## 🛠️ 技术架构

- **后端**: FastAPI + WebSocket + 异步处理
- **前端**: HTML5 + JavaScript + 现代CSS
- **翻译**: 优化的文言文到粤语翻译算法
- **语音**: Edge TTS 粤语语音合成
- **缓存**: Redis 缓存系统
- **部署**: Docker + Nginx 负载均衡

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

1. **前置要求**
   ```bash
   # 安装 Docker 和 Docker Compose
   # Ubuntu/Debian:
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo apt-get install docker-compose
   
   # macOS:
   brew install docker docker-compose
   ```

2. **启动服务**
   ```bash
   # 克隆项目
   git clone <repository-url>
   cd buddhist-cantonese-translator
   
   # 启动服务
   bash start-docker.sh
   ```

3. **访问系统**
   - 主服务: http://localhost
   - 直接访问: http://localhost:8000
   - 负载均衡: http://localhost:8080

### 方式二：本地开发

1. **安装依赖**
   ```bash
   # Python 3.8+
   pip install -r requirements.txt
   
   # Redis (Ubuntu/Debian)
   sudo apt-get install redis-server
   
   # Redis (macOS)
   brew install redis
   ```

2. **启动服务**
   ```bash
   # 启动 Redis
   redis-server --daemonize yes
   
   # 启动应用
   bash start.sh
   ```

3. **访问系统**
   - 访问地址: http://localhost:8000

## 📚 使用指南

### 1. 快速翻译
- 在首页的快速翻译区域输入文言文内容
- 点击"立即翻译"按钮
- 查看粤语译文并可播放语音

### 2. 文档翻译
- 点击"选择文件"上传佛经文档
- 支持的格式：TXT、DOC、DOCX
- 文件大小：最大支持几十MB
- 点击"开始翻译"进行批量翻译

### 3. 翻译特色
- **保留术语**: 阿弥陀佛、菩萨等佛教术语保持原样
- **生活化**: 其他内容翻译成广州老百姓日常用语
- **意译方式**: 注重语境和语感，而非逐字翻译

### 4. 语音功能
- 每段译文都可以点击"🔊 粤语朗读"
- 使用广州本地口音
- 支持语音缓存，重复播放更快

## 🔧 系统配置

### 性能参数
- **并发连接**: 1000+ WebSocket 连接
- **文件大小**: 最大 100MB
- **翻译速度**: 平均每段 0.5-2 秒
- **缓存时间**: 音频文件缓存 24小时

### 翻译设置
```python
# 在 services/translation_service.py 中配置
BUDDHIST_TERMS = {
    "阿弥陀佛", "南无阿弥陀佛", "观世音菩萨", 
    "文殊菩萨", "普贤菩萨", "地藏菩萨"
    # ... 更多术语
}
```

### 语音设置
```python
# 在 services/tts_service.py 中配置
CANTONESE_VOICES = [
    "zh-HK-HiuMaanNeural",  # 香港粤语 女声
    "zh-HK-WanLungNeural",  # 香港粤语 男声
]
```

## 📊 监控与管理

### Docker 环境
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down
```

### 健康检查
```bash
# 检查服务健康状态
curl http://localhost/health

# 检查 Redis 连接
redis-cli -h localhost -p 6379 ping
```

### 日志文件
- 应用日志: `logs/fastapi.out.log`
- 错误日志: `logs/fastapi.err.log`
- Nginx日志: `logs/nginx.out.log`
- Redis日志: `logs/redis.out.log`

## 🔍 故障排除

### 常见问题

1. **Redis 连接失败**
   ```bash
   # 检查 Redis 是否运行
   redis-cli ping
   
   # 启动 Redis
   redis-server --daemonize yes
   ```

2. **端口被占用**
   ```bash
   # 查看端口占用
   lsof -i :8000
   
   # 修改端口（在 docker-compose.yml 中）
   ports:
     - "8001:8000"
   ```

3. **文件上传失败**
   - 检查文件大小是否超过限制（100MB）
   - 确认文件格式是否支持（TXT、DOC、DOCX）
   - 检查磁盘空间是否充足

4. **翻译速度慢**
   - 增加 FastAPI 工作进程数量
   - 优化 Redis 缓存配置
   - 考虑使用更快的翻译API

### 性能优化

1. **增加工作进程**
   ```bash
   # 在 start.sh 中修改
   uvicorn main:app --workers 8 --host 0.0.0.0 --port 8000
   ```

2. **Redis 优化**
   ```bash
   # 增加 Redis 内存限制
   redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
   ```

3. **Nginx 缓存**
   ```nginx
   # 在 nginx.conf 中添加
   proxy_cache_path /tmp/nginx_cache levels=1:2 keys_zone=cache:10m;
   proxy_cache cache;
   ```

## 🤝 贡献指南

欢迎贡献代码和建议！

1. **Fork 项目**
2. **创建特性分支**: `git checkout -b feature/new-feature`
3. **提交更改**: `git commit -am 'Add new feature'`
4. **推送分支**: `git push origin feature/new-feature`
5. **创建 Pull Request**

### 开发环境设置
```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
python -m pytest tests/

# 代码格式化
black .
isort .
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- 感谢所有佛经文献的贡献者
- 感谢广州粤语文化的传承者
- 感谢开源社区的支持

## 📞 联系方式

- **问题反馈**: 请在 GitHub Issues 中提交
- **功能建议**: 欢迎通过 Issues 或 Discussions 提出
- **技术交流**: 欢迎提交 Pull Request

---

**愿此系统能够帮助更多人理解佛经智慧，传承粤语文化！** 🙏