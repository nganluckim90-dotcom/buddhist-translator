#!/usr/bin/env python3

import asyncio
import sys
import uvicorn

if __name__ == "__main__":
    # 设置正确的Python路径
    sys.path.insert(0, '.')
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )