"""管理接口路由：robots 集合 CRUD。

鉴权：所有接口要求 Authorization: Bearer <ADMIN_TOKEN>。
appSecret：入库自动 Fernet 加密；对外视图不返回密钥字段。
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pymongo import ReturnDocument

from app.core.admin_auth import require_admin
from app.core.crypto import encrypt_secret
from app.core.deps import get_db
from app.models.robot import (
    RobotCreateReq,
    RobotDoc,
    RobotPublic,
    RobotUpdateReq,
)

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


def _to_public(doc: dict) -> RobotPublic:
    """从 mongo doc 投影到对外安全视图，剥离敏感字段。"""
    return RobotPublic(**{k: doc.get(k) for k in RobotPublic.model_fields.keys()})


@router.post("/robots", response_model=RobotPublic)
async def create_robot(req: RobotCreateReq, db=Depends(get_db)):
    """创建机器人：robot_code 唯一；appSecret 加密落库。"""
    if await db.robots.find_one({"robot_code": req.robot_code}):
        raise HTTPException(409, "robot_code already exists")
    doc = RobotDoc(
        robot_code=req.robot_code,
        robotId=req.robotId,
        name=req.name,
        appSecret_encrypted=encrypt_secret(req.appSecret),
        description=req.description,
    ).model_dump()
    await db.robots.insert_one(doc)
    return _to_public(doc)


@router.get("/robots", response_model=list[RobotPublic])
async def list_robots(db=Depends(get_db)):
    """列出全部机器人（不含密文字段）。"""
    cursor = db.robots.find({}, {"appSecret_encrypted": 0})
    return [_to_public(doc) async for doc in cursor]


@router.get("/robots/{robot_code}", response_model=RobotPublic)
async def get_robot(robot_code: str, db=Depends(get_db)):
    """按 robot_code 查询单个机器人。"""
    doc = await db.robots.find_one({"robot_code": robot_code})
    if not doc:
        raise HTTPException(404, "robot not found")
    return _to_public(doc)


@router.put("/robots/{robot_code}", response_model=RobotPublic)
async def update_robot(robot_code: str, req: RobotUpdateReq, db=Depends(get_db)):
    """局部更新机器人字段；提供 appSecret 时重新加密。"""
    update = {"updated_at": datetime.now(timezone.utc)}
    for field in ("name", "robotId", "status", "description", "sid", "company_name"):
        v = getattr(req, field)
        if v is not None:
            update[field] = v
    if req.appSecret is not None:
        update["appSecret_encrypted"] = encrypt_secret(req.appSecret)
    res = await db.robots.find_one_and_update(
        {"robot_code": robot_code},
        {"$set": update},
        return_document=ReturnDocument.AFTER,
    )
    if not res:
        raise HTTPException(404, "robot not found")
    return _to_public(res)


@router.delete("/robots/{robot_code}")
async def delete_robot(robot_code: str, db=Depends(get_db)):
    """按 robot_code 删除机器人。"""
    res = await db.robots.delete_one({"robot_code": robot_code})
    if res.deleted_count == 0:
        raise HTTPException(404, "robot not found")
    return {"deleted": True}
