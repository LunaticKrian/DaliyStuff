# PixelPack · 整站 UI 重构（设计稿 v1）

> 参照 `../260728-auth-ui/` 的高级深色方向，扩展为**完整设计系统 + 桌面/移动关键页原型**，
> 在「游戏 / 数据」界面融入克制的**像素工艺**。深 / 浅双主题、桌面 + 移动。

## 预览

```bash
open design/260728-site-redesign/index.html        # 设计总览（设计系统展示 + 入口）
open design/260728-site-redesign/desktop/app.html  # 桌面端可点击原型（7 个视图，顶部导航切换）
open design/260728-site-redesign/mobile/app.html   # 移动端可点击原型（5 个 tab，底部 tabbar 切换）
```

- 桌面导航 / 移动 tabbar 可点击切换视图，支持深链 `#items` / `#stats` …
- 顶栏 / 设置里的 ☾ 按钮一键切换**深 / 浅主题**。

## 目录结构

```
260728-site-redesign/
├─ index.html                  # 设计总览（原则 / 色彩 / 字体 / 像素工艺 / 图标 / 预览入口）
├─ design-system/              # ★ 设计系统（全站共享）
│  ├─ tokens.css               # 语义令牌：深色默认 + [data-theme=light] 浅色
│  ├─ typography.css           # 字体加载 + 排版工具类
│  ├─ pixel.css                # 像素工艺层（直角卡/角标/分段块/徽章/RPG条/图标）
│  ├─ components.css           # 通用组件（按钮/卡片/表单/表格/徽章/导航/弹窗…）
│  └─ icons.svg                # 像素图标 sprite（Pixelarticons MIT + 手绘 px-gem，59 个）
├─ desktop/   app.html · styles.css · app.js     # 桌面外壳 + 7 视图
├─ mobile/    app.html · styles.css · app.js     # 移动外壳 + 5 视图
└─ README.md
```

> 注：每个 app.html / index.html 已**内联** icons.svg，保证离线 / 截图可靠；构建时由 `<!-- @@SPRITE@@ -->` 标记注入。

## 设计原则

1. **高级感当底座** —— 近黑底 + 靛蓝紫青渐变 + 玻璃拟态 + Space Grotesk / Inter / JetBrains Mono。彻底丢弃 CRT 扫描线、闪烁星点、`>` 终端梗、硬偏移投影、像素字当正文（这些是旧版「AI 味」的来源）。
2. **像素只进数据层** —— 像素工艺（分段经验条 / 角标取景 / 像素图标 / LV 像素字）只出现在角色卡、进度、统计等「游戏 / RPG 数据」表面；输入框 / 按钮等控件区保持现代精致。两者分工共存，而非像素糊满全屏。
3. **系统化 · 主题无关** —— 组件只引用语义令牌，深 / 浅双主题零改造切换；桌面与移动同源。

## 像素工艺清单

| 设备 | 类 | 用途 |
|---|---|---|
| 直角卡片 + 抖动底纹 + 渐变描边 | `.px-card.dither.grad-border` | 角色卡 / 详情头 |
| 四角 L 形刻度（HUD 取景） | `.tick.tl/.tr/.bl/.br` | 像素卡取景框 |
| 分段像素块条 | `.blocks[data-blocks][data-pct]` | EXP / HP / MP / 进度 / 密码强度 |
| 像素徽章 | `.px-badge` | LV / 等级点睛（Press Start 2P） |
| 像素 chip | `.px-chip` | 分类 / 标签 |
| RPG 数据条 | `.rpg-bar` | HP / MP / EXP 带标签 |
| 像素图标 | `<svg class="pi"><use href="#pi-*"/></svg>` | 全站图标 |

像素浓度可平滑增减：更克制 = 去角标 / 抖动、`--r-px` 改回圆角；更浓 = 控件聚焦加像素角标、按钮加切角。

## 资产与署名

| 资产 | 来源 | 许可 |
|---|---|---|
| 像素图标（58 个 + smartphone） | [Pixelarticons](https://github.com/halfmage/pixelarticons) by Gerrit Halfmann | **MIT** |
| 像素宝石图标 `px-gem` | 手绘补充 | 原创可随意用 |
| Space Grotesk / Inter / JetBrains Mono | Google Fonts | OFL |
| Press Start 2P / Pixelify Sans / VT323（像素点缀） | Google Fonts | OFL |
| 背景（极光 / 网格 / 抖动） | CSS 生成 | — |

## 覆盖页面

**桌面（`desktop/app.html`）**：角色信息 / 物品 / 物品详情 / 统计 / 委托 / AI 对话 / 设置 —— 覆盖仪表盘、列表、详情、表单、数据可视化、会话、设置七种布局类型。
**移动（`mobile/app.html`）**：角色 / 物品 / 委托 / AI / 我（设置）。

## 落地到 Vue（`web/src`）

设计稿是自包含原型；落地时无需照搬 HTML，按结构映射：

1. **令牌** → 把 `design-system/tokens.css` 合并进 `web/src/styles/theme.css`（现有 `[data-theme=light]` 约定一致），替换旧的 `--pixel-*` 复古令牌；字体接进 `fonts.css`。
2. **组件** → `components.css` / `pixel.css` 拆为全局样式或组件化；`MainLayout.vue` / `MobileLayout.vue` 去掉 `scanlines-crt / stars / pixel-vignette / [DS] / 投币`，换成本稿顶栏 + 状态栏 / 底部 tabbar。
3. **图标** → `npm i pixelarticons`，按需 import 单个 SVG；或保留 sprite `<use>` 方案。手绘 `px-gem` 可入库。
4. **分段像素块** → `app.js` 里的 `buildBlocks()/fillBlocks()` 移植为组合式函数，数据驱动 `--exp`（conic 环）与 `.on`。
5. **页面** → 逐个 `views/*.vue` 与 `views/mobile/*.vue` 套用对应视图的标记 + 类名，逻辑层（stores/api）不动。

## 校验

深 / 浅双主题在桌面（仪表盘 / 物品 / 统计 / 委托 / 聊天 / 设置 / 详情）与移动（角色 / 物品）均已用无头 Chrome 截图 + 图像分析交叉核对：图标渲染、分段块、角标、等级环、图表（柱图 / 环形）、对比度、响应式均通过，无重大 bug。
