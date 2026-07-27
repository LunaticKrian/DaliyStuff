# PixelPack

> 🌐 Languages: **English** | [简体中文](docs/readme/README.zh-CN.md)

A pixel-art, RPG-styled personal-item tracker and daily-life dashboard. Manage your belongings, spending, and tasks in a gamified way.

![img.png](docs/asstes/img.png)

## Features

- **Desktop client** — native macOS shell (Tauri 2 thin client): first-run server setup, persistent login via Keychain, tray + global shortcut, device-session management (prebuilt builds in Releases; dev/build in the *Desktop client* section below)
- **Item management** — record item info (price, source, warranty, tags); auto daily-averaged cost
- **Character system** — upload portrait, set name/class, record birthday & star sign
- **Daily quests** — auto-generated daily tasks (add item, log spending, …); complete them for EXP
- **Achievements** — collection achievements (first add, master collector, …); unlocked ones are written to the adventure log
- **Adventure log** — auto-recorded system events + manual entries, RPG-style timeline
- **World map** — daily AI tech-intel feed with history, organized by six domains (LLMs / agents / vision / infra / research / tools) (frontend + mock; backend pending)
- **Stats** — spending trends, item-status breakdown, warranty reminders, and other charts
- **Pixel UI** — NES.css-based pixel-art theme, Press Start 2P / Ark Pixel fonts

## Tech stack

| Layer | Tech |
|---|------|
| Frontend | Vue 3.5 + TypeScript + Pinia 3 + Vue Router 4 + Vite 8 |
| Backend | FastAPI + SQLAlchemy 2.0 (async) + SQLite (aiosqlite) |
| Desktop | Tauri 2 + Rust (thin client, reuses `web/`, tokens in OS Keychain) |
| Auth | JWT + session-based (refresh rotation / reuse detection / device sessions) |
| Charts | ECharts 6 |
| Styling | NES.css + custom pixel components |

## Project structure

```
PixelPack/
├── server/                # Python backend
│   ├── app/
│   │   ├── main.py        # FastAPI entry, router registration, static files
│   │   ├── config.py      # config (DB, secret, upload dir)
│   │   ├── database.py    # SQLAlchemy async engine + Session
│   │   ├── models/        # ORM models (User, Item, Journal, Quest, ...)
│   │   ├── schemas/       # Pydantic request/response models
│   │   ├── services/      # business logic
│   │   ├── routers/       # API routes (REST endpoints)
│   │   └── utils/         # JWT, password hashing, DI
│   └── requirements.txt
├── web/                   # Vue frontend
│   ├── src/
│   │   ├── api/           # ofetch API wrappers
│   │   ├── components/    # reusable components (PixelDatePicker, ...)
│   │   ├── layouts/       # layouts (AuthLayout, MainLayout)
│   │   ├── router/        # routes + navigation guards
│   │   ├── stores/        # Pinia stores (auth, notification)
│   │   ├── styles/        # global styles (pixel theme, animations, fonts)
│   │   ├── types/         # TypeScript types
│   │   ├── utils/         # helpers (format, export, calc, platform abstraction, refresh worker)
│   │   └── views/         # pages (Dashboard, ItemList, Quests, ...) + desktop/ (Setup, ...)
│   └── package.json
├── application/desktop/   # Tauri 2 shell (src-tauri/ Rust + reuses web/)
└── uploads/               # user-uploaded images (gitignored)
```

## Quick start

### Prerequisites

- Python 3.10+
- Node.js 24+ (aligned with `node:24-alpine` in `web/Dockerfile`)
- npm 10+

### Backend

Create the virtualenv at the **project root** (one repo for both ends; Python is backend-only):

```bash
# at project root
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r server/requirements.txt
```

Start the dev server (⚠️ must run inside `server/`, since `DATABASE_URL` and `UPLOAD_DIR` are relative paths):

```bash
cd server
uvicorn app.main:app --reload --port 8000 --log-config app/uvicorn_log_config.json
```

Then visit `http://127.0.0.1:8000/docs` for the API docs.

### Frontend

```bash
cd web
npm install
npm run dev
```

The frontend dev server runs at `http://localhost:3000` and proxies `/api` and `/uploads` to the backend at `http://127.0.0.1:8000`.

Backend tests (auth sessions, etc.):

```bash
cd server && pytest -q
```

### Desktop client (macOS · Tauri 2)

The desktop app is a **thin client**: it reuses the `web/` frontend, talks to the backend over HTTPS, and stores tokens in the system keychain. **Zero server-side changes.**

- **Prebuilt builds**: see **Releases** (first macOS release `v1.0.0`, Apple Silicon).
- **Local dev / build from source**: see [`application/desktop/README.md`](application/desktop/README.md).

```bash
cd application/desktop
npm install                 # installs @tauri-apps/cli (needs Rust toolchain + Xcode CLT)
npm run dev                 # tauri dev: first-run server setup → sign in
npm run build               # tauri build → produces .dmg / .app
```

Design doc: [docs/technology/260726-桌面端客户端技术方案.md](docs/technology/260726-桌面端客户端技术方案.md).

### Production build (containerized)

The frontend is built via a Docker multi-stage build (`web/Dockerfile`: `node` build → `nginx` static serve). **No need to run `npm run build` on the host in production** — `docker compose up -d --build web` does it. For local dev, use `npm run dev` as above.

## Docker deployment (recommended for production)

`docker-compose.yml` brings up two containers — `api` (FastAPI/uvicorn) and `web` (multi-stage nginx static) — both on the shared `airise-web` network. External traffic is handled by the standalone `airise-gateway`, which terminates TLS and reverse-proxies.

```bash
git clone https://github.com/LunaticKrian/PixelPack.git
cd PixelPack

# 1. Configure secrets (never in git, never in the image — injected at runtime)
cp server/.env.example server/.env
vi server/.env          # fill in ANTHROPIC_AUTH_TOKEN

# 2. Build and start api + web (build on the server — see notes below)
docker compose up -d --build
```

Common commands:

```bash
docker compose ps            # status (api, web)
docker compose logs -f api   # backend logs
git pull && docker compose up -d --build   # update code (./data is preserved)
```

**Deployment topology**

```
Browser ──https──▶ airise-gateway (standalone project, owns 80/443, pure router)
                       ├─ /api/       ──▶ pixelpack-api:8000   (this compose)
                       └─ /, /uploads/ ──▶ pixelpack-web:80    (this compose, SPA + uploads served directly)

┌─ docker-compose (this project) ───────────────────────────┐
│  web (nginx:alpine)         ← multi-stage: node build→nginx │
│   ├─ serve SPA (fallback + gzip + cache)                    │
│   └─ serve /uploads (mount ./data/uploads:ro)               │
│  api (uvicorn) :8000                                        │
│   └─ FastAPI + APScheduler (writes ./data/uploads)          │
│                                                              │
│  volumes:  ./data → /app/data (api)                         │
│            ./data/uploads → /app/data/uploads:ro (web)      │
│            ├─ data.db                                        │
│            └─ uploads/   (api writes, web reads, same compose) │
│  networks: airise-web (external, talks to the gateway)      │
└──────────────────────────────────────────────────────────────┘
```

**Notes**

- **Persistence**: `data.db` and `uploads/` all live under `./data` (bind mount); rebuilding/upgrading containers won't lose data — back up with `tar czf backup.tar.gz data/`.
- **Secrets**: `.env` is injected via compose `env_file`; images are safe to push to public registries.
- **Gateway**: `airise-gateway` is a **separate project/repo** (not under this one) — a **pure router**: TLS + `/api`→api + everything else→web, **mounts no project host path**. Uploaded files are served directly by the `web` container (`api` writes, `web` reads the same `./data`; zero path drift). See the airise-gateway repo README for its config.
- **⚠️ Bundled-binary platform consistency**: `claude-agent-sdk` ships a glibc native binary (~240MB), so the backend image **cannot use alpine**, and the **build platform must match the runtime platform**. Building on Apple Silicon for an amd64 server requires `docker buildx build --platform linux/amd64`; the safest option is still `docker compose build` directly on the server.

Full steps, secret-safety discussion, HTTPS/domain extension, and troubleshooting are in **[docs/deployment/deploy.md](docs/deployment/deploy.md)**.

## Docs

| Doc | Contents |
|------|------|
| [docs/technology/260726-桌面端客户端技术方案.md](docs/technology/260726-桌面端客户端技术方案.md) | Desktop Tauri 2 thin client: architecture, platform-abstraction layer, CSP/CORS, packaging/distribution, mobile roadmap |
| [docs/technology/260727-鉴权会话化与应用锁.md](docs/technology/260727-鉴权会话化与应用锁.md) | Refresh rotation + reuse detection + device sessions + desktop app lock (PIN/Touch ID) — design & implementation |
| [docs/deployment/deploy.md](docs/deployment/deploy.md) | Full deployment: web container build → backend deploy → gateway update, with verification, daily updates, backup, troubleshooting |
| [docs/technology/260719-nginx部署架构.md](docs/technology/260719-nginx部署架构.md) | Gateway-hosting architecture (unified entry, shared network, wildcard cert, multi-project onboarding) |
| [docs/technology/260719-新服务上线与网关扩展.md](docs/technology/260719-新服务上线与网关扩展.md) | New-project onboarding SOP: backend container joins `airise-web`, site config from `_template.example`, gateway extension |
| [docs/technology/260719-通配证书签发.md](docs/technology/260719-通配证书签发.md) | `*.airise.site` wildcard cert DNS-01 issuance, auto-renew hook, single-domain→wildcard migration, troubleshooting |
| [docs/updatelog.md](docs/updatelog.md) | Repo changelog |
| airise-gateway repo README | Gateway container (`airise-gateway`, standalone project) docs |

## API overview

| Prefix | Description |
|----------|------|
| `/api/auth` | register, login, token refresh (rotation), password change, profile update |
| `/api/auth/sessions` | device-session list, remote sign-out of a specific device |
| `/api/items` | item CRUD, image upload, status change, CSV export |
| `/api/categories` | category management |
| `/api/tags` | tag management |
| `/api/journals` | adventure log (auto + manual) |
| `/api/quests` | daily-quest progress, achievements |
| `/api/stats` | overview, recent items, warranty alerts |

All authenticated endpoints use the `Authorization: Bearer <token>` header.

## Configuration

Backend config via env vars or `server/.env`:

```env
DATABASE_URL=sqlite+aiosqlite:///./data.db
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
UPLOAD_DIR=uploads
```

## License

MIT
