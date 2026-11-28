---
name: airboat-expression-workflow
description: 制作、修补和交接 ESP AirBoat / Mosaico 的表情库，围绕 480 方形 AFM、绿色待机锚点、分层微动作和 GSP 显示链路进行离线预览与验证。用于 AirBoat 表情工作，不适用于 DeskBot 的 EAF / 圆屏资源链路。
---

# AirBoat / Mosaico 表情工作流

本技能只负责 AirBoat 表情资源及其 Mosaico 接入。DeskBot 使用独立的 EAF、圆屏布局、语义映射和发布锁流程，应调用 `$deskbot-expression-workflow`。

表情库工程根目录为 `D:\502 Bad Gateway\Codex Project\ESP AirBoat\expression-library`。使用本机技能副本时，所有工程内资源路径都相对此目录解析；需要参考细节时，优先打开该工程内本技能目录中的对应 `references/` 文件。

## 先判断任务类型

| 任务 | 先读 | 主要结果 |
| --- | --- | --- |
| 新表情、参考图或 GIF | [美术与动作](references/art-and-motion.md)、[独立生图](references/image-api.md) | 配对源稿、提示词、调用记录与动态预览 |
| 修补已有表情 | [修补案例](references/repair-cases.md) | 保留原演绎的局部修补及同帧、动态对照 |
| 包体、清晰度、镜像或聆听条 | [修补案例](references/repair-cases.md)、[执行步骤](references/runbook.md) | 可复算的资源变化、图层合成和测试结果 |
| 验收或移交 Mosaico | [执行步骤](references/runbook.md) | AFM 与 manifest 配对、验证记录和 AirBoat 接入卡 |

## AirBoat 固定约定

- 母版为 480×480 全脸。当前生产资源使用 AFM1；按当前 manifest 区分主体表演、进入与收尾，不把过渡片段误当成完整表情。
- 默认表情和待机采用用户确认的对称软方眼与绿色底色。完整双眼素材自带左右布局和时差；只对原版窄单眼素材按布局镜像配对。
- 首尾锚点保持一致，微动作各有节拍：开心的轻重回弹、晕眩的递减余震、张望时瞳孔先动、疲惫的沉降和费力抬眼。修瑕疵先保留原造型、幅度、时长和节奏；只有用户明确要求重设计时才改动作。
- `assets/square-pop/` 是 AirBoat 专用轻量包：21 个视觉表演供 29 个语义入口引用。共享素材不合并语义节点；`sleepy` 与 `tried` 保持独立语义，按当前 manifest 查看视觉复用关系。
- 背景、眼白、瞳孔与装饰分层处理。检查 GIF 透明区时区分 alpha 与隐藏 RGB，逐帧确认眼白和瞳孔没有被误删；不把其他项目的 EAF 或映射表直接带入 AirBoat。
- 资源检查、浏览器预览、Mosaico 构建/安装、设备实时身份和用户实屏验收是不同证据层，分别记录状态。

## 一轮工作的执行顺序

1. 读取当前工作区差异、`docs/development/pipeline.md`、`docs/development/architecture.md`、`docs/development/known-solutions.md`，以及固件应用规则。确定目标资源、当前 manifest 和可恢复基线。
2. 先定位问题层：源画、动作谱、图层提取、编码、AFM 播放器或 GSP UI。只改用户指出的表情/帧范围，保留其他语义及时间节奏。
3. 从源稿重建 AFM、manifest 和预览数据；确认工作台直接播放将交付的配对资源。检查进入、完整演绎、收尾、循环边界和中途切换。
4. 按改动执行资源检查、`tests/contour-review.cjs`；Square Pop 另跑 `tests/square-pop.cjs`、`tests/square-pop-art.py` 和包检查。具体命令见 [执行步骤](references/runbook.md)。
5. 需要固件接入时，核对 `app_response → app_expression_view / app_expression_player → GSP` 当前链路，遵循 `firmware/mosaico-vibe/AGENTS.md` 的设备操作契约。按层记录构建、安装、实时身份和实屏反馈；浏览器通过不代表设备通过。
6. 用户要求阶段记录、发布或清理时，按 AirBoat 项目规则处理：阶段结果写入带日期的 `research/experience/` 并更新管线；GitHub 操作使用当前 Clash 代理；清理只针对明确的本任务产物。

## 项目内入口

以下路径相对 `expression-library/`：

- `assets/contour-review/manifest.json`：微动作与轮廓 AFM。
- `assets/square-pop/manifest.json`：AirBoat 专用 Square Pop manifest。
- `docs/product/expression-contour-review.html`：表情动态预览。
- `docs/product/expression-workbench.html`：节点工作台。
- `docs/product/layered-expressions.zh-CN.md`：AFM 与显示接入约定。
- `skills/airboat-expression-workflow/scripts/inspect_pack.py`：AFM 检查器。
- `skills/airboat-expression-workflow/references/runbook.md`：完整验证步骤。
