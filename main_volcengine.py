"""
古文翻译粤语应用 - 使用火山方舟大模型版本
集成火山方舟豆包大模型，实现高质量古文到粤语的翻译
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import logging
import os

# 导入火山方舟翻译服务
from services.volcengine_translation_service import create_volcengine_translation_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(title="古文翻译粤语应用", description="使用火山方舟大模型翻译古文到地道粤语")

# 配置模板
templates = Jinja2Templates(directory="templates")

# 火山方舟API配置
VOLCENGINE_API_KEY = "75daa9cc-4673-4a3a-a578-3ac1ac988578"

# 全局翻译服务实例
translation_service = None

class TranslationRequest(BaseModel):
    """翻译请求模型"""
    text: str

class TranslationResponse(BaseModel):
    """翻译响应模型"""
    original_text: str
    translated_text: str
    success: bool
    error_message: str = ""

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    global translation_service
    try:
        # 初始化火山方舟翻译服务
        translation_service = create_volcengine_translation_service(VOLCENGINE_API_KEY)
        logger.info("火山方舟翻译服务初始化成功")
    except Exception as e:
        logger.error(f"翻译服务初始化失败: {e}")
        raise

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页面"""
    return templates.TemplateResponse("index_volcengine.html", {"request": request})

@app.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """
    翻译古文到粤语
    
    Args:
        request: 包含待翻译文本的请求
        
    Returns:
        翻译结果
    """
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="请输入要翻译的古文")
        
        original_text = request.text.strip()
        
        # 检查翻译服务是否可用
        if translation_service is None:
            raise HTTPException(status_code=500, detail="翻译服务未初始化")
        
        logger.info(f"开始翻译: {original_text[:50]}...")
        
        # 使用火山方舟大模型进行翻译
        translated_text = translation_service.translate_to_cantonese(original_text)
        
        if not translated_text:
            raise HTTPException(status_code=500, detail="翻译失败，请稍后重试")
        
        logger.info(f"翻译完成: {translated_text[:50]}...")
        
        return TranslationResponse(
            original_text=original_text,
            translated_text=translated_text,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"翻译过程出错: {str(e)}")
        return TranslationResponse(
            original_text=request.text,
            translated_text="",
            success=False,
            error_message=f"翻译失败: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "古文翻译粤语应用",
        "translation_engine": "火山方舟大模型",
        "version": "2.0"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {str(exc)}")
    return {"error": "服务器内部错误", "detail": str(exc)}

if __name__ == "__main__":
    # 确保必要的目录存在
    os.makedirs("templates", exist_ok=True)
    os.makedirs("services", exist_ok=True)
    
    print("🚀 启动古文翻译粤语应用 (火山方舟大模型版)")
    print("📝 访问 http://localhost:8000 使用应用")
    print("🔧 使用火山方舟豆包大模型提供高质量翻译")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )