from contextlib import asynccontextmanager
from fastapi import FastAPI
from tortoise.contrib.fastapi import RegisterTortoise
from app.settings import TORTOISE_ORM
from app.utils.minio_client import MinioClient  # 新增

# 1. 引入路由
from app.routers.resume import router as resume_router
from app.routers.prompt import router as prompt_router


# 2. 使用 lifespan 上下文管理器（现代方式）
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化 MinIO（修复 Bug 2）
    await MinioClient.init_bucket()
    print("MinIO 桶已初始化")

    # 初始化数据库
    async with RegisterTortoise(
        app=app,
        config=TORTOISE_ORM,
        generate_schemas=True,
        add_exception_handlers=True,
    ):
        print("数据库连接已建立")
        yield
        print("数据库连接已关闭")


# 3. 创建 APP（使用 lifespan）
app = FastAPI(
    title="简历智能解析系统",
    description="提供简历上传解析、手动录入、筛选查询及提示词管理等能力。",
    lifespan=lifespan,
)

# 4. 注册路由
app.include_router(resume_router)
app.include_router(prompt_router)


@app.get("/")
def read_root():
    return {"message": "服务已启动，请访问 /docs 查看接口文档"}