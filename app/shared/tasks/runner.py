"""Celery 同步任务中的异步运行辅助。"""

import asyncio
import sys
from collections.abc import Coroutine
from typing import Any


def run_async[T](coroutine: Coroutine[Any, Any, T]) -> T:
    """为单个 Celery 任务运行异步领域逻辑。"""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    return asyncio.run(coroutine)
