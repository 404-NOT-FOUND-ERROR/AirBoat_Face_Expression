# Square Pop · 方圆怪趣接入

[全套动态对比](expression-square-review.html) · [节点工作台](expression-workbench.html?square=funny) · [已确认待机](expression-square-idle.html)

21 段独立表演共用用户已确认的软方对称待机。待机双眼同尺寸，包含小瞥、呼吸、慢眨和双眨；情绪表演保留方圆变化、大小眼、错拍装饰与夸张回弹。AirBoat 原有 29 个语义入口全部保留，重复的表演资源通过目录别名共用。

| 独立动画 | 保留的语义入口 |
| --- | --- |
| `idle` | `idle`、`neutral` |
| `tried` | `tried`、`sleepy` |
| `happy` | `happy`、`laughing` |
| `sad` | `sad`、`crying` |
| `silly` | `silly`、`question`（好奇歪头）、`insert`（插入动画） |
| `funny` | `funny`、`delicious`（好吃）、`eat`（吃东西） |

「困倦」与「疲惫」仍是两个独立语义入口，分别调用同一份 `tried` 动画。其余未列出的语义各自对应同名动画。

## 配对资源

| 项目 | 当前值 |
| --- | --- |
| [AFM](../../assets/square-pop/square-pop.afm) | 4,607,851 B |
| [目录](../../assets/square-pop/manifest.json) | 720,473 B |
| 合计 | 5,328,324 B，约 5.08 MiB，比全展开版小24.6% |
| 工作台内嵌数据 JS | 6,864,408 B，仅用于离线网页，包含 AFM Base64 与完整目录 |
| AFM SHA-256 | `1b835f35bd1cb71d08590f3027fba25d2892a8ec5bb7f56a5145e3be16ea359b` |
| 画布 / 帧率 / 覆盖 | 480×480 / 25 fps / 4 bit，16 级 |
| 表演 / 兼容语义 | 21 / 29 |
| 待机 | 160 帧，6.4 秒，逐帧精确镜像 |
| 完整采样 | 1,954 帧，含进入与收尾 |

此 AirBoat 精简包单独放在 `assets/square-pop/`，上一版保留在 `assets/contour-review/`。本轮已完成资源和浏览器检查，固件构建、安装及实屏验收仍由 AirBoat 主线完成。

## 播放契约

沿用 [AFM1 精灵格式](layered-expressions.zh-CN.md)。`aliases` 只复用素材文件，调用语义仍保持独立。`authored_transitions: true` 表示进入和收尾已有逐帧形变姿态。按阶段读取：

| 阶段 | 帧区间 | 图层来源 |
| --- | --- | --- |
| 进入 | `[0, 19)` | `clip.entry_keyframes` |
| 主体 | `[19, 19 + body_frames)` | `clip.keyframes` |
| 收尾 | `[19 + body_frames, 38 + body_frames)` | `clip.exit_keyframes` |

每帧 40 ms。进入末帧与主体首帧、主体末帧与收尾首帧逐像素相同；完整首尾为共同绿色待机。主体循环只循环主体区间。时间来自播放时钟，迟到按实际时间选帧。

进入和收尾直接绘制对应的姿态；眼形已经包含几何形变，背景沿 [参考播放器](expression-optimized-player.js) 的 HSV 路径变色。瞳孔在眼白范围内裁切。默认待机使用左右四图层与精确镜像复用，其他姿态也可能将双眼合为一组图层，按引用矩形绘制即可。全脸绘制一次，镜像开关作用于完成画面。

中途打断以当前显示姿态接下一语义，由项目现有播放器与回应所有者处理。语义事件驱动语音和身体动作；动画绘帧只更新显示。聆听条继续使用[透明合成](../../integrations/listen-overlay/README.zh-CN.md)。

## 制作与验证

1. `scripts/export-square-idle.cjs` 从已确认的待机绘制器导出 160 帧眼白与瞳孔覆盖；源哈希记录在 `inputs/soft-square-idle.json`。
2. `scripts/build-square-pop-pack.py` 读原生 GIF、分离图层、采样完整表演，按每只眼的局部轮廓构建 19 帧进入，反向复用为收尾。脚本需要 NumPy、Pillow 和 SciPy。
3. `scripts/render-square-pop-review.cjs` 从实际 AFM 解码器导出各语义的 GIF、缩略图、动态拼图与过渡分解图；[预览回执](../../output/imagegen/airboat-square-pop-20261124/preview-manifest.json)绑定 AFM 哈希。
4. `tests/square-pop.cjs` 检查已确认待机的 73,728,000 个覆盖采样、所有阶段边界、主体循环、离线播放、两个节点库和手机布局。通用检查器继续校验精灵游程、引用和哈希。
5. `tests/square-pop-art.py` 比对俏皮修复前后的眼白/瞳孔全部48帧，检查96图层精确不变，以及所有主体/进入/收尾姿态均不含绿色残片。

验证回执：[AFM 包检查](../../output/imagegen/airboat-square-pop-20261124/pack-validation.json) · [浏览器与节点检查](../../output/imagegen/airboat-square-pop-20261124/validation.json) · [俏皮像素回归](../../output/imagegen/airboat-square-pop-20261124/art-validation.json)。

API 艺术源稿、提示词和实际调用参数保留在 [本轮目录](../../output/imagegen/airboat-square-pop-20261124/)。预览卡片和交付 GIF 都由 AFM 渲染，和播放器使用同一份素材。

## 两项目接入顺序

当前 AirBoat 资源映射和检查清单见[AirBoat 接入卡](../../integrations/square-pop/AIRBOAT.md)；DeskBot 接入时的语义边界和适配检查见[DeskBot 评估卡](../../integrations/square-pop/DESKBOT.md)。

AirBoat 主开发从本机 `D:\502 Bad Gateway\Codex Project\ESP AirBoat\expression-library\assets\square-pop\` 读取 AFM 与目录，接现有 `app_response → app_expression_view / app_expression_player → GSP`。保持现有语音、字幕、相机和身体动作入口，先量测资源分区、工作缓冲和帧耗时，再构建候选。

DeskBot 主开发从同一路径读取，按当前活动显示后端适配。若目标为 360 圆屏，等比派生全脸，检查四周与字幕留位；记录派生资源大小和新哈希。沿当前 `SetEmotion/SetStatus` 链路接入，身体动作保持由原事件触发。

本包把笑/开心、哭泣/难过、好奇/插入动画/俏皮、好吃/吃东西/搞怪四组入口各合并为一份视觉动画。精简后的实际大小、哈希和帧数见同目录 manifest 与本轮研究记录。各主线以当前分区和实测帧耗时选择装入方式。

实屏验收先看待机的对称与眨眼，再看思考、好奇、大笑、晕眩和疲惫的一整轮；随后试对话、语音条、字幕、取消、切页与返回。构建、安装、实时身份和用户反馈分别记录。
