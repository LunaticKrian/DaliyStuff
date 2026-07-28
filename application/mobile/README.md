# PixelPack 移动端 (Mobile · Tauri 2 · iOS/Android)

移动端**瘦客户端**：复用仓库根的 `web/` Vue 前端（移动视图层 `web/src/views/mobile/*` + `MobileLayout.vue`），经 HTTPS 直连线上 FastAPI 服务端。**服务端零改动**（CORS 已 `*`，鉴权会话化已支持多设备）。

> 技术方案见 `docs/technology/260728-移动端客户端技术方案.md`，设计稿见 `design/260728-mobile-app/`，桌面端对照见 `../desktop/`。

## 目录结构

```
application/mobile/
├── package.json              # tauri cli 脚本（dev/build/ios/android/icon）
└── src-tauri/
    ├── Cargo.toml            # Rust 依赖（tauri 2 + store/os/notification）
    ├── build.rs
    ├── tauri.conf.json       # frontendDist → ../../../web/dist；CSP；bundle
    ├── capabilities/default.json
    ├── .gitignore            # 忽略 gen/（ios/android 工程）、target/
    └── src/
        ├── main.rs           # 入口
        ├── lib.rs            # 插件装配 + 命令注册
        └── commands.rs       # 令牌存储(set/get/del_secret) + 生物识别(TODO)
```

## 前置依赖

1. **Rust 工具链** + 移动端 target：
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   # iOS
   rustup target add aarch64-apple-ios aarch64-apple-ios-sim x86_64-apple-ios
   # Android（需先装 Android Studio + NDK）
   rustup target add aarch64-linux-android armv7-linux-androideabi x86_64-linux-android i686-linux-android
   ```
2. **iOS**：macOS + Xcode + Apple Developer 账号
3. **Android**：Android Studio + JDK + 签名 keystore
4. **本目录依赖**（Tauri CLI）：
   ```bash
   cd application/mobile && npm install
   ```
5. **初始化移动工程**（生成 `src-tauri/gen/{android,ios}`，已 gitignore）：
   ```bash
   npm run android:dev -- --init   # 或 tauri android init
   npm run ios:dev -- --init       # 或 tauri ios init
   ```
6. **图标**（生成到 `src-tauri/icons/`）：
   ```bash
   npm run icon -- <源图 png 1024x1024>
   ```

## 运行 / 构建

```bash
# 开发（热更新，挂模拟器/真机）
npm run ios:dev
npm run android:dev

# 发布构建（产物在 src-tauri/gen/{android,ios}/*/build）
npm run ios:build
npm run android:build
```

## 与前端的衔接

- 同一份 `web/dist` 同时供桌面/移动：`tauri.conf.json` 的 `frontendDist → ../../../web/dist`。
- 平台判定在前端 `web/src/utils/platform.ts::isMobile()`（UA 命中 iOS/Android）→ `App.vue` 选 `MobileLayout`，路由按平台分流到 `views/mobile/*`。
- 令牌存储：前端 `tokenStore` 经 `invoke('get_secret' / 'set_secret' / 'del_secret')` 调用本仓 `commands.rs`（桌面端同名命令，前端无分叉）。
- 服务器地址首屏接驳：移动 Tauri 首启未配置 → 路由强制进 `views/mobile/Setup.vue`（同桌面端守卫）。

## 应用锁 · GUILD LOCK

- **PIN**：前端 `composables/useAppLock.ts` 全实现（SHA-256 存储，启动/回前台落锁，`components/mobile/LockScreen.vue`）。已可用。
- **生物识别**：`commands.rs::authenticate_biometric` 为占位。接入步骤见该命令注释（添加 `tauri-plugin-biometric`、lib.rs 注册、capabilities 授权）。前端 `LockScreen` 已在 Tauri 环境调用该命令。

## ⚠️ 待工具链验证（本机无 Rust/iOS/Android 环境）

- Rust 侧未经 `cargo build` 验证（同桌面端历史）。
- store 命令、CSP、bundle 图标、移动工程 init 均需在装好工具链的机器上首次构建确认。
- 生产强化：令牌存储建议从 tauri-plugin-store 换为 iOS Keychain / Android Keystore。
- WebRTC（传输）在移动网络下 ICE/STUN 表现需实测（`iceServers: []` 当前仅局域网直连）。
