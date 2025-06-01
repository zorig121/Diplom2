# app/api/v1/routes/containers.py

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId
from datetime import datetime
import docker
import uuid

from app.core.config import config
from app.core.security import get_current_user_from_cookie
from app.db.mongodb import get_db

router = APIRouter(prefix="/containers", tags=["containers"])
client = docker.from_env()


class ContainerConfig(BaseModel):
    image: Optional[str] = Field(
        None, description="Docker image нэр (жишээ нь `jupyter/datascience-notebook`)."
    )
    cpu: float = Field(..., gt=0, description="Хуваарилах CPU-ийн хэмжээ (жишээ нь 0.5 = 50%).")
    ram: float = Field(..., gt=0, description="Хуваарилах RAM хэмжээ (GB).")
    timeout_minutes: Optional[int] = Field(
        None, description="Контейнерийн автомат зогсолтгүй хоцрох хугацаа (минут)."
    )

    class Config:
        schema_extra = {
            "example": {
                "image": "jupyter/datascience-notebook",
                "cpu": 0.5,
                "ram": 4.0,
                "timeout_minutes": 60,
            }
        }


@router.post("/launch", status_code=status.HTTP_201_CREATED)
async def launch_container(
    config_data: ContainerConfig,
    current_user=Depends(get_current_user_from_cookie),
    db=Depends(get_db),
):
    """
    Шинээр Docker контейнер үүсгэх. JupyterLab тохиргоо болон токен-ыг тохируулна.
    """
    user_id = str(current_user["_id"])
    container_name = f"jupyter-{user_id}-{uuid.uuid4().hex[:8]}"

    chosen_image = config_data.image or config.JUPYTER_IMAGE
    # Автомат зогсолтын хугацаа хэрвээ заагаагүй бол default-т авна
    timeout = config_data.timeout_minutes or config.ACCESS_TOKEN_EXPIRE_MINUTES

    try:
        container = client.containers.run(
            image=chosen_image,
            name=container_name,
            detach=True,
            mem_limit=f"{int(config_data.ram * 1024)}m",        # GB→MB
            cpu_period=100000,
            cpu_quota=int(config_data.cpu * 100000),
            ports={"8888/tcp": None},  # Динамик порт сонгоно
            environment={"JUPYTER_TOKEN": uuid.uuid4().hex},
            labels={
                "owner_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "timeout_minutes": str(timeout),
            },
        )
    except docker.errors.ImageNotFound:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Тухайн Docker image олдсонгүй. Та image-гээ шалгана уу.",
        )
    except docker.errors.APIError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Контейнер үүсгэхэд Docker API алдаа гарлаа: {e.explanation}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Контейнер үүсгэхэд алдаа гарлаа: {str(e)}",
        )

    # MongoDB-д контейнер мэдээллийг хадгалах
    container_doc = {
        "user_id": user_id,
        "container_id": container.id,
        "name": container_name,
        "image": chosen_image,
        "created_at": datetime.utcnow(),
        "status": "running",
        "timeout_minutes": timeout,
    }
    await db["containers"].insert_one(container_doc)

    # "8888/tcp" портын холболтын мэдээллийг авах
    container.reload()
    ports_info = container.attrs["NetworkSettings"]["Ports"].get("8888/tcp")
    host_port = ports_info[0]["HostPort"] if ports_info else None

    if not host_port:
        # Хэрвээ порт олдохгүй бол контейнерийг устгаж, алдаа буцаана
        container.remove(force=True)
        await db["containers"].update_one(
            {"container_id": container.id},
            {"$set": {"status": "error", "error": "No port assigned"}},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Контейнер портыг динамикаар авсангүй.",
        )

    jupyter_url = f"http://{config.GPU_HOST}:{host_port}/?token={container.attrs['Config']['Env'][0].split('=')[1]}"

    return {
        "container_name": container_name,
        "container_id": container.id,
        "host_port": host_port,
        "jupyter_url": jupyter_url,
        "message": "Контейнер амжилттай үүсгэгдлээ.",
    }


@router.get("/status/{container_id}")
async def container_status(
    container_id: str, current_user=Depends(get_current_user_from_cookie)
):
    """
    Өгөгдсөн container_id-тай Docker контейнерийн статусыг буцаана.
    """
    try:
        container = client.containers.get(container_id)
        status_str = container.status
    except docker.errors.NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Контейнер олдсонгүй."
        )
    except docker.errors.APIError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Docker API алдаа гарлаа: {e.explanation}",
        )

    return {"container_id": container_id, "status": status_str}


@router.post("/stop/{container_id}")
async def stop_container(
    container_id: str,
    current_user=Depends(get_current_user_from_cookie),
    db=Depends(get_db),
):
    """
    Өгөгдсөн container_id-тай Docker контейнерийг зогсоож, MongoDB-д статус шинэчилнэ.
    """
    try:
        container = client.containers.get(container_id)
        container.stop()
    except docker.errors.NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Контейнер олдсонгүй."
        )
    except docker.errors.APIError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Docker API алдаа гарлаа: {e.explanation}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Контейнер зогсоох үед алдаа гарлаа: {str(e)}",
        )

    # MongoDB-д статусыг 'stopped' болгон шинэчлэх
    await db["containers"].update_one(
        {"container_id": container_id}, {"$set": {"status": "stopped"}}
    )

    return {"message": "Контейнер амжилттай зогсоолоо."}
