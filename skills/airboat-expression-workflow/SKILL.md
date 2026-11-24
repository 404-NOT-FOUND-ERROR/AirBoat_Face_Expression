---
name: airboat-expression-workflow
description: 制作、修补和交接 AirBoat 与 DeskBot 的彩色表情库，复用原动作节拍，处理瞳孔、过渡、透明聆听条与 AFM 分层资源，并通过离线工作台验证。适用于这两个项目的表情工作，不处理一般固件故障或飞控开发。
---

# AirBoat / DeskBot 表情工作流

把已认可的造型、完整表演和微动作交付到可对照的工作台，再按实际设备的显示链接入。默认采用项目内已有生成器、素材和播放器。

本目录在 `expression-library/skills/airboat-expression-workflow/`；以下工程路径以 `expression-library/` 为根。该技能保存在项目内，另一位 AI 可直接读取本文件使用。

## 先判断本次工作

| 用户需求 | 先读 | 预期交付 |
| --- | --- | --- |
| 新表情、参考图、原生 GIF | [美术与动作](references/art-and-motion.md)、[独立生图](references/image-api.md) | 新稿、提示词、调用记录和可播放预览 |
| 现有表情有瑕疵 | [修补案例](references/repair-cases.md) | 只改对应缺陷的新旧同帧、完整动态对照 |
| 体积、清晰度、镜像和黑框 | [修补案例](references/repair-cases.md) | 可复算的资源统计、合成结果 |
| 验收、移交、发布或整理产物 | [执行步骤](references/runbook.md) | 配对资源、验证记录和各项目接入卡 |

按需读对应参考，不为一次修补重跑整个生图流程。

## 已确认的制作约定

- 「修一下瑕疵」保留原造型、幅度、时长、停顿和左右差异；先定位问题帧。用户明确要求重新设计时再改动作。统一成一套圆眼、平滑成同一种节奏，会丢掉表情性格。
- 当前母版为 480×480、25 fps。完整双眼已经包含镜像和左右时差；原版窄单眼素材才按各自布局镜像配对。
- 共享绿色待机和首尾锚点用于接续；主体仍有完整表演。进入、表演和收尾分别验证，中途打断从当前姿态衔接。
- 当前并列维护两套 480 px 包：`assets/contour-review/` 是完整微动作库；`assets/square-pop/` 是 AirBoat 轻量整合包，21份独立表演由29个语义入口引用。默认和待机采用用户确认的等大软方对称眼。Square Pop 的 `authored_transitions: true` 使用目录内19帧 `entry_keyframes` / `exit_keyframes`，不能按旧9帧轮廓包推断。别名只共用素材，不合并事件语义节点，例如 `sleepy` 和 `tried` 必须分别显示。
- 瞳孔、眼睑、眼睛整体和装饰各有节拍。保留预动、主动作、短停、轻重不同的回弹、衰减余震和回稳。首尾一致不代表所有动作走同一条时间曲线。
- 目前 `neutral → idle`、`sleepy → tried`。`tried` 是现有疲惫动画键；困倦和疲惫在语义目录、触发节点与事件优先级上分别保留，只在素材文件层复用。
- `aliases` 只减少重复视觉素材，不会合并用户可见语义、事件优先级或动作请求。困倦与疲惫仍各有节点；按项目明确指定的共享组建立其他素材映射。
- `assets/square-pop/` 采用 AirBoat 专用语义映射。DeskBot 可复用造型或 AFM 播放方案，但须按自己的语义合同建立映射，不能直接继承 AirBoat 的 `laughing/question/insert` 等别名。
- 排查透明 GIF 的背景闪烁时，先比较 RGBA alpha 与 RGB 不透明提取，定位背景残片、眼白、瞳孔和装饰。清理后逐帧验证眼白/瞳孔不变；仅当源图确为透明背景且目标表情无真实彩色装饰时才移除装饰层。
- 用户看新旧大图、屏幕尺寸小图和完整动态后评审。软件检查通过与用户认可视觉效果分别记录。

## 一次迭代的执行顺序

1. **固定现状。** 读取项目协作规则、当前 manifest、用户反馈和工作树差异。用本目录的 `scripts/inspect_pack.py` 生成包摘要。另存要比较的 AFM/JSON 配对或记录可恢复的 Git 提交。
2. **限定改动。** 写明要修的现象、对应帧、仍需保留的动作特征。先在一项上修补；不以整库重绘代替局部修补。
3. **选择处理层。** 原始美术 → 动作谱 → 图层提取 → 资源编码 → 播放器 → UI 叠层，逐层定位。先用已有源稿和动作谱；确有新美术需求才调用 Images API。
4. **生成同一份交付。** 从源稿重建 AFM、manifest 和网页内嵌数据；工作台直接播放待交付资源。新旧对照至少覆盖进入、动作高点、停顿、收尾和循环边界。
5. **分项验证。** 资源读回、重点表情、共享首尾、镜像和别名、完整动态、手机/桌面、离线加载依次检查。共享动画映射须断言各语义节点仍分别存在；清理背景须断言原眼白/瞳孔姿态逐帧不变。执行方法见 [runbook](references/runbook.md)。
6. **按当前主线交接。** AirBoat 与 DeskBot 分别确认显示所有者、分辨率、字幕/语音/身体动作入口。提交配对资源、哈希和接入卡；代码接入、构建、安装、实时身份和用户实屏验收分别记状态。
7. **归档可复用结果。** 阶段证据写进 AirBoat 的带日期 research。只把重复、高成本或影响架构的问题加入 known-solutions；一次性日志留在 research。按用户本次授权决定是否推送或清理。

## 本工程入口

- [微动作配对资源](../../assets/contour-review/manifest.json)、[方圆怪趣配对资源](../../assets/square-pop/manifest.json)、[Square Pop 预览](../../docs/product/expression-square-review.html)、[方圆接入卡](../../docs/product/expression-square-pop.zh-CN.md)、[微动作包摘要](references/current-pack.json)
- [动态对照](../../docs/product/expression-contour-review.html)、[节点工作台](../../docs/product/expression-workbench.html)
- [当前接入约定](../../docs/product/expression-micro-motion.zh-CN.md)、[AFM1 格式](../../docs/product/layered-expressions.zh-CN.md)
- [当前生成器](../../scripts/build-contour-review.py)、[连续轮廓修补](../../scripts/expression_source_repair.py)、[动作谱](../../scripts/expression_repertoire.py)
- [全库浏览器检查](../../tests/contour-review.cjs)、[聆听条算法](../../integrations/listen-overlay/README.zh-CN.md)

`references/current-pack.json` 是核验时的快照；每次改素材后重新运行检查并更新。它不会证明另一项目已采用同一包。

查看已有成功范围和证据时读取 [案例索引](references/case-index.md)。
