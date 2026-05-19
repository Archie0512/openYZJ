"""Handler 抽象基类，定义同步/异步两种调度形态的统一接口。"""
from __future__ import annotations

from abc import ABC, abstractmethod

from fastapi import BackgroundTasks

from app.models.yunzhijia import YunzhijiaPayload, YunzhijiaResponseData


class BaseHandler(ABC):
    """命令处理器基类。

    - name：handler 标识，用于日志 / command_logs.handler 字段
    - is_async：True 表示主流程立即返回占位、真实计算放到 BackgroundTask
    """

    name: str = "base"
    is_async: bool = False

    @abstractmethod
    async def handle(
        self,
        payload: YunzhijiaPayload,
        sessionId: str,
        bg: BackgroundTasks,
    ) -> YunzhijiaResponseData:
        """同步路径：返回 3 秒内必须给出的响应数据。

        异步 handler 也必须立即返回一个占位响应；耗时计算请通过 bg.add_task 注册。
        """
        ...
