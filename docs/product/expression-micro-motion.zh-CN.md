# 微动作表情库 · 接入卡

[全库动态对比](expression-contour-review.html) · [节点工作台](expression-workbench.html?micro=look_around) · [AFM1 基础格式](layered-expressions.zh-CN.md)

这版覆盖 29 个语义、28 段独立表演。`neutral` 与 `idle` 共用对称绿色眼神；左右看共用精灵，位置和图层镜像成对变换。开心的压扁、悬停与二次回弹，晕眩的递减余震，以及张望时瞳孔领先眼形的节拍均保留。困倦、思考、大笑等有各自的停顿、错拍和恢复，而不是套用一条统一的运动曲线。

## 本地资源

从 `D:\502 Bad Gateway\Codex Project\ESP AirBoat\expression-library` 读取：

| 文件 | 用途 |
| --- | --- |
| [contour-review.afm](../../assets/contour-review/contour-review.afm) | 眼白、瞳孔和装饰的局部精灵 |
| [manifest.json](../../assets/contour-review/manifest.json) | 裁切尺寸、绘制矩形、镜像、节拍、语义与来源哈希 |
| [expression-optimized-player.js](expression-optimized-player.js) | `AirboatLayeredPlayer(pack)` 合成参考 |
| [build-contour-review.py](../../scripts/build-contour-review.py) | 从保留的 480 原始 GIF 与动作谱重建 |
| [contour-review.cjs](../../tests/contour-review.cjs) | 浏览器验收、交界帧和对称检查 |

AFM 与 JSON 共 **2,238,680 B（2.14 MiB）**。比上一版 480 分层资源大约 7.4%，比 240 交付 EAF 小约 41.2%。AFM SHA-256 为 `38bfea99ef37742e43cb07707f0bfef11e3354fee9967fad13e4b19a7f137090`。设备端工作缓冲和分区用量在固件接入时量测。

## 接入顺序

1. 将 AFM 和目录的必要字段纳入各自工程，记录母版哈希。旧 EAF 解码器继续读取原格式；候选资源通过独立的 AFM 合成后端接入当前显示所有者。先跑待机、受惊、单眼眨、晕眩和含装饰片段，再切换全库。
2. 母版为 480×480、25 fps，进入和收尾各占 9 帧。精灵原始 `w/h` 和引用里的目标矩形可能不同，按目标矩形平滑采样。每只眼单独清空遮罩，先合成眼白，再用同一只眼的覆盖裁住黑瞳孔，缺眼白则瞳孔不可见；之后输出 RGB565。对比预览的背景、装饰、眼白、瞳孔顺序。
3. `exit_from_last` 使用实际主体末姿势；`clip_pupils` 启用逐眼裁切。固定首尾在共享绿色待机，主体循环边界对齐。运行中若被新语义打断，从当前姿势接目标；字幕更新不重播表情，表情帧推进不再次触发语音或身体动作。单次/持续状态沿现有语义契约，工作台中的「持续表演」用于单独审片。
4. 聆听表情有独立彩色图层。若保留旧 `listen.eaf` 作为状态提示，走[透明覆盖参考](listen-overlay-preview.html)，避免同屏叠两条提示；检查字幕和状态栏遮挡。

**AirBoat**：沿当前 `app_response → app_expression_player → GSP` 链路接入，480 母版按设备原画布绘制。先做主机解码、像素和状态测试，再做固定 S31 构建；检查分区余量、屏幕帧耗时及相机、语音和飞控共存。安装交给主线使用的程序。

**DeskBot**：从当前 `SetEmotion`／`SetStatus` 显示入口接入，情绪到 C61 底座动作的映射继续只在原事件入口执行。若当前屏幕为 360×360，先做等比缩放的预览与派生资源，核对圆屏边缘及字幕，再测 ESP32-S3 的内存、帧耗时和对话、触摸、休眠恢复。DeskBot 直接使用本机路径。

本轮完成资源生成和浏览器验证。两项目的设备端接入、固件构建、安装及实屏验收分别记录。
