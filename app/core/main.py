import sys


from contextlib import asynccontextmanager
from pathlib import Path

if not __package__:
    # 直接运行文件时，从项目根目录导入，避免本目录的 logging.py 遮蔽标准库。
    # FastAPI 等第三方库也会导入 logging，必须放在这段路径调整之后。
    sys.path[0] = str(Path(__file__).resolve().parents[2])

import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.infra.checkpointer import (
    close_checkpointer,
    init_checkpointer,
)

from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.core.logging import configure_logging
from app.agents.insurance_advisor import init_insurance_agent
from app.modules.chat.router import router as chat_router
from app.modules.chat_thread.router import router as chat_thread_router
from app.modules.product.router import router as product_router
configure_logging(settings.logging.logging_level)

logger = logging.getLogger(__name__)

#初始化生命周期钩子
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"【{settings.app.app_name}】应用启动中...")

    from app.infra.database import check_database, close_database

    try:
        # 1.检查业务数据库连接
        await check_database()
        # 2.初始化Checkpointer
        checkpointer = await init_checkpointer()

        # 3.初始化保险顾问Agent
        app.state.agent = init_insurance_agent(checkpointer)

        yield
    finally:
        logger.info("应用关闭中... ")
        # 3.关闭Checkpointer连接池
        await close_checkpointer()
        # 4.关闭SQLAlchemy连接池
        await close_database()


#初始化fastapi
app = FastAPI(
    title=settings.app.app_name,
    description="服务端-Agent",
    version="1.0.0",
    debug=settings.app.app_debug,
    lifespan=lifespan,
)



# 统一处理异常信息，发现是ChatThreadNotFoundError，返回对应的错误状态码和错误信息
@app.exception_handler(ApplicationError)
async def handle_application_error(
    request: Request,
    exc: ApplicationError, # 捕获到的异常（这里用自定义异常基类捕获，所有业务异常都会匹配到）
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code, # 异常中自带status
        content={
            "code": exc.code,        # 异常中自带code
            "message": exc.message,  # 异常中自带message
        },
    )


# 创建 app 后注册路由


app.include_router(chat_router)
app.include_router(chat_thread_router)
app.include_router(product_router)

#测试接口，检测健康
@app.get("/health",summary="健康检查", description="检查服务是否正常运行")
async def health_check():
    logger.info("健康检查接口被调用")
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "app.core.main:app",
        host=settings.app.app_host,
        port=settings.app.app_port,
        reload=False,
        loop= "asyncio:SelectorEventLoop" if sys.platform == "win32" else "auto",
    )
