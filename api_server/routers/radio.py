from __future__ import annotations
from api_server import celery_client
from fastapi import APIRouter
from api_server.models.db import LoRaConfig, FSK_Config

router = APIRouter(prefix="/radio", tags=["Radio"])


@router.post("/set_config")
async def radio_config(config: LoRaConfig | FSK_Config):
    #gs_device.radio.set_config(radio_config)
    return {"message": "OK"}


@router.post("/send_msg")
async def send_msg(msg: list[int] | bytes):
    celery_client.radio_send(msg)
    return {"message": "OK"}


# @router.get("/dump_registers")
# async def dump_registers():
#     return gs_device.radio.dump_memory()
