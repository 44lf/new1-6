DB_URL='mysql://root:123456@127.0.0.1:3306/project1?charset=utf8mb4'

TORTOISE_ORM = {
    "connections": {
        # 这里直接引用上面的变量
        "default": DB_URL
    },
    "apps": {
        "models": {
            # 告诉它去哪里找你写的 class Resume...
            # 如果你的 models.py 和 settings.py 在同一级目录，这就写 ["models"]
            "models": [
                    "app.db.resume_table",
                    "app.db.prompt_table", 
                    "app.db.candidate_table"
                    ],
            "default_connection": "default",
        }
    },
}