# 表情制作流程

[English](production.en.md) · [README](../README.zh-CN.md)

## 从想法到实屏

1. **选择回应。** 在工作台选一个语义，看看触发来源以及是否与其他语义共用素材。
2. **确定姿态。** 用 480×480 画布画完整眼神；使用双眼镜像布局时，可以只画左眼。
3. **设计节拍。** 将动作分成预动、主动作、停顿、余震和回稳，分别写出瞳孔、眼皮、整对眼睛何时开始和停下。
4. **对照动画。** 结合原版看关键帧、动效与接缝，同时检查大图和 Mosaico 尺寸的小图。
5. **整理映射。** 导出替换清单，记录目标语义、源文件、镜像偏好和备注。
6. **转码接入。** 转为固件支持的 EAF，更新帧间隔与循环区间，构建后核对分区占用。
7. **实屏体验。** 检查眼神可读性、字幕、触摸取消、切页、对话和待机播放。

## 格式与布局

| 项目 | 当前实现 |
| --- | --- |
| 屏幕 | 480×480 |
| 设备合成 | 以 360×360 逻辑画布缩放到屏幕 |
| 双眼 | 原版窄图的左眼放在 x=10，右侧镜像 |
| 整脸 | 方形试换素材铺满屏幕 |
| 聆听 | 100×46 独立叠层，逻辑位置 (130,25)，15 fps |
| 原版动画 | 通常为 20 fps；单次播放结束保持最后帧 |
| 当前小样 | 240×240、10 fps，以整脸布局显示 |
| EAF 编码 | 8 位索引色 RLE，最长边 360 px |
| EAF 容器 | 最多 256 个条目，含元数据；单包上限 4 MiB |
| 循环记法 | [起始,结束)，帧号从 0 开始，结束帧不参与循环 |

工作台中的留位线用于检查顶部提示和底部字幕。1.29.0 应用分区余 176,480 B，UI 分区余 189,808 B。EAF 存在应用分区内，共用文件只计算一次。

## 动作语言

| 表情 | 动作节拍 |
| --- | --- |
| 开心 | 先压低、弹起，再做两次逐渐减小的回弹 |
| 晕乎乎 | 左右交替，振幅逐渐变小，最后完全稳住 |
| 好奇 | 瞳孔先看过去，眼形跟上，停顿后回中 |
| 受惊 | 快速拉开眼形，定住，再留下少量余震 |
| 困倦 | 两侧眼皮略微错开地下落，轻轻抬回 |

每项 API 原生 GIF 有 16 帧。本地修整版分别处理眼形和瞳孔，使用固定配色，以 25 fps 采样，并保存原生 GIF 供对照。

全套表情的进入、循环、回归接口与颜色/眼神时序见[表情过渡规范](product/transition-spec.zh-CN.md)，可在[过渡实验室](product/expression-transition-studio.html)逐项和按场景预演。

## 生图

安装依赖：

~~~sh
python -m pip install -r requirements.txt
~~~

静态图使用 [OpenAI imagegen skill CLI](https://github.com/openai/skills/tree/main/skills/.curated/imagegen)，GIF 使用[官方 Images API](https://developers.openai.com/api/docs/guides/image-generation)。将本机配置路径作为参数传入：

~~~sh
python scripts/run-expression-imagegen.py probe --env-file /path/to/imagegen.env --proxy http://127.0.0.1:7897
python scripts/run-expression-imagegen.py static --env-file /path/to/imagegen.env --cli /path/to/image_gen.py --proxy http://127.0.0.1:7897
python scripts/run-expression-imagegen.py gif --env-file /path/to/imagegen.env --proxy http://127.0.0.1:7897
~~~

本地配置使用 DESKBOT_IMAGE_API_KEY 和 DESKBOT_IMAGE_BASE_URL 两个字段，官方地址为 https://api.openai.com/v1。脚本在运行时读取，生图子进程接收所需凭据。目录中保留显式模型、代理、提示词、输入校验值与结果校验值。

## 重新生成与检查

~~~sh
python scripts/build-expression-workbench.py --check
python scripts/review-expression-imagegen.py
python scripts/polish-expression-gifs.py
python scripts/build-transition-runtime.py
python tests/validate_release.py
~~~

浏览器交互验证使用 Playwright：

~~~sh
node tests/workbench.cjs /path/to/playwright /path/to/chromium
~~~

检查涵盖动画解码、镜像、新旧映射、搜索、播放、画布平移缩放、候选 GIF、替换草案和桌面／手机布局。
