import uvicorn
from api_server.main import app

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8080) # type: ignore # 192.168.31.30
