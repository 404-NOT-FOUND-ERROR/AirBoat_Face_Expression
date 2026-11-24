# 可执行步骤、验证和交接

以下命令从 `expression-library/` 执行。目的、开始信号、完成信号和证据位置分开写，便于下一位 AI 接着做。

## 1. 固定要修的版本

准备 `assets/contour-review/contour-review.afm` 与 `manifest.json`，确认工作树中的改动属于哪些任务。

```powershell
git status --short
python skills/airboat-expression-workflow/scripts/inspect_pack.py --output '<本轮 research 路径>/pack-before.json'
```

检查工具使用 Python 标准库。它核验 AFM 头、目录字节数、载荷/精灵哈希、RLE 解码和引用范围，报告 clip、兼容语义、帧数和包大小。成功打印 `status: passed`，退出码 0。比较期间保留对应 AFM/JSON 或可恢复提交，避免只留无法追溯的截图。

## 2. 选择生成入口

| 本次目的 | 入口 | 动作 |
| --- | --- | --- |
| 最新 AFM 动作/轮廓修补 | `scripts/build-contour-review.py` | 改源稿处理或动作谱，重建 AFM、JSON 和网页内嵌数据 |
| 原动作/大小眼/瞳孔归属 | `scripts/expression_source_repair.py` + `expression_repertoire.py` | 保留源图和 SCORES，修连续采样 |
| 待机、受惊 | `build-contour-review.py` 的对应 pose 函数 | 只改目标姿态，保留共享锚点 |
| 大笑 | `expression_repertoire.py` 的 laughing/laugh_lid | 连续抬下眼睑，保留错拍回弹 |
| 连续眼睑研究 | `scripts/expression_lid_study.py` | 适合明确的重设计需求，先做单项对照 |
| 旧 240 EAF 或初始 480 分层 | 原 complete/optimized 生成器 | 仅维护对应历史版本，不当作当前 contour 包 |

```powershell
python scripts/build-contour-review.py
python skills/airboat-expression-workflow/scripts/inspect_pack.py --output '<本轮 research 路径>/pack-after.json'
```

`build-contour-review.py` 是写入生成命令；单纯查看、统计或打包时不用重建。修改别名要一起更新网页语义选择、节点图、接入文档和检查。

`body_frames` 是播放采样帧数，不一定等于存储的 `keyframes` 数量。例如受惊可用 17 个姿态采样成 36 个主体帧；沿参考播放器的时间映射插值，不能把数量不同当作素材损坏。

## 3. 看同一份资源

打开 `docs/product/expression-contour-review.html#<语义>`，1× 看性格，0.5× 看瞳孔与眼睑，再拖进度看接缝。节点库在 `docs/product/expression-workbench.html?micro=<语义>`；AirBoat 还有父项目 `docs/product/expression-workbench.html`，两处共用 contour 包。

记录进入、动作高点、停顿、收尾和一整轮 GIF。对比取相同表演时刻，避免新旧时长不同造成误判。还要看 360/480 屏幕大小的小预览、圆屏边缘与字幕留位。

## 4. 跑对应检查

准备有 Pillow/NumPy 的 Python、Playwright 模块目录及可运行的 Chromium/Edge。优先复用 Codex 提供的 workspace dependencies，确认实际路径；普通 PATH 中的 `python` 可能缺图像依赖。Node 所在目录与模块目录分开确认。

```powershell
$playwrightModule = '<Playwright 模块的绝对路径>'
$browserExe = '<Edge 或 Chromium 可执行文件绝对路径>'
node tests/contour-review.cjs $playwrightModule $browserExe '../docs/product/expression-workbench.html'
python tests/validate_release.py
git diff --check
```

第三个参数是父 AirBoat 工作台；只有独立表情库时省略它。`contour-review.cjs` 验资源哈希、引用范围、逐帧渲染、主体变化、循环/过渡首尾、原动作节拍、左右镜像、困倦/疲惫素材复用且语义独立、手机/桌面和离线请求，产物在 `.test-output/contour-review/`。`validate_release.py` 另验保留的历史 EAF/optimized、生成一致性及本地链接，不单独证明 contour 全库正常。

修改 `assets/square-pop/` 时，另运行 `tests/square-pop.cjs`、`tests/square-pop-art.py` 和 `inspect_pack.py --pack-directory assets/square-pop`。浏览器测试覆盖29个语义节点及素材映射；艺术测试比较俏皮修改前后的眼白/瞳孔每帧，并确认无背景碎片。重建预览后，确认 `preview-manifest.json` 绑定新 AFM 哈希。

若修改的是波形合成，补跑 `tests/listen-overlay.c` 的原生 C 检查和 `tests/listen-overlay-browser.cjs`。只有接入实际 AirBoat 播放器时，按 `integrations/listen-overlay/README.zh-CN.md` 执行实际源码副本回归。新问题引发的失败要定位；已经通过且资源未变化，不反复扩大测试。

## 5. 交给两个主项目

| 项目 | 接入位置与适配 | 设备验收重点 |
| --- | --- | --- |
| AirBoat / Mosaico | 核对当前 `app_response → app_expression_view / app_expression_player → GSP`；母版 480，全脸只绘一次 | 语音、字幕、相机和控制页共存，离页/取消/返回 |
| DeskBot | 核对活动 `SetEmotion/SetStatus`、Emote/GFX 后端和实际屏幕；若 360 圆屏则等比派生 | 小智对话、触摸、休眠恢复、C61 身体动作只由事件触发 |

两边都先解析 `aliases`，逐眼清遮罩，正确使用目标矩形与 flip。AFM 由独立后端读取，既有 EAF 解码契约保持明确。字幕更新和每帧绘制不重发语音或身体动作。

交接卡写：本机资源路径、AFM+JSON 配对、哈希、语义别名、完整播放规则、关键变化、适配目标、构建/内存/耗时要求和用户操作卡。两项目同机时直接给本地路径，采用后各自纳入工程；GitHub commit 用于追溯，不替代工作树哈希。

本机最新交接样例：AirBoat `research/experience/20261123-expression-continuity/AIRBOAT.md` 与 `DESKBOT.md`。这两个路径相对父 AirBoat 项目，独立克隆的表情库可能没有它们。

## 6. 每层结果怎么记

| 层级 | 足够的记录 | 不代表 |
| --- | --- | --- |
| 资源检查 | 配对哈希、大小、解码、语义和边界 | 固件已接入 |
| 浏览器验证 | 播放、对照、镜像、触摸尺寸、离线、JS 错误 | 设备帧率或用户认可 |
| 目标构建 | 当前代码/目标、编译结果、分区、缓冲和耗时量测 | 已装机 |
| 安装与实时身份 | 安装回执、设备身份、版本/指纹和健康状态 | 用户能看到完整表演 |
| 用户实屏 | 实际设备、测试动作、用户反馈、通过/待改项 | 另一项目也已通过 |

显示数据和设备生命周期跟随各自项目规则。这里交接的是方法与资源，不替代两主线的实屏结果。

## 7. 发布与清理

用户要求发布时，先跑上述检查，确认提交范围和 `.secrets` 等配置的排除规则，再通过当前 Clash 代理执行：

```powershell
git -c http.proxy=http://127.0.0.1:7897 push origin HEAD:main
git -c http.proxy=http://127.0.0.1:7897 ls-remote origin refs/heads/main
```

实际分支以仓库状态和用户目标为准。记录本地提交、远端提交和 CI 结果；GitHub description 用英文，README 保留中英切换。历史成功发布 `5a70ba7` 不含后续本机候选，不能用旧 CI 结果覆盖当前工作树。

用户要求清理时，只列当前任务的具体产物和大小。保留原始美术、提示词、回执、当前配对资源、验证证据和主线需要的安装包；重复截图、已替换的临时对照和临时构建可按授权范围清理。删除前解析实际路径，区分项目和其他支线。磁盘占用和本轮释放量都现场量测，历史数字不当作当前结果。

## 阶段记录模板

```text
任务：修哪项表情/哪种缺陷；用户授权的变化范围
基线：源稿、资源对、哈希或提交；保留哪些节拍
方法：改哪一层，为什么能消除现象
产物：配对资源、工作台入口、GIF/同帧对照
验证：实际运行命令、结果文件、软件/构建/安装/实屏分别状态
交接：AirBoat/DeskBot 各自下一步与完成信号
```
