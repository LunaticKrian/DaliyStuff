# PixelPack · 登录 / 注册 设计稿（260728）

> 深色 · 极客高级感。沿用 landing（`260727-pixelpack-landing`）确立的品牌令牌，
> 替换掉旧的「复古街机 / CRT 像素」登录风。

## 为什么重做

当前线上登录注册（`web/src/views/Login.vue`、`Register.vue`、`layouts/AuthLayout.vue`）仍是**旧复古风**：

- CRT 扫描线、移动扫描光带、40 个闪烁星点、像素网格、暗角
- 像素字体（Press Start 2P）、`>` 终端提示符、`_` 闪烁光标
- 硬 3px 边框、硬偏移投影 `3px 3px 0`
- 标题还写着**旧名 `DAILY STUFF`**（项目已改名 PixelPack）

而最新的 landing 已经整体转向**近黑底 + 靛蓝/紫/青渐变 + 玻璃拟态 + Space Grotesk/Inter/JetBrains Mono**。
**登录页与最新品牌方向完全脱节**，读起来像「AI 套了个通用复古模板」——这就是「AI 味」的来源。

## 设计方向

严格沿用 landing 的令牌（色板、字体、极光、网格、圆角、投影），让登录注册成为 landing 的自然延续：

| 维度 | 取舍 |
| --- | --- |
| 布局 | **分屏**：左 = 品牌/存档面板（落地页同款极光 + 网格），右 = 聚焦的认证表单卡 |
| 配色 | 近黑 `#0a0b10`；靛蓝 `#6366f1` / 紫 `#a855f7` / 青 `#22d3ee` 渐变 |
| 字体 | Space Grotesk（标题）/ Inter（正文）/ JetBrains Mono（微标签）—— **mono 微标签替代旧的 `>` 终端梗**，保留极客气质但不廉价 |
| 质感 | 玻璃面 `rgba(255,255,255,.04)`、柔焦投影、16px 圆角、青色聚焦环 |

## 签名元素（集中投入的大胆度）

**左面板做成一张「游戏存档 / 角色卡」**——产品是「把生活过成一场 RPG」，所以让认证页直接讲产品语言：

- **登录态**：显示「继续存档 Lv.24 · 冒险者」，EXP 78%，迷你统计（物品 / 连胜 / 成就）
- **注册态**：显示「新建存档 Lv.1」，且**密码强度实时驱动角色卡的 EXP 经验条与等级**——越强密码，初始等级越高，称号从「新手 → 见习 → 冒险者 → 老练 → 传奇」

这是 RPG 隐喻 × 认证流程的专属交集，不是任何通用模板会有的东西。表单本身保持克制：mono 浮动微标签、显隐密码、渐变主按钮、可选 GitHub（贴合 OSS / 开发者受众）。

## 预览

```
open design/260728-auth-ui/index.html
```

- 顶部「登录 / 注册」分段控件切换两个视图，也可深链 `#register` / `#login`
- 注册页输入密码可看到左侧角色卡 EXP 与等级实时变化

## 落地到 Vue 的映射

设计稿是自包含原型；落地时无需照搬 HTML，按现有结构映射即可：

1. **`AuthLayout.vue`**：移除 `scanlines-crt` / `scanline-sweep` / `stars` / `pixel-grid-overlay` / `pixel-vignette` / `insert-coin-text`，
   改为本稿的 `.brand`（极光 + 网格 + 角色卡）+ `<slot />` 包一层 `.form-panel`。标题 `DAILY STUFF` → `PixelPack`。
2. **`Login.vue` / `Register.vue`**：复用现有逻辑（`useAuthStore`、校验、错误处理），
   只替换模板与 `<style>`：表单结构、字段、`toggle-pw`、注册密码强度 EXP、提交按钮 loading 态。
3. **令牌**：建议在 `web/src/styles/theme.css` 新增一组「v2 深色令牌」（或与 landing 共享），
   把本稿 `:root` 里的 `--bg / --surface / --grad / --cyan …` 与字体导入统一管理，避免硬编码。
4. **字体**：把 Google Fonts 的 Space Grotesk / Inter / JetBrains Mono 接入 `fonts.css`。
5. **密码强度 → EXP**：`main.js` 里的 `strength()` 与 `renderStrength()` 直接可移植为组合式函数，
   数据驱动 `--exp`（CSS conic 渐变环）与等级文案。

## 无障碍 / 响应式

- 键盘聚焦环、`aria-selected` 视图切换、`aria-live` 错误区、密码显隐 `aria-label`
- `prefers-reduced-motion` 关闭极光漂移与入场动画
- ≤ 900px 折叠为单列，左面板降级为紧凑头部（隐藏统计行）
