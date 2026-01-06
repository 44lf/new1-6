from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from app.settings import TORTOISE_ORM


# 1. 创建 FastAPI APP
app = FastAPI(title="简历智能解析系统")

# 2. 注册数据库
# 这一步非常关键，它把 Tortoise 和 FastAPI 绑在一起了
register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,  # 【重要】这句话的意思是：如果表不存在，就自动帮我建表！
    add_exception_handlers=True,
)

# 3. 写个简单的测试接口，看看服务能不能通
@app.get("/")
def read_root():
    return {"message": "服务已启动，数据库连接正常！"}

# 注意：以后我们的路由（Router）会加在这里