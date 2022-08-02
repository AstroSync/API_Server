from __future__ import annotations
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api_server.database_api import db_get_all_sessions
from api_server.routers import websocket_api, basic

with open("./api_description.md", "r", encoding='utf-8') as f:
    description = f.read()


app = FastAPI(title="Coordinator API", description=description)
app.include_router(websocket_api.router)
app.include_router(basic.basic_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
print(f'There is {len(db_get_all_sessions())} pending sessions')


def main():
    uvicorn.run(app, host="0.0.0.0", port=80)
# asyncio.run(connect_ground_stations())


# if __name__ == '__main__':
#     import uvicorn
#     # Popen(['python', '-m', 'https_redirect'])
#     uvicorn.run(app, host="localhost", port=8081)  # 192.168.31.30
