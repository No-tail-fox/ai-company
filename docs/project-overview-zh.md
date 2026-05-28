# 新商机 AI 工作台项目说明文档

## 1. 项目概述

本项目是一个面向 AI 工具、内容资源、会员权益和运营管理的 Web 应用。前台提供门户首页、AI 工作台、图像/视频/音频/对话工具、课程资源、社区交流、会员权益等用户入口；后台提供用户、积分、会员、兑换码、内容、课程、模型渠道和审计日志管理。

系统采用前后端分离架构：

- 前端：Vue 3 单页应用，负责门户页面、工作台和管理后台交互。
- 后端：FastAPI 应用，负责 REST API、鉴权、业务服务、数据库读写、文件存储和第三方模型渠道调用。
- 数据：默认使用 SQLite，适合本地演示和轻量部署；Docker 部署中使用持久化卷保存数据库和文件。
- 异步任务：Docker 部署时可启用 Redis + Celery，用于生成任务和飞书课程同步。

## 2. 技术选型

### 前端

| 类型 | 选型 | 说明 |
|---|---|---|
| 框架 | Vue 3 | 使用组合式 API 构建页面和复杂交互 |
| 构建工具 | Vite 6 | 本地开发启动快，支持开发代理和生产构建 |
| 语言 | TypeScript | 约束 API 数据结构、页面模型和表单 payload |
| 路由 | vue-router 4 | 管理门户页、详情页、工作台和后台路由 |
| 图标 | lucide-vue-next | 提供后台导航、按钮和卡片图标 |
| 测试 | Vitest | 覆盖前端模型转换、API payload 和页面逻辑 |

主要前端目录：

```text
frontend/
  src/
    App.vue                 # 应用壳，区分前台 PortalChrome 和后台 AdminView
    router.ts               # SPA 路由
    styles.css              # 全局样式
    components/             # 门户页、工作台、详情页、会员页等
    views/                  # 后台视图、认证视图、门户视图
    services/               # API 封装、数据 normalizer、后台表单 payload
  tests/                    # Vitest 测试
  vite.config.ts            # Vite 配置，含 /api 代理
```

### 后端

| 类型 | 选型 | 说明 |
|---|---|---|
| Web 框架 | FastAPI | 提供类型化 REST API、依赖注入和自动文档能力 |
| 数据校验 | Pydantic 2 | 定义请求 DTO 和响应 payload |
| ORM | SQLAlchemy 2 | 管理用户、内容、任务、会员、钱包等数据模型 |
| 数据库 | SQLite | 默认本地数据库，路径为 `backend/data/app.db` |
| 鉴权 | PyJWT | 登录后签发 Bearer Token，后台接口按角色校验 |
| HTTP 客户端 | httpx | 用于调用外部模型/渠道服务 |
| 异步任务 | Celery + Redis | Docker 模式下处理生成任务和飞书同步 |
| 文件上传 | python-multipart + StaticFiles | 上传图片/音频并通过 `/storage` 访问 |

主要后端目录：

```text
backend/
  app/
    main.py                 # FastAPI 应用、路由和依赖
    settings.py             # 环境变量配置
    db.py                   # SQLAlchemy engine/session/init_db
    models.py               # 数据表模型
    schemas.py              # 请求和响应模型
    seed.py                 # 演示数据初始化
    services/               # 业务服务层
    tasks/                  # Celery 任务
  tests/                    # Pytest 后端测试
```

### 部署

| 类型 | 选型 | 说明 |
|---|---|---|
| 容器编排 | Docker Compose | 一键启动前端、后端、worker、Redis |
| 前端生产服务 | Nginx | 托管 Vue 构建产物，并反向代理 `/api` 和 `/storage` |
| 后端容器 | Python 3.12 slim | 运行 FastAPI + Uvicorn |
| 前端构建容器 | Node 20 | 执行 `npm ci` 和 Vite build |

## 3. 如何启动

### 3.1 本地开发启动

本地开发建议分别启动后端和前端。默认后端地址是 `http://127.0.0.1:8000`，前端默认端口是 `5173`。如果端口被占用，可以换成 `5174`。

#### 启动后端

```powershell
cd "G:\360MoveData\Users\foxnotail\Documents\New project\backend"
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

后端健康检查：

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/v1/health
```

正常返回：

```json
{"status":"ok"}
```

#### 启动前端

```powershell
cd "G:\360MoveData\Users\foxnotail\Documents\New project\frontend"
npm install
npm run dev -- --port 5174
```

访问地址：

- 前台首页：`http://127.0.0.1:5174/home`
- AI 工作台：`http://127.0.0.1:5174/workbench`
- 管理后台：`http://127.0.0.1:5174/admin`

#### 本地代理说明

`frontend/vite.config.ts` 会把前端的 `/api` 请求代理到后端：

```ts
const apiProxyTarget = process.env.VITE_API_PROXY_TARGET ?? 'http://127.0.0.1:8000';
```

如果后端不是 `8000` 端口，可在启动前端前设置：

```powershell
$env:VITE_API_PROXY_TARGET = "http://127.0.0.1:8001"
npm run dev -- --port 5174
```

### 3.2 Docker 启动

Docker 模式会启动四个服务：

- `frontend`：Nginx + Vue 静态资源
- `backend`：FastAPI
- `worker`：Celery worker
- `redis`：任务队列和结果存储

启动命令：

```powershell
cd "G:\360MoveData\Users\foxnotail\Documents\New project"
Copy-Item .env.example .env
docker compose up -d --build
```

默认访问：

- 应用地址：`http://127.0.0.1/`
- 健康检查：`http://127.0.0.1/api/v1/health`

如果本机 `80` 端口被占用，修改 `.env`：

```env
PUBLIC_HTTP_PORT=8080
```

然后访问 `http://127.0.0.1:8080/`。

### 3.3 演示账号

应用启动时会执行 `ensure_demo_data` 初始化演示数据。

| 类型 | 手机号 | 密码 |
|---|---|---|
| 普通用户 | `13800000000` | `user123456` |
| 运营管理员 | `13900000000` | `admin123456` |

验证码接口的默认开发验证码是 `123456`。

## 4. 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `APP_NAME` | 新商机 | FastAPI 应用名称 |
| `API_PREFIX` | `/api/v1` | 后端 API 前缀 |
| `DATABASE_URL` | `sqlite:///backend/data/app.db` | 数据库连接地址 |
| `JWT_SECRET` | `change-me-before-production` | JWT 签名密钥，生产必须更换 |
| `CELERY_ENABLED` | 本地默认 `false`，Docker 默认 `true` | 是否启用 Celery 队列 |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Celery broker |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/1` | Celery result backend |
| `STORAGE_DIR` | `backend/storage` | 上传文件和生成结果存储目录 |
| `FEISHU_APP_ID` | 空 | 飞书同步配置 |
| `FEISHU_APP_SECRET` | 空 | 飞书同步配置 |
| `FEISHU_WIKI_SPACE_ID` | 空 | 飞书知识库空间 |
| `FEISHU_WIKI_ROOT_NODE_TOKEN` | 空 | 飞书根节点 |
| `PUBLIC_HTTP_PORT` | `80` | Docker 前端暴露端口 |

## 5. 前端设计

### 5.1 应用入口和页面壳

前端入口是 `frontend/src/main.ts`，创建 Vue 应用并挂载路由。`App.vue` 根据当前路由决定使用哪种页面壳：

- `/admin`：直接渲染后台管理视图。
- 其他前台路由：渲染 `PortalChrome`，提供顶部导航、搜索、账号区和通用门户框架。

### 5.2 路由设计

核心路由定义在 `frontend/src/router.ts`：

| 路由 | 页面 | 说明 |
|---|---|---|
| `/home` | `PortalView` | 首页/门户页 |
| `/workbench` | `WorkbenchPage` | AI 工作台总入口 |
| `/workbench/image` | `ImagePage` | 图像生成 |
| `/workbench/video` | `VideoPage` | 视频生成 |
| `/workbench/audio` | `AudioPage` | 音频任务 |
| `/learning` | `CourseLibraryPage` | 课程库 |
| `/membership/benefits` | `MembershipBenefitsPage` | 会员权益 |
| `/admin` | `AdminView` | 管理后台 |
| `/:pageKey` | `PortalView` | 动态门户频道页 |
| `/:detailPath(.*)*` | `PortalDetailPage` | 内容详情页 |

详情页同时支持 `/workspace`、`/community`、`/templates`、`/resources`、`/projects`、`/toolkit`、`/learning` 等路径前缀。

### 5.3 数据访问层

前端的数据访问集中在 `frontend/src/services`：

- `api.ts`：封装所有后端请求、Token 保存、用户会话、后台管理 API。
- `viewModel.ts`：把后端字段转换为前端视图模型，提供 fallback 数据。
- `adminForms.ts`：把后台表单转换为后端 payload。
- `communicationHall.ts`：社区交流大厅数据模型。
- `adminInteractions.ts`：后台拖拽排序、预览缩放等交互工具。
- `icons.ts`：图标映射。

请求层统一追加 `X-Tenant-ID: demo`。后台接口会读取 `opc_admin_token`；用户侧接口会读取 `opc_user_session`。

### 5.4 后台管理前端

`AdminView.vue` 是后台主界面，按模块组织：

- 概览：用户、会员、积分、内容、模型资源等统计。
- 人员管理：新增、编辑、禁用用户。
- 会员管理：会员计划、用户会员开通记录。
- 积分管理：钱包流水、人工调账。
- 兑换码管理：批量生成兑换码，赠送积分或会员权益。
- 内容管理：首页轮播、频道页、模块、卡片、详情内容和实时预览。
- 课程管理：飞书课程导入后的列表、状态清洗和详情打开。
- 模型中心：供应商渠道、模型配置、工具绑定、工作台能力绑定。
- 审计日志：后台操作记录查询。

## 6. 后端设计

### 6.1 应用结构

`backend/app/main.py` 负责创建 FastAPI 应用、注册中间件、初始化数据库和声明 API 路由。启动生命周期中会调用：

1. `init_db()`：创建数据库表，并对 SQLite 做轻量 schema 补齐。
2. `ensure_demo_data()`：写入演示用户、钱包、门户内容、会员计划、模型渠道和工具绑定。

后端通过 `CORSMiddleware` 放开跨域，方便本地前端调试。上传和生成文件通过 `/storage` 静态挂载访问。

### 6.2 分层设计

后端采用简单清晰的三层结构：

```text
API 路由层 main.py
  -> Pydantic schemas.py 校验请求
  -> services/ 处理业务规则
  -> SQLAlchemy models.py 读写数据库
```

服务层按领域拆分，避免把业务逻辑堆在路由中。典型服务包括：

- `auth.py`：密码哈希、登录、注册、JWT。
- `account.py`：账号资料。
- `wallet.py`：积分余额、冻结、流水。
- `memberships.py`：会员计划和用户会员。
- `redemptions.py`：兑换码批次和兑换。
- `payments.py`：充值订单。
- `portal.py`：门户配置、页面、详情、搜索、用户动作。
- `admin_content.py`：后台内容页、模块、卡片管理。
- `home_dashboard.py`：首页仪表盘和轮播。
- `image.py` / `video.py` / `audio.py` / `chat.py`：AI 工作台能力。
- `model_configs.py`：模型渠道、模型配置、工具绑定。
- `workbench_capabilities.py`：工作台能力开关和绑定。
- `channel_router.py`：外部模型渠道分发。
- `generation.py`：生成任务、积分预估、任务状态。
- `feishu_import.py`：飞书课程和知识库导入。
- `uploads.py`：图片/音频上传。
- `admin_management.py`：后台用户、统计、审计。

### 6.3 数据模型

主要数据库模型定义在 `backend/app/models.py`：

| 模型 | 说明 |
|---|---|
| `Tenant` | 租户 |
| `User` | 用户和后台管理员 |
| `Wallet` / `WalletTransaction` / `WalletReservation` | 积分钱包、流水和冻结 |
| `PaymentOrder` | 充值订单 |
| `MembershipPlan` / `UserMembership` | 会员计划和用户会员 |
| `RedemptionBatch` / `RedemptionCode` | 兑换码批次和兑换码 |
| `ContentPage` / `ContentSection` / `ContentItem` | 门户页面、模块和卡片 |
| `PortalDetailDocument` / `PortalDetailVersion` / `PortalDetailComment` | 详情页正文、版本和评论 |
| `HomeHeroSlide` | 首页轮播 |
| `AiAssistant` / `PromptTemplate` | 助理和提示词模板 |
| `ApiChannel` / `ModelConfig` / `ToolModelBinding` / `ChannelRoute` | 模型供应商、模型配置、工具绑定和路由 |
| `GenerationTask` / `Asset` | 生成任务和资源 |
| `ChatSession` / `ChatMessage` | 对话会话和消息 |
| `FeishuSyncRun` / `FeishuSyncNode` | 飞书同步运行记录 |
| `UserPortalAction` | 用户收藏、下载等动作 |
| `AdminActionLog` | 后台审计日志 |

### 6.4 鉴权和权限

用户登录后，后端返回 JWT access token。需要登录的接口读取 `Authorization: Bearer <token>`。

后台接口使用 `require_admin` 校验管理员身份，并通过 `require_admin_role` 判断最低角色要求，例如：

- `READ_ONLY`：查看后台数据。
- `CONTENT_EDITOR`：编辑内容、课程、首页等。
- `OPERATOR`：模型配置、渠道和工具绑定。

### 6.5 异步任务设计

Celery 应用定义在 `backend/app/celery_app.py`，包含两个任务模块：

- `app.tasks.generation`：处理图像、视频、音频等生成任务。
- `app.tasks.feishu_import`：处理飞书知识库同步。

生成任务流程：

```text
前端提交生成请求
  -> 后端根据 target_type / target_id 找模型绑定
  -> 预估积分并创建 GenerationTask
  -> Celery worker 调用 ChannelRouter
  -> HttpChannelTransport 请求外部模型渠道
  -> 更新任务状态、结果 URL 和积分流水
```

Docker 部署时 `CELERY_ENABLED=true`，任务会进入 Redis 队列。轻量本地开发时默认不启用 Celery，适合调试页面和普通 API。

## 7. 主要 API 模块

所有接口默认前缀为 `/api/v1`。

| 模块 | 代表接口 | 说明 |
|---|---|---|
| 健康检查 | `GET /health` | 服务状态 |
| 门户配置 | `GET /portal/config`、`GET /portal/pages/{page_key}` | 前台频道和页面配置 |
| 门户详情 | `GET/PATCH /portal/details/{detail_path}` | 内容详情、版本、评论 |
| 首页 | `GET /home/dashboard` | 首页仪表盘和推荐 |
| 用户认证 | `POST /auth/register`、`POST /auth/login` | 注册、登录、验证码、密码 |
| 账号 | `GET /account/summary`、`PATCH /account/profile` | 账号资料和积分摘要 |
| 会员 | `GET /memberships/status` | 用户会员状态 |
| 支付/兑换 | `POST /payments/recharge-orders`、`POST /redemptions/redeem` | 充值订单和兑换码 |
| 图像 | `GET /image/workbench`、`POST /image/generations` | 图像工作台和生成 |
| 视频 | `GET /video/workbench`、`POST /video/generations` | 视频工作台和生成 |
| 音频 | `POST /audio/uploads`、`POST /audio/tasks`、`GET /audio/tasks` | 音频上传和任务 |
| 对话 | `GET /chat/workbench`、`POST /chat/sessions`、`POST /chat/sessions/{id}/messages` | 对话工作台 |
| 社区 | `GET/POST /communication/posts` | 交流大厅 |
| 课程 | `GET /courses`、`GET /admin/courses` | 课程列表和管理 |
| 后台用户 | `GET/POST /admin/users` | 用户管理 |
| 后台会员 | `/admin/membership-plans`、`/admin/user-memberships` | 会员管理 |
| 后台积分 | `/admin/wallet-transactions`、`/admin/wallets/{user_id}/adjust` | 钱包流水和调账 |
| 后台兑换码 | `/admin/redemption-batches`、`/admin/redemption-codes` | 批次和兑换码 |
| 后台内容 | `/admin/pages`、`/admin/sections`、`/admin/items`、`/admin/home-slides` | 页面、模块、卡片和首页 |
| 模型中心 | `/admin/provider-channels`、`/admin/model-configs`、`/admin/tool-model-bindings` | 渠道、模型、工具绑定 |
| 工作台能力 | `/workbench/capabilities`、`/admin/workbench-capabilities` | 工作台功能配置 |
| 文件上传 | `/admin/uploads`、`/audio/uploads` | 图片和音频上传 |
| 飞书导入 | `/admin/imports/feishu/wiki/sync`、`/admin/imports/feishu/browser/snapshot` | 飞书知识库/浏览器快照导入 |

## 8. 功能模块说明

### 8.1 门户和内容中心

门户页面由后台配置驱动，包括页面、模块和卡片三层：

```text
ContentPage
  -> ContentSection
    -> ContentItem
```

前端根据 `layout` 渲染不同布局，例如工具网格、课程列表、音频表格、横幅、排行榜等。内容详情支持正文、亮点、步骤、交付物、FAQ、下载链接、版本发布和回滚。

### 8.2 AI 工作台

工作台包含：

- 总入口：展示图像、视频、音频、对话等能力。
- 图像生成：提交 prompt，创建图像任务。
- 视频生成：提交 prompt，创建视频任务。
- 音频任务：支持音频上传、配音/转写等任务入口。
- 对话工作台：会话创建、消息发送、导出。

工作台能力可在后台绑定到具体模型配置，并设置积分覆盖价和启停状态。

### 8.3 模型中心

模型中心用于把前台工具和外部 AI 服务解耦：

- 供应商渠道：配置 base URL、API Key、适配器类型、超时、优先级、鉴权 JSON 和配置 TOML。
- 模型配置：配置模型 Key、能力类型、供应商模型名、默认积分、上下文窗口和计费元数据。
- 工具绑定：将页面卡片、工作台能力、助手或模板绑定到模型配置。
- 工作台能力绑定：控制图像、视频、音频、对话等能力是否启用，以及使用哪个模型。

### 8.4 用户、积分和会员

用户体系包含普通用户和管理员。每个用户可拥有钱包、会员记录和门户动作记录。

积分相关能力：

- 查询账户摘要。
- 后台人工调账。
- 充值订单。
- 生成任务预估和扣费。
- 兑换码赠送积分。

会员相关能力：

- 后台配置会员计划。
- 给用户开通会员。
- 兑换码赠送会员天数。
- 内容和课程可配置会员访问要求。

### 8.5 兑换码

后台可创建兑换码批次，设置：

- 批次数量。
- 赠送积分。
- 关联会员计划。
- 赠送会员天数。
- 过期时间。

用户在前台兑换后，系统会写入积分或会员权益，并记录兑换状态。

### 8.6 课程和飞书导入

课程模块支持：

- 用户侧课程库浏览。
- 后台课程列表、搜索、分类筛选。
- 课程内容格式清洗。
- 飞书 Wiki 同步。
- 浏览器快照导入 Markdown 内容和资源映射。

Docker 模式下飞书同步可以进入 Celery worker；本地轻量模式可按接口同步执行。

### 8.7 社区交流

社区模块提供帖子列表和发帖能力。帖子可关联到详情页路径，复用门户详情页能力进行展示。

### 8.8 上传和存储

后端提供图片和音频上传接口。上传文件保存到 `STORAGE_DIR`，并通过 `/storage` 暴露给前端。Docker 部署时该目录挂载到 `ai-company-backend-storage` 持久化卷。

### 8.9 审计和后台操作

后台会记录关键管理操作，便于排查内容、用户、会员、积分和模型配置变更。

## 9. 运行验证

### 前端

```powershell
cd "G:\360MoveData\Users\foxnotail\Documents\New project\frontend"
npm test
npm run build
```

### 后端

```powershell
cd "G:\360MoveData\Users\foxnotail\Documents\New project\backend"
pytest
```

### 手工检查

1. 打开 `http://127.0.0.1:5174/home`，确认门户首页可访问。
2. 打开 `http://127.0.0.1:5174/admin`，使用管理员账号登录。
3. 在后台切换“内容管理”“模型中心”“兑换码管理”等模块。
4. 调用 `http://127.0.0.1:8000/api/v1/health`，确认后端返回 `{"status":"ok"}`。

## 10. 二次开发建议

- 新增 API 时，优先在 `schemas.py` 定义请求模型，再在对应 `services/` 文件实现业务逻辑，最后在 `main.py` 暴露路由。
- 新增前台页面时，先在 `router.ts` 增加路由，再在 `components/` 或 `views/` 中实现页面。
- 新增后台表单时，把 payload 转换逻辑放到 `services/adminForms.ts`，避免组件内堆积字段转换。
- 涉及后端返回字段变更时，同时更新 `viewModel.ts` 的 normalizer 和相关测试。
- 涉及生成能力时，优先通过模型中心配置 `ApiChannel`、`ModelConfig` 和 `ToolModelBinding`，减少硬编码。
- 生产部署前必须更换 `JWT_SECRET`，并确认外部模型 API Key 不出现在前端代码或公开日志中。
