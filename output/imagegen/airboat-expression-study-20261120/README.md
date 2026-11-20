# AirBoat 表情设计参考

[打开比较页](gallery.html) · [图稿总览](reference-sheet.png) · [动作关键帧](motion-frames.png)

29 项包含固件的 28 个语义和独立聆听合成。每项可对照原版动效、生成参考图与新 GIF。

- png/：静态参考，由官方 Images API 的 gpt-image-2.5-sunburst 生成后分切；疲惫另行修正构图。
- gif/：gpt-image-2.6-sunburst 返回的原生 GIF，480×480，每项 16 帧。
- preview/：本地修整后的参考 PNG、25 fps GIF，固定背景，对每只眼的眼白和瞳孔分别插值，并接回循环起点。
- prompts/ 与 calls/：提示词、显式模型、请求字段、代理、输入及输出指纹。
- original/ 与 motion-study/：原库动效和基于用户原稿的五段本地节拍研究。

本批经 Clash 代理生成，接口为 https://api.openai.com/v1/images/edits。图稿选择、EAF 转码与 Mosaico 实屏评审沿同一条制作流程推进。
