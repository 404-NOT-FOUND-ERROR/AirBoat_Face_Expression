# 独立 Images API 流程

## 适用步骤

只有需要新美术稿或新原生 GIF 时进入本步骤。现有素材的瞳孔、裁切、节拍或编码问题，先按 [repair-cases](repair-cases.md) 在本地修补。

本项目已成功使用独立的 OpenAI 官方 Images API。静态图使用 imagegen 配套 CLI；原生 GIF 使用项目独立脚本。下列模型与参数是已有回执，不代表所有未来模型或参数均可用；新增调用前核对当前官方文档和工具实际支持。

## 准备

1. 读取可用 imagegen skill 的独立 API/CLI 使用方式。
2. 只读引用 `D:\502 Bad Gateway\Codex Project\DeskBot\.secrets\imagegen.env`；仅在生图子进程里读取/映射所需字段。
3. 说明文档的当前路径是 `D:\502 Bad Gateway\Codex Project\DeskBot\docs\image-api-workflow.md`。早期消息中的 `docs\image-api-workflow\.md` 路径已不适用。
4. 使用 Clash 本地 HTTP 代理。本轮成功回执是 `http://127.0.0.1:7897`；新机器或新会话先确认实际监听端口。
5. 准备已认可的全脸底图、目标语义、动作提示词和本轮输出目录。配置文件、聊天 API、Codex 配置和全局环境各自保持独立。

配置字段为 `DESKBOT_IMAGE_API_KEY`、`DESKBOT_IMAGE_BASE_URL`、`DESKBOT_IMAGE_MODEL`。调用显式传模型；凭据只存在生图进程中，回执只记模型、端点、代理、输入/输出哈希和安全错误码。

## 已成功的调用形态

| 目标 | 历史调用与参数 | 成功依据 |
| --- | --- | --- |
| 静态参考 | `gpt-image-2.5-sunburst`；1024×1024、medium、PNG，官方 edit CLI | `output/imagegen/airboat-expression-study-20261120/calls/static-*.json` |
| 原生 GIF | `gpt-image-2.6-sunburst`；480×480、medium、complexity=medium、16 帧、GIF、n=1 | `calls/gif-idle.json`、`calls/gif-laughing.json` 的 status=ok |
| 慢表情节奏 | 每帧 120 ms；如 idle、relaxed、tried、sad、crying | 回执逐帧 delays_ms 和真实 GIF 解码 |
| 活跃表情节奏 | 每帧 90 ms；如 laughing | 同上；后续本地动作谱仍可独立细化 |

接口为 `https://api.openai.com/v1/images/edits`。现有 GIF 脚本通过明确代理的 HTTP 客户端调用，`trust_env=False`，设请求超时并禁自动重试。若请求结果不确定，先看回执和输出，按本次任务数量决定补跑，避免盲目重复生成。

## 执行动作

命令从 `expression-library/` 执行，`python` 指具备项目依赖的已确认解释器：

```powershell
$imageConfig = 'D:\502 Bad Gateway\Codex Project\DeskBot\.secrets\imagegen.env'
$imageProxy = 'http://127.0.0.1:7897'
python scripts/run-expression-imagegen.py probe --env-file $imageConfig --proxy $imageProxy
python scripts/run-expression-imagegen.py static --only 01 --env-file $imageConfig --proxy $imageProxy --cli '<已确认的 image_gen.py 路径>'
python scripts/run-expression-imagegen.py gif --only happy --workers 1 --env-file $imageConfig --proxy $imageProxy
```

`static --only` 选美术分组 ID，`gif --only` 选语义键。先核对 `study.json` 中实际存在的 ID。`probe` 读取模型列表，不生成图片。

现有 `run-expression-imagegen.py` 的 `OUT` 固定到历史研究目录。新一轮先在独立候选副本中设置输出位置，或将输出目录做成参数；保留已认可的原始稿和回执。脚本还依赖本机已有的 `httpx2` 客户端，执行前检查所选解释器是否具备该模块。

## 提示词的有效结构

1. 用已认可底图固定两眼布局、大小、配色和画面占比。
2. 每次只指定一种表情，并说明主体动作和要保留的性格。
3. 明确瞳孔先动、眼皮稍后、两眼错拍、装饰晚起、回弹递减等节奏；避免只写「生动、流畅」。
4. 要求完整单画幅动画，背景稳定，装饰在画布内。
5. 首尾可用于循环或接共享待机；具体接续由本地动作/合成层验收。

## 完成信号与结果位置

收到 GIF 后用 Pillow 实际解码，检查格式为 GIF、帧数大于 1、尺寸、逐帧时长和循环标记；改后缀不算原生 GIF。静态图、原生 GIF、修整版分开留存。

在本项目 `output/imagegen/<本轮名称>/` 保存输入图、提示词、调用参数、原始输出、预览、manifest 和安全回执。展示完整 GIF 供用户评审，再决定是否进入 AFM。源码里记录的模型可用性只对应当时回执。
