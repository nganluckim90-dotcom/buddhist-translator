import os
import uvicorn
from main import app

if __name__ == "__main__":
    # Railway会设置PORT环境变量
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )