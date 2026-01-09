from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from app.settings import TORTOISE_ORM

# 1. 引入路由
from app.routers.resume import router as resume_router
from app.routers.prompt import router as prompt_router

# 2. 创建 APP
app = FastAPI(title="简历智能解析系统")

# 3. 注册路由
app.include_router(resume_router)
app.include_router(prompt_router)

# 4. 注册数据库
register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,
    add_exception_handlers=True,
)

@app.get("/")
def read_root():
    return {"message": "服务已启动，请访问 /docs 查看接口文档"}
