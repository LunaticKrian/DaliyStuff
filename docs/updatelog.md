# 仓库更新日志

PS：更新记录以日期倒排更新

## 2026年07月28日

### 新增：移动端客户端 GUILD DECK（Tauri 2 · iOS/Android · 全模块）

把 PixelPack 从「Web + 桌面」扩展到**移动端原生 App**，复用 `web/` Vue 前端，瘦客户端经 HTTPS 直连线上 API（服务端零改动）。技术方案见 [`260728-移动端客户端技术方案.md`](technology/260728-移动端客户端技术方案.md)，设计稿见 `design/260728-mobile-app/`（16 屏可交互原型）。

**选型**：**Tauri 2 mobile**（与桌面端同栈，Rust 壳 + 系统 WebView），覆盖 **iOS + Android**；UI **全新移动端设计**（非响应式套壳）；**完整对齐 Web**。签名设计「**公会掌机 GUILD DECK**」：CRT 开机仪式 + 设备状态条链路 LED（与桌面同源）+ 方向键式 Tab Dock（中央凸起智核徽记）。字体跟随现网系统字体。

**前端基座**（`web/src/`）
- `utils/platform.ts`：新增 `isMobile/isIOS/isAndroid`（UA 判定，无新依赖）+ `setMobileOverride`
- `layouts/MobileLayout.vue`：掌机外壳（开机幕 + 状态条 + viewport + Tab Dock）+ 应用锁挂载
- `styles/mobile.css`：移动端设计系统（`m-*` 前缀，复用 `--pixel-*` token）
- `App.vue` / `router/index.ts`：按 `isMobile()` 选布局 + 分流到 `views/mobile/*`，`meta.tab` 控制 Dock；新增 `/me`（我的）
- `composables/useAppLock.ts` + `components/mobile/LockScreen.vue`：**PIN 应用锁**（SHA-256 存储，启动/回前台落锁），生物识别走 Tauri 命令

**移动视图层**（`web/src/views/mobile/`，19 个，全部复用 api/stores/composables/types）
- 鉴权流：Setup（首屏接驳）/ Login / Register / CharacterCreation
- P0：Dashboard · Items（**成本视角：每件日均成本 + 总消耗 + 使用天数 + 附加成本**）/ ItemDetail / ItemForm / Quests / Chat（智核 SSE 流式）/ Profile / Settings（账户/应用锁/设备会话/登出）
- P1：WorldMap（信号台+情报+航海日志）/ Stats（日均榜+分类）/ BlogList·Detail·Editor / Resume（预览+打印PDF）/ Transfer（WebRTC 移植）

**移动外壳**（`application/mobile/`，对齐 `application/desktop/` 结构）
- `src-tauri/`：`Cargo.toml`（tauri2 + store/os/notification）、`tauri.conf.json`（frontendDist→web/dist、CSP）、`lib.rs`/`commands.rs`（令牌 set/get/del_secret + 生物识别占位）、capabilities、README（含工具链/构建/生物识别接入步骤）

**验证与偏离**：前端 `npm run build`(vue-tsc) **通过**；Rust 外壳待工具链编译（本机无 Rust/iOS/Android，同桌面端）。偏离见技术方案 §9——履历史 AI 编辑暂缓（仅预览+打印PDF）、生物识别占位（PIN 已全可用）、令牌用 store 而非 Keychain/Keystore（生产强化路径已记）。

## 2026年07月27日

### 新增：鉴权会话化（refresh 轮换 + 会话级复用检测 + 设备会话管理）
把无状态 JWT 升级为**可吊销的有状态会话**，配合桌面端把 refresh 长期存于钥匙串的收紧时机。技术方案见 [`260727-鉴权会话化与应用锁.md`](technology/260727-鉴权会话化与应用锁.md)。

- **背景问题**：旧实现 `/auth/refresh` 签新 refresh 但旧 refresh 永不失效 → 7 天内签发的每个 refresh 都长期有效且可续期；`/auth/logout` 是空壳不作废任何令牌；令牌只含 `sub`，无 jti/会话，无法吊销单会话，改密码也不失效。被窃 refresh = ≥7 天可续期的持久沦陷。
- **服务端（Phase 1）**（`server/app/`）
  - 新增 `refresh_sessions` 会话表（`models/session.py`：sid/jti/family_id/吊销标记/滑动续期时间）+ `services/session.py`
  - **refresh 轮换 + 会话级复用检测**：旧 refresh 重放即吊销该会话族（family），但**不连坐其他设备**
  - access/refresh 增加 sid/jti/iat claims；`get_current_user` 校验会话存活 → 登出/吊销对 access token **立即生效**
  - `/logout` 真实吊销；`/password` 改密踢其他设备；新增 `GET/DELETE /sessions` 设备管理
  - 引入 pytest + 会话化端到端测试（5 passed）
- **前端（Phase 2）**（`web/src/`）
  - 统一 refresh worker（`utils/refresh.ts`），收敛 client/sse/auth 三路 refresh（否则复用检测误伤正常多标签 / HTTP+SSE 并发）
  - 修复 401 重试结果被丢弃（`api/client.ts` 包装层正确回传调用方）
  - 跨标签 token 同步（storage 事件）；登出连服务端吊销
  - 修 `BlogEditor` 绕过 tokenStore 的历史 bug（桌面端上传可用）
  - Settings 页加「设备会话」管理卡片

### 新增：官网落地页设计稿
`design/260727-pixelpack-landing/`（`index.html` / `main.js` / `styles.css`）—— PixelPack 产品落地页静态原型。

### 新增：开源许可证 + README 重写（含中文版）
- 新增 `LICENSE` 开源许可证
- 重写 `README.md`（中文）+ 新增 `docs/readme/README.zh-CN.md`，对齐当前「Web + 桌面端」产品形态与部署架构

## 2026年07月26日

### 新增：冒险者履历 DOSSIER（简历管理 + AI 对话编辑）
新增个人简历模块，把简历以「公会登记档案」形式管理，支持 **AI 对话编辑**（变更**人工确认后才落库**）。技术方案见 [`260726-简历管理与AI编辑.md`](technology/260726-简历管理与AI编辑.md)，设计稿见 `design/260726-resume/`（基础管理 + AI 三栏对话）与 `design/260726-resume-templates/`（模板原型）。

- **设计**：左侧表单 CRUD + 右侧 A4 简历纸实时预览（像素/RPG 外壳 + 内嵌专业衬线简历纸，可导出 PDF）；AI 编辑以对话为主 + 字段内联润色
- **后端**（`server/app/`，复用 intel/task_agent 的 GLM + `claude-agent-sdk` 模式）
  - `models/resume.py`：`Resume` / `ResumeVersion`（版本快照）/ `PendingChange`（待确认变更）/ 对话表
  - `services/resume.py`：简历 CRUD + 版本化 + Undo（每次接受变更生成新版本，可回滚到任意历史快照）
  - `services/resume_agent.py`：AI **只读工具按需取**（`get_resume`/`get_section`，不把整份简历常驻 system prompt）；写工具**不直接落库**，而是在数据副本上校验 + 算 diff（非法即返回 error 让模型重试）→ 写 `PendingChange(pending)` → 即时经 SSE 推送，用户点「接受」才回放 args 并生成新版本
  - `routers/resume.py`：简历 CRUD + 对话线程 + SSE 流式 + 接受/拒绝/回滚端点
- **Web 实现**（`web/src/`）
  - `views/Resume.vue`：表单 + A4 实时预览 + AI 对话（流式打字机 + pending 变更卡 + 接受/拒绝）+ 版本/Undo
  - 多模板 `components/resume-templates/`（Pixel / Pro / Academic / Minimal 四套 + `shared.ts` 公共 + `useResumeI18n`）
  - `utils/exportPdf.ts`：基于 html2pdf 的 A4 PDF 导出（含字体子集处理）
  - `api/resume.ts` / `types/resume.ts`；`utils/sse.ts` 新增 `streamResumeChat`

### 新增：桌面端原生客户端（Tauri 2 瘦客户端）
把 Web 站点扩展为**桌面原生 App**，复用 `web/` Vue 前端，经 HTTPS 直连线上 FastAPI（**服务端零改动**，CORS 已 `*`）。技术方案见 [`260726-桌面端客户端技术方案.md`](technology/260726-桌面端客户端技术方案.md)，设计稿见 `design/260726-desktop-app/`，代码见 `application/desktop/`。

- **选型**：**Tauri 2**（Rust 外壳 + 系统 WebView），为未来移动端（iOS/Android）留路；非 Electron
- **`application/desktop/src-tauri/`**：`tauri.conf.json`（frontendDist → `web/dist`、CSP、托盘、bundle）、`lib.rs`（插件装配 + 系统托盘 + 全局快捷键 + 命令注册）、`commands.rs`（OS Keychain 钥匙串 set/get/del_secret，存 refresh token）
- **`web/` 平台层改造**：新增 `utils/platform.ts`（平台探测）、`views/desktop/Setup.vue`（首屏服务器配置）、`views/desktop/DesktopSettings.vue`；`api/client.ts`/`auth`/`sse`/`router` 适配桌面端（token 走 keyring）；`npm run build`(vue-tsc) 通过
- **能力**：系统托盘 + 常驻 + 全局快捷键 + 开机自启、原生系统通知、本地文件集成；在线为主 + 轻量只读缓存（不本地写入、不双向同步）
- **v1 偏离/暂缓**：标题栏用系统装饰（自定义像素标题栏留待下版）；只读离线缓存、拖拽上传/批量导入、自动更新与签名分发为 P1/P2。Rust 侧未经本机 `cargo` 验证（环境未装 Rust），见 `application/desktop/README.md`

### 重构：字体体系切回系统字体（移除像素字体）
移除 Ark Pixel / Press Start 2P / VT323 三款像素字体，全站字体栈改为系统字体，并清理多语言字体资源。

- **改动**：`web/public/fonts/` 删除 `ark-pixel-16px-proportional-*`（7 个语言变体 woff2）+ `OFL.txt`；`index.html` Google Fonts 去掉 `Press Start 2P` / `VT323`；`styles/fonts.css` 的 `--font-pixel` / `--font-pixel-en` / `--font-pixel-num` 改为系统字体栈与等宽栈
- **连带**：约 30 个 `.vue`/`.css` 文件跟随字体变量收敛；`utils/exportPdf.ts` 适配新字体栈的 PDF 导出

## 2026年07月19日

### 部署：/uploads 改由 web 容器直发，网关瘦身成纯路由器

把 `/uploads` 从「网关挂载宿主路径直发」改为「web 容器直发」，消除跨 compose 的路径漂移。

- **根因**：网关（`airise-gateway` 独立 compose）直发 `/uploads` 时，硬编码宿主绝对路径 `/opt/pixelpack/data/uploads`；而 api（PixelPack compose）用相对 `./data`。两个 compose 各自解析，换部署目录即漂移，线上踩过图片 404（PixelPack 实际跑在 `/root/pixel-pack`）。
- **改法**：`/uploads` 交给 `pixelpack-web` 容器直发 —— `web/nginx.conf` 加 `location /uploads/ { alias /app/data/uploads/; }`，web 容器挂 `./data/uploads:ro`。api 写、web 读**同属一个 compose、同用 `./data`** → 宿主绝对路径必然一致，**零漂移**。
- **网关瘦身**：站点 conf 去掉 `location /uploads/`（随 `location /` 转发给 web）；网关 compose 移除 uploads 挂载，**只挂 conf/snippets/证书**，不挂任何项目路径。网关彻底成为纯路由器（`/api`→api、其余→web，只认容器名）。
- **约束不变**：web 容器仍是纯静态叶子（SPA + `/uploads` 直发），不碰 `/api`、WS（那些由网关单层直连 api）。`/uploads` 经 web 但纯静态，不涉 WS/SSE 参数，不违反约束。
- **文档同步**：deploy.md、nginx部署架构.md（§3 目标架构/交付方式、§6 落地、§9 清单、§10 历史变更）、新服务上线与网关扩展.md、README、airise-gateway README 全部更新。
- 详见 [`technology/260719-nginx部署架构.md`](technology/260719-nginx部署架构.md) §3「交付方式 B」、§10「历史变更」。

### 部署：前端容器化（多阶段构建）+ 网关拆分独立仓库

把前端从「宿主机 `npm run build` → 产物挂载进网关直发」改为 **Docker 多阶段构建**，并把网关从本仓库 `nginx/` 拆分为独立项目 `airise-gateway`。

- **前端容器**（`web/`）
  - 新增 `web/Dockerfile`：两阶段 `node:24-alpine`（`npm ci` + `vue-tsc` + `vite build`）→ `nginx:alpine` serve `dist`。
  - 新增 `web/nginx.conf`（镜像自带）：SPA history 回退 + gzip + `/assets` 长缓存。
  - 新增 `web/.dockerignore`。
  - 根 `docker-compose.yml` 新增 `web` 服务（`pixelpack-web`），接入 `airise-web`，不暴露端口；生产环境不再依赖宿主机 node。
- **网关拆分**（`airise-gateway` 独立仓库）
  - `PixelPack/nginx/` 整体迁出为独立项目 `airise-gateway`，本仓库不再保留。
  - 站点 conf（`pixelpack` / `model.airise.site`）：`location /` 由 `root` 直发改为 `proxy_pass http://pixelpack-web`；`/api`、`/uploads`、WS 仍由网关单层处理不变。
  - 网关 compose 移除 `/opt/pixelpack/web/dist` 挂载（SPA 改由 web 容器提供），保留 uploads / 证书挂载。
- **架构定调**：前端 web 容器是**纯静态叶子**（只 `try_files` + gzip + 缓存），不碰 `/api`、`/uploads`、WS —— 与初版「内层 nginx 啥都管」的双重 nginx 踩坑结构有本质区别。详见 [`technology/260719-nginx部署架构.md`](technology/260719-nginx部署架构.md) §3「前端 SPA 的两种交付方式」、§10「历史变更」。
- **文档同步**：README、`docs/deployment/deploy.md`、`bootstrap-deploy.sh` / `deploy-dns.sh`（`GW_DIR` 改 `/opt/airise-gateway`、前端改容器构建）、`260719-nginx部署架构.md`、`260719-新服务上线与网关扩展.md`、`260719-通配证书签发.md` 全部更新为现行部署。

### 部署：网关托管模式上线 + 部署链路打通

把 PixelPack 从「内层 nginx + 外层网关」双层结构，切换为统一的 **airise-gateway 网关托管模式**（架构见 [`technology/260719-nginx部署架构.md`](technology/260719-nginx部署架构.md)）。完整部署流程见 [`deploy.md`](deploy.md)；新项目接入见 [`technology/260719-新服务上线与网关扩展.md`](technology/260719-新服务上线与网关扩展.md)。本次上线修掉三个阻塞部署的线上问题：

- **claude 子进程 root 下拒绝启动**：`server/Dockerfile` 新增 `ENV IS_SANDBOX=1`（claude 官方沙箱旁路开关），容器以任意用户运行都能兜底 `bypassPermissions` 的 root 校验。
- **网关无限重启 `host not found in upstream "<project>-api"`**：模板文件 `nginx/conf.d/_template.conf`（含字面占位符）被构建期烤进镜像被 nginx 加载。`nginx/.dockerignore` 增加排除项，模板不再进镜像。
- **SQLite 启动报 `attempt to write a readonly database`**：宿主机 `./data` 属主非 1000。部署前 `chown -R 1000:1000 data`（部署文档 §3）。

## 2026年07月12日

### 重构：每日任务系统 V1.0（手动自定义 + AI 自然语言生成）

把原本「硬编码 `QUEST_DEFS` + 每日随机抽样」的固定任务系统，重构为「手动自定义 + AI 对话生成 + 等级经验联动 + 任务核心成就」的可成长任务系统。技术方案见 `docs/technology/060712-每日任务系统.md`，设计稿见 `design/260712-dailytask/`。

**设计稿**（`design/260712-dailytask/`，静态原型 + 交互演示）
- 委托大厅（任务页）：分类瓷砖 + 难度星 + 完成印章 + 浮动经验；侧栏等级/打卡/成就格
- NEXA 任务内核（对话页）：未来科技设定，CSS 绘制内核头像 + 命令行输入 + 任务即时插入卡
- 拉丁/数字用 Chakra Petch（清爽），中文回退像素字体；图标用单色几何 dingbat（移除彩色 emoji）

**后端核心**（`server/app/`）
- `models/task.py`：新增 `Task` 表（title/description/category/source/target/progress/completed/exp_reward/due_date/recurrence…），每日清单 = `due_date == today`
- `models/user.py` + `utils/migrate.py` + `main.py`：`User` 加 `exp` 独立列，启动时 `ensure_column` 幂等迁移（`create_all` 不 ALTER 已存表）
- `services/task.py`：任务 CRUD + `complete_task`（加经验→写日志→判成就→升级日志）+ 撤销 + 多步进度
- `services/quest.py`：重写为**任务核心 12 成就**（初试身手 / 坚持十连 / 半百里程 / 百炼成钢 / 三日不辍 / 一周不缺 / 月度勤勉 / 完美一天 / 学者 / 智者辅佐 / 自律工匠 / 百日征途）+ exp 等级（`exp // 50 + 1`）+ 连续打卡计算
- `routers/tasks.py`：`/api/tasks` 全套（list/create/patch/delete/complete/uncomplete/progress）
- 移除物品增删改的旧任务埋点（`routers/items.py`），物品不再驱动任务系统

**AI 对话生成**（复用 intel 的 `claude-agent-sdk` + GLM 模式）
- `models/chat.py`：`ChatSession` / `ChatMessage`（对话入库）
- `services/task_agent.py`：per-request MCP 工具工厂（`list_today_tasks` 查重 + `create_task` **function call 直接写库**）+ `run_agent()` 流式生成器
- `services/chat.py`：会话/消息持久化、首条消息自动生成标题
- `routers/chat.py`：会话 CRUD + `POST /messages` **SSE 流式**（事件 `start/delta/tool/task_created/done/end`），per-session `asyncio.Lock` 防并发，独立 session 落库助手消息规避 `get_db` 流式关闭陷阱
- 实测：GLM 6 轮 ~26s，`list_today_tasks` → 4× `create_task`（source=ai）→ 总结，事件流 + 任务入库 + 消息持久化全通

**Web 实现**
- `views/Quests.vue` 重写为「委托大厅」任务页：今日清单 + 完成印章 + 新增/编辑/删除 + 多步进度 + 侧栏（等级经验条/连续打卡/今日进度/成就格），沿用 `--pixel-*` / `.pixel-border` / Press Start 2P 数字 / `var(--font-pixel)` 中文
- `views/Chat.vue` 新增 NEXA 对话页：会话侧栏 + 消息流 + 流式打字机（闪烁光标）+ `task_created` 即时插入卡 + `tool` 状态行，文本色统一白色
- `utils/sse.ts`：带 JWT 的 SSE 客户端（`fetch` + `ReadableStream` + 401 自动刷新，替代不能带头的 `EventSource`）
- `api/tasks.ts` / `api/chat.ts` / `types/task.ts` / `types/chat.ts` 新增；`api/quests.ts` / `types/quest.ts` 改为新 summary 结构
- 顶部导航新增「委托大厅」「AI 对话」入口；路由 `/quests` `/chat`

### 修复：经验不持久化 + 成就死代码（任务系统重构附带）
- 经验原本存 `User.settings` JSON 的 `quest_exp`/`daily_completed`，该 JSON 列未用 `MutableDict`，SQLAlchemy 检测不到原地修改 → 实测 `users.settings` 全空、经验从未真正写入。改为 `User.exp` 独立列持久化（验证：完成任务后 `user.exp` 正确累加）
- `WARRANTY_WATCHER` 成就在 `check_achievements` 无判定条件 → 永不解锁；随成就体系整体重设计移除

## 2026年07月11日

### 新增：世界地图模块（AI 技术情报每日推送与历史查看）

顶部导航「角色信息」右侧新增「❖ 世界地图」入口，用于 AI 技术文章的每日推送与历史回溯。

**设计稿**（`design/world-map/`，静态原型）
- 像素 RPG 风格静态页面：信号台（每日推送）+ 像素世界地图 + 航海日志（历史）
- 文件：`world-map.html` / `styles.css` / `main.js`

**Web 实现**（纯前端 + Mock，后端待接入）
- 路由 `/world-map`（`web/src/router/index.ts`）+ 顶部导航项（`web/src/layouts/MainLayout.vue`）
- `web/src/types/intel.ts`：六大知识疆域常量（大模型 / 智能体 / 视觉 / 基建 / 研究 / 工具）与类型定义
- `web/src/api/intel.ts`：Mock 数据层（`listTodayIntel` / `listArchive` / `getIntelStats`），返回 Promise 便于后续替换为真实 API
- `web/src/views/WorldMap.vue`：信号台（ON AIR 广播 + 打字机 + 统计卡 + 今日情报卡）+ 航海日志（按月分组 + 疆域筛选 + 未读徽标）+ 阅读模态

**迭代**
- 经反馈移除「像素世界地图」版块（其筛选功能与日志 chips 重复、占空间过大），未读计数合并进航海日志的筛选 chips，信息零丢失

### 接入：Claude Agent SDK（经 GLM 代理）驱动真实情报抓取
世界地图从 Mock 切换为真实后端。Agent 走 GLM 的 Anthropic 兼容端点（`open.bigmodel.cn/api/anthropic`），不依赖官方 Anthropic Key。

**后端**（`server/app/`）
- `services/intel_agent.py`：用 `claude-agent-sdk` 的 `query()` + `output_format`（JSON Schema 结构化输出）驱动 Agent；内置进程内 MCP 工具 `search_ai_news`（RSS 聚合，feedparser+httpx）与 `fetch_page`（html2text 抓全文），规避 GLM 不支持的 WebSearch/WebFetch
- `services/intel.py`：`generate_intel_now`（`asyncio.Lock` 防并发）/ `scheduled_generate_intel` / `store_daily_intel` / `list_today` / `list_archive`（一天一页）/ `get_stats`
- `routers/intel.py`：`GET /today` `GET /archive` `GET /stats` `POST /generate`（手动触发，`overwrite` 参数）
- APScheduler 定时任务（`INTEL_CRON_HOUR/MINUTE`）每日自动抓取；GLM 配置写入 `server/.env`（已 gitignore），`intel_agent` 启动时把 Settings 注入 `os.environ` 供子进程继承
- 技术方案文档：`docs/technology/260711-ClaudeCode接入.md`

**Web 对接**
- `api/intel.ts` / `types/intel.ts` 由 Mock 切真实接口；`generateIntel` 超时 300s（Agent 含 RSS 抓取实测约 2–3 分钟）

### 迭代：航海日志分页与侦测交互
- **一天一分页**：`ArchivePageResponse` 改为日维度（`date / page / totalPages / dates`），按 `DISTINCT` 日期定位，疆域筛选自动跳过空天；pager 改为日导航（「第 X / Y 天」+ 前/后一天日期标注）
- **侦测控制台**（主动发起检索）：信号台底部新增雷达扫描动画 + 「发起侦测」按钮，点击触发 `POST /generate` 并循环状态文案 + 计时，成功后刷新今日情报与统计
- **翻页抖动修复**：翻页/切疆域改用保留旧内容 + 半透明蒙层（不再整块塌陷为 spinner），pager.y 采样波动 0px
- **渲染闪烁修复**：`stagger-list` 入场动画只在首次加载播一次，翻页不再重播
- **日期日历**：分页器日期选择改用项目像素日历组件 `PixelDatePicker`（新增 `dropUp` 向上展开 / `markedDates` 标记有情报日 / `restrictToMarked` 置灰空日三个可选 prop，默认关闭不影响其余调用），有情报日点哪跳哪、空日不可选
- **移除空页占位**：删掉「该疆域暂无历史记录」空状态块
- 路由调整为 `/260711-world-map`

