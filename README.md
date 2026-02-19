# Dino AWDP Platform (MVP)

一个用于 CTF AWDP 赛事的后端平台 MVP，支持：

- 注册 / 登录（JWT）
- 创建队伍 / 加入队伍
- 按题目动态分发容器（模拟）
- Flag 校验与计分
- 用户上传修复包并校验是否成功修复漏洞（模拟评测）
- 排行榜

> 说明：当前版本重点是**可运行的后端骨架 + 核心业务流程**。容器分发和修复包校验为可替换的抽象实现，后续可以接入真实 Docker/K8s 和 CI 沙箱。

## 快速启动

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

访问：
- 前端首页: `http://127.0.0.1:8000/`
- OpenAPI: `http://127.0.0.1:8000/docs`

## 运行测试

```bash
pytest -q
```

## 核心接口

- `POST /auth/register`
- `POST /auth/login`
- `POST /teams`
- `POST /teams/{invite_code}/join`
- `GET /challenges`
- `POST /containers/allocate`
- `POST /flags/submit`
- `POST /patches/submit`
- `GET /leaderboard`

## 目录结构

```
app/
  core/        # 配置与安全
  models.py    # SQLAlchemy 模型
  schemas.py   # Pydantic DTO
  services.py  # 业务规则
  deps.py      # 鉴权依赖
  main.py      # FastAPI 路由
tests/
```


## 前端页面

当前已内置一个单页前端（`app/static/index.html`），可直接调用后端接口完成：

- 注册 / 登录（自动保存 JWT）
- 创建队伍 / 通过邀请码加入队伍
- 查询题目并分配动态容器
- 提交 Flag
- 提交 Patch
- 查看排行榜
