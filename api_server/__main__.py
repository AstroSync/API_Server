import os
import uvicorn
from api_server.main import app

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get('API_PORT', '8080')))  # type: ignore # 192.168.31.30