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
# import redis
from docx import Document
from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from services.translation_service import TranslationService
from services.tts_service import TTSService
from services.text_processor import TextProcessor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(title="佛经粤语翻译系统", version="1.0.0")

# 添加CORS中间件支持跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
translation_service = TranslationService()
tts_service = TTSService()
text_processor = TextProcessor()

# Redis连接（用于缓存和会话管理）
redis_client = None
# try:
#     redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
#     redis_client.ping()
#     logger.info("Redis连接成功")
# except:
#     logger.warning("Redis连接失败，使用内存缓存")
#     redis_client = None

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"客户端 {client_id} 已连接，当前连接数：{len(self.active_connections)}")
        
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"客户端 {client_id} 已断开，当前连接数：{len(self.active_connections)}")
            
    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
                self.disconnect(client_id)

manager = ConnectionManager()

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """返回主页面"""
    async with aiofiles.open("templates/index.html", mode="r", encoding="utf-8") as f:
        html_content = await f.read()
    return HTMLResponse(content=html_content)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件接口"""
    try:
        # 验证文件类型
        if not file.filename.lower().endswith(('.txt', '.doc', '.docx')):
            raise HTTPException(status_code=400, detail="只支持txt、doc、docx格式文件")
        
        # 生成唯一文件ID
        file_id = str(uuid.uuid4())
        
        # 保存上传的文件
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        file_path = temp_dir / f"{file_id}_{file.filename}"
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # 提取文本内容
        text_content = await text_processor.extract_text(file_path)
        
        # 分割文本为段落
        paragraphs = text_processor.split_into_paragraphs(text_content)
        
        # 缓存文本内容
        cache_key = f"file:{file_id}"
        if redis_client:
            redis_client.setex(cache_key, 3600, json.dumps({
                "paragraphs": paragraphs,
                "filename": file.filename,
                "total_paragraphs": len(paragraphs)
            }))
        
        logger.info(f"文件上传成功: {file.filename}, 段落数: {len(paragraphs)}")
        
        return {
            "status": "success",
            "file_id": file_id,
            "filename": file.filename,
            "total_paragraphs": len(paragraphs)
        }
        
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket连接处理"""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
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
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        manager.disconnect(client_id)

async def handle_file_translation(client_id: str, file_id: str):
    """处理文件翻译"""
    try:
        # 从缓存获取文件内容
        cache_key = f"file:{file_id}"
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if not cached_data:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "文件未找到或已过期"
                }, client_id)
                return
            
            file_data = json.loads(cached_data)
            paragraphs = file_data["paragraphs"]
        else:
            await manager.send_personal_message({
                "type": "error", 
                "message": "缓存服务不可用"
            }, client_id)
            return
        
        # 发送开始翻译消息
        await manager.send_personal_message({
            "type": "translation_start",
            "total_paragraphs": len(paragraphs)
        }, client_id)
        
        # 逐段翻译
        for i, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue
                
            # 翻译当前段落
            translated = await translation_service.translate_to_cantonese(paragraph)
            
            # 发送翻译结果
            await manager.send_personal_message({
                "type": "translation_result",
                "paragraph_id": i,
                "original": paragraph,
                "translated": translated,
                "progress": (i + 1) / len(paragraphs) * 100
            }, client_id)
            
            # 小延迟避免过载
            await asyncio.sleep(0.1)
        
        # 发送翻译完成消息
        await manager.send_personal_message({
            "type": "translation_complete"
        }, client_id)
        
    except Exception as e:
        logger.error(f"文件翻译失败: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"翻译失败: {str(e)}"
        }, client_id)

async def handle_text_translation(client_id: str, text: str):
    """处理单段文本翻译"""
    try:
        translated = await translation_service.translate_to_cantonese(text)
        
        await manager.send_personal_message({
            "type": "text_translation_result",
            "original": text,
            "translated": translated
        }, client_id)
        
    except Exception as e:
        logger.error(f"文本翻译失败: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"翻译失败: {str(e)}"
        }, client_id)

async def handle_audio_generation(client_id: str, text: str, paragraph_id: Optional[int] = None):
    """处理语音生成"""
    try:
        # 生成语音文件
        audio_file = await tts_service.generate_cantonese_audio(text)
        
        await manager.send_personal_message({
            "type": "audio_generated",
            "audio_url": f"/audio/{audio_file}",
            "paragraph_id": paragraph_id
        }, client_id)
        
    except Exception as e:
        logger.error(f"语音生成失败: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"语音生成失败: {str(e)}"
        }, client_id)

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """获取音频文件"""
    audio_path = Path("temp/audio") / filename
    if audio_path.exists():
        return FileResponse(audio_path, media_type="audio/wav")
    else:
        raise HTTPException(status_code=404, detail="音频文件未找到")

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "connections": len(manager.active_connections),
        "timestamp": time.time()
    }

if __name__ == "__main__":
    # 创建必要的目录
    Path("temp").mkdir(exist_ok=True)
    Path("temp/audio").mkdir(exist_ok=True)
    Path("static").mkdir(exist_ok=True)
    Path("templates").mkdir(exist_ok=True)
    
    # 启动服务器
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # 生产环境关闭reload
        log_level="info"
    )