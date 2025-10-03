import os
import uvicorn
from main import app

if __name__ == "__main__":
    # Replit特定配置
    host = "0.0.0.0"
    port = 8000
    
    # 检查是否在Replit环境中
    if os.environ.get('REPL_ID'):
        print("🔧 检测到Replit环境，使用优化配置")
        # Replit环境配置
        port = int(os.environ.get("PORT", 8000))
    else:
        # 其他环境配置
        port = int(os.environ.get("PORT", 8000))
    
    print(f"🚀 启动服务器在 {host}:{port}")
    print(f"🌐 WebSocket端点: ws://{host}:{port}/ws/")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        # 在Replit中关闭reload避免问题
        reload=False
    )