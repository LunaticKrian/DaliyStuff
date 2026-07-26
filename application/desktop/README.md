# PixelPack 桌面端 (Desktop · Tauri 2)

桌面端**瘦客户端**：复用仓库根的 `web/` Vue 前端，经 HTTPS 直连线上 FastAPI 服务端。**服务端零改动**（CORS 已 `*`）。

> 技术方案见 `docs/technology/260726-桌面端客户端技术方案.md`，设计稿见 `design/260726-desktop-app/`。

## 目录结构

```
application/desktop/
├── package.json              # tauri cli 脚本（dev/build/icon）
└── src-tauri/
    ├── Cargo.toml            # Rust 依赖（tauri 2 + 插件 + keyring）
    ├── build.rs
    ├── tauri.conf.json       # frontendDist → ../../../web/dist；CSP；托盘；bundle
    ├── capabilities/default.json
    ├── icons/                # 应用图标（PNG；生产 icns/ico 用 tauri icon 生成）
    └── src/
        ├── main.rs           # 入口
        ├── lib.rs            # 插件装配 + 托盘 + 全局快捷键 + 命令注册
        └── commands.rs       # OS Keychain 钥匙串命令（set/get/del_secret）
```

## 前置依赖

1. **Rust 工具链**（本机暂未安装，需先装）：
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```
2. **系统依赖**：
   - macOS：Xcode Command Line Tools `xcode-select --install`
   - Windows：[WebView2](https://developer.microsoft.com/microsoft-edge/webview2/) + MSVC Build Tools
   - Linux：`webkit2gtk-4.1`、`libayatana-appindicator3-dev` 等（见 Tauri 官方前置清单）
3. **本目录依赖**（Tauri CLI）：
   ```bash
   cd application/desktop
   npm install        # 装 @tauri-apps/cli
   ```
4. `web/` 依赖与构建：仓库根 `web/` 已 `npm install`。

## 运行（开发）

```bash
cd application/desktop
npm run dev          # = tauri dev
```

- `tauri dev` 会先执行 `beforeDevCommand`（`npm --prefix ../../web run dev`）拉起 Vite，再启动 Rust 外壳加载 `http://localhost:3000`。
- 首次编译 Rust 依赖较慢（数分钟），之后增量很快。
- 首屏会让你**配置服务器地址**（输入线上 `https://...` origin → 测试接驳 → 登录）。地址存于 `tauri-plugin-store` 的 `app.json`；令牌存于 **OS Keychain**。

> 路径假设 `tauri` 在 `application/desktop/` 下执行。`tauri.conf.json` 中 `frontendDist` 相对 `src-tauri`（3 层 `..`），`beforeDevCommand` 相对当前目录（2 层 `..`）。

## 生产打包

```bash
cd application/desktop
npm run build       # = tauri build（先 web build 出 dist，再产出原生安装包）
```

- macOS 产出 `.app` / `.dmg`；Windows `.msi`/`.exe`；Linux `.AppImage`/`.deb`。
- **签名/公证**：分发前需 macOS Developer ID + 公证，Windows 代码签名；详见技术方案 §6.4、§8。
- **完整图标**：生产 bundle 的 `.icns`/`.ico` 由 `npm run icon`（= `tauri icon src-tauri/icons/icon.png`）一键生成全平台图标集，覆盖到 `icons/`。

## 故障排查

| 现象 | 原因 / 处理 |
|---|---|
| Rust 编译报某插件闭包/解析签名不符 | Tauri 2 小版本 API 微差；按编译器提示调整 `src/lib.rs`（全局快捷键 `register` 的闭包签名、`register(accelerator, …)` 的字符串解析是最可能的点）。 |
| 运行时 `permission missing: notification:allow-notify` 等 | 在 `capabilities/default.json` 的 `permissions` 里加对应 `allow-*` 权限。 |
| 接驳失败 / 请求被 CSP 拦 | 确认服务器 origin 是 `https://`；`tauri.conf.json` 的 `csp` 已放开 `connect-src https: wss:` 与 `img-src https:`，如仍被拦按报错放开对应指令。 |
| Linux 令牌存不进 Keychain | Linux 需 Secret Service（gnome-keyring/kwallet）；无则 `keyring` 会失败，首屏重新登录即可（内存缓存仍可用）。 |
| `/uploads` 图片不显示 | 由前端 `client.ts` 的响应归一化自动补全为绝对地址；若仍相对，确认服务器返回的是 `/uploads/...`。 |

## 与 Web 端的关系

- 前端单代码库：桌面端**不 fork** `web/`，仅在 `web/` 内以 `isTauri()`（`web/src/utils/platform.ts`）门控桌面分支。纯浏览器访问行为不变。
- 桌面专属页：`web/src/views/desktop/Setup.vue`（首屏接驳）、`DesktopSettings.vue`（系统调谐）。
- 原生能力抽象：`web/src/utils/native.ts`（Web 端 no-op）。

## v1 范围与后续

**已实现**：服务端可配 + uploads 归一化 + 钥匙串令牌 + 401 路由跳转 + 首屏接驳 + 托盘 + 全局快捷键 + 开机自启 + 系统通知抽象 + 桌面设置页。

**后续阶段**（见技术方案 §11）：自定义像素标题栏（签名视觉，设计稿已就绪）、只读离线缓存、拖拽上传/批量导入/本地导出、自动更新与签名分发。
