import asyncio
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional
import uuid

import aiofiles
import httpx
from docx import Document
from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# 导入增强的服务
try:
    from services.translation_service_enhanced import TranslationService
except ImportError:
    # 如果增强版本不存在，使用修复版本
    try:
        from services.translation_service_fixed import TranslationService
    except ImportError:
        from services.translation_service import TranslationService

try:
    from services.tts_service_web import TTSService
except ImportError:
    from services.tts_service import TTSService

from services.text_processor import TextProcessor

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建必要的目录
def create_directories():
    dirs = ["temp", "temp/audio", "static", "templates", "logs"]
    for dir_name in dirs:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
        logger.info(f"创建目录: {dir_name}")

create_directories()

# 创建FastAPI应用
app = FastAPI(title="佛经粤语翻译系统 - 增强版", version="2.0.0")

# 添加CORS中间件支持跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
logger.info("初始化增强服务...")
translation_service = TranslationService()
tts_service = TTSService()
text_processor = TextProcessor()
logger.info("增强服务初始化完成")

# 内存缓存替代Redis
memory_cache = {}
logger.info("内存缓存系统初始化完成")

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"✅ 客户端 {client_id} 已连接，当前连接数: {len(self.active_connections)}")
        
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"❌ 客户端 {client_id} 已断开，当前连接数: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message, ensure_ascii=False))
                logger.debug(f"📨 向客户端 {client_id} 发送消息: {message.get('type', 'unknown')}")
            except Exception as e:
                logger.error(f"❌ 发送消息失败: {e}")
                self.disconnect(client_id)

manager = ConnectionManager()

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """返回主页"""
    try:
        async with aiofiles.open("templates/index_enhanced.html", "r", encoding="utf-8") as f:
            content = await f.read()
        logger.info("✅ 增强主页加载成功")
        return HTMLResponse(content=content)
    except FileNotFoundError:
        # 如果增强版不存在，使用原版
        try:
            async with aiofiles.open("templates/index.html", "r", encoding="utf-8") as f:
                content = await f.read()
            logger.info("✅ 主页加载成功（原版）")
            return HTMLResponse(content=content)
        except FileNotFoundError:
            logger.error("❌ 模板文件未找到")
            return HTMLResponse("<h1>模板文件未找到</h1>")

@app.get("/health")
async def health_check():
    """健康检查端点"""
    health_info = {
        "status": "healthy",
        "version": "2.0.0 - Enhanced",
        "timestamp": time.time(),
        "connections": len(manager.active_connections),
        "cache_size": len(memory_cache),
        "features": {
            "enhanced_translation": True,
            "web_speech_tts": True,
            "cantonese_optimization": True
        }
    }
    logger.info(f"🏥 健康检查: {health_info}")
    return health_info

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件"""
    try:
        logger.info(f"📁 开始处理文件上传: {file.filename}")
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="没有选择文件")
        
        # 检查文件类型
        allowed_extensions = ['.txt', '.doc', '.docx']
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail="不支持的文件格式")
        
        # 生成文件ID
        file_id = str(uuid.uuid4())
        logger.info(f"🔑 生成文件ID: {file_id}")
        
        # 读取文件内容
        content = await file.read()
        logger.info(f"📊 文件读取完成，大小: {len(content)} 字节")
        
        # 处理文件内容
        if file_extension == '.txt':
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text_content = content.decode('gbk')
                except UnicodeDecodeError:
                    text_content = content.decode('utf-8', errors='ignore')
        elif file_extension in ['.doc', '.docx']:
            # 保存临时文件
            temp_path = f"temp/{file_id}{file_extension}"
            with open(temp_path, 'wb') as f:
                f.write(content)
            
            # 提取文本
            text_content = text_processor.extract_text_from_docx(temp_path)
            
            # 删除临时文件
            os.remove(temp_path)
        
        logger.info(f"📝 文本提取完成，长度: {len(text_content)} 字符")
        
        # 存储到内存缓存
        cache_key = f"file:{file_id}"
        cache_data = {
            "filename": file.filename,
            "content": text_content,
            "upload_time": time.time(),
            "file_id": file_id
        }
        memory_cache[cache_key] = cache_data
        
        logger.info(f"💾 文件缓存成功，缓存键: {cache_key}")
        logger.info(f"🎉 文件上传完成: {file.filename}")
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "size": len(content),
            "text_length": len(text_content),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"❌ 文件上传失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """增强WebSocket连接处理"""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            logger.info(f"📨 收到来自 {client_id} 的消息: {message.get('type', 'unknown')}")
            
            if message["type"] == "translate_file":
                # 开始翻译文件
                await handle_file_translation(client_id, message["file_id"])
            elif message["type"] == "translate_text":
                # 翻译单段文本
                await handle_text_translation(client_id, message["text"])
            elif message["type"] == "generate_audio":
                # 生成语音
                await handle_audio_generation(client_id, message["text"], message.get("paragraph_id"))
                
    except WebSocketDisconnect:
        logger.info(f"🔌 客户端 {client_id} 正常断开连接")
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"❌ WebSocket错误 {client_id}: {e}", exc_info=True)
        manager.disconnect(client_id)

async def handle_file_translation(client_id: str, file_id: str):
    """处理文件翻译（增强版）"""
    try:
        logger.info(f"🔄 开始增强文件翻译 - 客户端: {client_id}, 文件ID: {file_id}")
        
        # 从内存缓存获取文件内容
        cache_key = f"file:{file_id}"
        
        if cache_key not in memory_cache:
            logger.error(f"❌ 缓存中未找到文件: {cache_key}")
            await manager.send_personal_message({
                "type": "error",
                "message": f"文件未找到或已过期 (ID: {file_id})"
            }, client_id)
            return
        
        file_data = memory_cache[cache_key]
        content = file_data["content"]
        
        logger.info(f"✅ 从缓存获取文件成功: {file_data['filename']}")
        
        # 分段处理文本
        paragraphs = text_processor.split_text_into_paragraphs(content)
        logger.info(f"📄 文本分段完成，共 {len(paragraphs)} 段")
        
        # 发送开始信号
        await manager.send_personal_message({
            "type": "translation_start",
            "total_paragraphs": len(paragraphs),
            "filename": file_data["filename"],
            "enhancement": "地道粤语翻译"
        }, client_id)
        
        # 逐段翻译（使用增强版本）
        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                logger.info(f"🔤 增强翻译第 {i+1}/{len(paragraphs)} 段: {paragraph[:50]}...")
                
                try:
                    # 使用增强翻译服务
                    translated = await translation_service.translate_to_cantonese(paragraph.strip())
                    logger.info(f"✅ 增强翻译完成: {translated[:50]}...")
                    
                    # 发送翻译结果
                    await manager.send_personal_message({
                        "type": "translation_result",
                        "paragraph_id": i,
                        "original": paragraph.strip(),
                        "translated": translated,
                        "progress": ((i + 1) / len(paragraphs)) * 100,
                        "enhancement": "cantonese_optimized"
                    }, client_id)
                    
                    # 短暂延迟
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"❌ 段落翻译失败: {e}")
                    # 发送错误，但继续处理下一段
                    await manager.send_personal_message({
                        "type": "translation_result",
                        "paragraph_id": i,
                        "original": paragraph.strip(),
                        "translated": f"翻译出错: {paragraph.strip()}",
                        "progress": ((i + 1) / len(paragraphs)) * 100
                    }, client_id)
        
        # 发送完成信号
        logger.info("🎉 增强文件翻译完成")
        await manager.send_personal_message({
            "type": "translation_complete",
            "enhancement": "cantonese_enhanced"
        }, client_id)
        
    except Exception as e:
        logger.error(f"❌ 增强文件翻译失败: {e}", exc_info=True)
        await manager.send_personal_message({
            "type": "error",
            "message": f"增强翻译失败: {str(e)}"
        }, client_id)

async def handle_text_translation(client_id: str, text: str):
    """处理文本翻译（增强版）"""
    try:
        logger.info(f"🔤 增强文本翻译: {text[:50]}...")
        translated = await translation_service.translate_to_cantonese(text)
        await manager.send_personal_message({
            "type": "text_translation_result",
            "original": text,
            "translated": translated,
            "enhancement": "cantonese_optimized"
        }, client_id)
        logger.info("✅ 增强文本翻译完成")
    except Exception as e:
        logger.error(f"❌ 增强文本翻译失败: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"增强翻译失败: {str(e)}"
        }, client_id)

async def handle_audio_generation(client_id: str, text: str, paragraph_id: Optional[int] = None):
    """处理语音生成（Web版本）"""
    try:
        logger.info(f"🔊 生成Web语音: {text[:50]}...")
        audio_id = await tts_service.generate_speech(text)
        
        # 获取音频配置
        audio_config = tts_service.get_audio_config(audio_id)
        
        await manager.send_personal_message({
            "type": "audio_ready",
            "audio_config": audio_config,
            "paragraph_id": paragraph_id,
            "web_speech": True
        }, client_id)
        logger.info("✅ Web语音配置生成完成")
    except Exception as e:
        logger.error(f"❌ Web语音生成失败: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"语音生成失败: {str(e)}"
        }, client_id)

@app.get("/audio/{audio_id}")
async def get_audio_config(audio_id: str):
    """获取音频配置"""
    try:
        config = tts_service.get_audio_config(audio_id)
        return JSONResponse(content=config)
    except Exception as e:
        logger.error(f"获取音频配置失败: {e}")
        raise HTTPException(status_code=404, detail="音频配置未找到")

# 清理过期缓存的定时任务
async def cleanup_cache():
    """清理过期的缓存"""
    while True:
        try:
            current_time = time.time()
            expired_keys = []
            
            for key, data in memory_cache.items():
                # 缓存1小时后过期
                if current_time - data.get('upload_time', 0) > 3600:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del memory_cache[key]
                logger.info(f"🗑️ 清理过期缓存: {key}")
            
            if expired_keys:
                logger.info(f"🧹 清理了 {len(expired_keys)} 个过期缓存项")
            
            # 清理旧音频文件
            tts_service.cleanup_old_files()
                
        except Exception as e:
            logger.error(f"❌ 缓存清理失败: {e}")
        
        # 每10分钟清理一次
        await asyncio.sleep(600)

# 启动时创建清理任务
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 增强应用启动，创建缓存清理任务")
    asyncio.create_task(cleanup_cache())

if __name__ == "__main__":
    # Replit环境检测和配置
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 8000))
    
    logger.info("=" * 60)
    logger.info("🙏 佛经粤语翻译系统 - 增强版 启动")
    logger.info("=" * 60)
    logger.info(f"🌐 地址: http://{host}:{port}")
    logger.info(f"🔌 WebSocket: ws://{host}:{port}/ws/")
    logger.info(f"💾 缓存系统: 内存缓存")
    logger.info(f"🔧 环境: {'Replit' if os.environ.get('REPL_ID') else '本地'}")
    logger.info(f"✨ 增强功能: 地道粤语翻译 + Web语音")
    logger.info("=" * 60)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        reload=False  # Replit中关闭reload
    )