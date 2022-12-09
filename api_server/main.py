from __future__ import annotations
import os
# import sys
import uvicorn
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from api_server.routers import basic, websocket_api, schedule, radio, rotator

with open(os.path.join(os.path.dirname(__file__), "api_description.md"), "r", encoding='utf-8') as f:
    description = f.read()

app: FastAPI = FastAPI(title="Coordinator server API")
app.include_router(rotator.router)
app.include_router(radio.router)
app.include_router(schedule.router)
app.include_router(websocket_api.router)
app.include_router(basic.router)

# idp.add_swagger_config(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# uvicorn GS_backend.__main__:app --proxy-headers --host 0.0.0.0 --port 8080

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8080)  # type: ignore # 192.168.31.30
# JobEvent (code=1024)>, code: 1024, type: <class 'int'>
# JobSubmissionEvent (code=32768)>, code: 32768, type: <class 'int'
# <JobExecutionEvent (code=4096)>, code: 4096, type: <class 'int'
