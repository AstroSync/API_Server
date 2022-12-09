import random
import time

from fastapi import APIRouter

# from api_server.hardware.naku_device_api import NAKU
from api_server.models.api import RotatorModel
from api_server import celery_client
# from api_server.models.api import RotatorModel


router = APIRouter(prefix="/rotator", tags=["Rotator"])


# @router.post("/set_config")
# async def rotator_config(rotator_model: RotatorModel):
#     RotatorDriver().set_config(rotator_model.dict())
#     return {"message": "OK"}


@router.post("/set_angle")
async def set_angle(az: float, el: float):
    # RotatorDriver().set_angle(az, el)
    celery_client.set_angle(az, el)
    return {"message": 'OK'}


@router.post("/set_random_angle")
async def set_random_angle():
    az, el = random.uniform(0, 180), random.uniform(-90, 90)
    # RotatorDriver().set_angle(az, el)
    celery_client.set_angle(az, el)
    return {"az": f'{az:.2f}', 'el': f'{el:.2f}'}


# @router.post("/set_speed")
# async def set_speed(az_speed: float, el_speed: float):
#     RotatorDriver().set_speed(az_speed, el_speed)
#     return {"message": 'OK'}


@router.get("/")
async def get_position():
    position: tuple[float, float] = celery_client.get_position()  # type: ignore
    print(position)
    return {"az": position[0], "el": position[1]}


# @router.get("/condition")
# async def get_condition():
#     return RotatorDriver().rotator_model.__dict__


# @router.get("/update_condition")
# async def update_condition():
#     RotatorDriver().queue_request_condition()
#     time.sleep(1.5)
#     return RotatorDriver().rotator_model.__dict__

