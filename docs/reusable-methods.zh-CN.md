# 表情工作流：可复用方法与步骤

整理日期：2026-11-24。覆盖这条表情支线的制作、修补、预览、编码、交接、代理发布和产物整理。

## 给下一位 AI

直接让它读取 [SKILL.md](../skills/airboat-expression-workflow/SKILL.md)：

```text
请读取本机技能入口：
D:\502 Bad Gateway\Codex Project\ESP AirBoat\expression-library\skills\airboat-expression-workflow\SKILL.md

按其中对应的方法处理这次表情任务。先保留已经认可的造型、完整表演和微动作节拍，再修本次指定的问题。使用当前本机资源核验与动态对照，分别记录软件检查和实屏结果。
```

技能保存在项目内，AirBoat 和 DeskBot 的 AI 都能读取。它没有安装到用户全局技能目录。

## 方法按任务查

| 现在要做什么 | 复用方法 | 操作说明 |
| --- | --- | --- |
| 画新表情或做 GIF | 独立官方 API、显式模型、Clash、回执归档 | [生图步骤](../skills/airboat-expression-workflow/references/image-api.md) |
| 表情缺少灵动 | 拆开瞳孔、眼睑、整体、装饰的起止节拍 | [美术与动作](../skills/airboat-expression-workflow/references/art-and-motion.md) |
| 瞳孔缺口、过渡跳、被裁切 | 按原图、拆层、动作谱、编码、合成逐层定位 | [修补案例](../skills/airboat-expression-workflow/references/repair-cases.md) |
| 高清与占用兼顾 | 480 母版、4 bit 边缘、局部图层、精确共享 | [格式约定](product/layered-expressions.zh-CN.md) |
| 检查当前到底是哪一版 | 核对配对文件、解码、哈希、别名和大小 | [检查脚本](../skills/airboat-expression-workflow/scripts/inspect_pack.py) |
| 把表情接进两个固件 | 按实际显示后端适配，完整播放，设备各自验收 | [执行与交接](../skills/airboat-expression-workflow/references/runbook.md) |
| 查哪些已成功、证据在哪 | 精选案例、范围和记录索引 | [成功案例](../skills/airboat-expression-workflow/references/case-index.md) |

## 一次修补怎么做

1. **看原来的完整动作。** 准备当前工作台和源稿，写下哪里有瑕疵、哪些造型与节拍继续保留。
2. **只改对应层。** 找到问题帧，判断是源图、拆层、跳帧、裁切还是叠层。保留原动作谱；需要重设计时先做独立候选。
3. **重建并读回。** 生成成对 AFM/JSON 与工作台数据，检查哈希、别名、边界和精灵解码。
4. **前后动态对照。** 1× 看感觉，0.5× 看细节，暂停到动作高点和接缝；再看小屏、镜像和完整一轮。
5. **记录可复用结论。** 保存实际检查结果、当前资源与对照，更新日期 research 和管线。
6. **按主项目接入。** 交当前本地路径、哈希、播放规则和操作卡，再分别做构建、安装、实时身份与实屏。

## 已固定的经验

- 「只修一下」保留原性格和动作；统一圆眼重绘曾损失思考、歪头和搞怪的灵动。
- 首尾统一只是过渡接口；进入之后要播完整表演，循环主体也要保留自己的节拍。
- 双眼身份跟着眼睛和瞳孔走，不能简单沿屏幕中线切开。
- 灰度聆听条的黑底用覆盖率合成处理，黑瞳孔仍为实色。
- 清晰度、文件大小和运行内存分别测量；网页预览通过不等于实机已接入。
- 同机项目直接用本地素材，当前工作树哈希比旧 GitHub 发布号更能确定本次资源。

目前标准库检查器、方法文档和证据索引可直接复用；当前设备固件状态仍以各主线最新记录为准。
