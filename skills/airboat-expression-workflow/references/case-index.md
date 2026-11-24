# 成功案例与证据索引

核对日期：2026-11-24。这里记录已完成的资源、方法或软件验证。用户提出的新需求和设备后续接入单独标注，不能由网页检查推为实屏成功。

证据目录相对父项目 `ESP AirBoat/research/experience/`。独立下载的表情仓库可能不含这些 research 记录；可复用代码、技能和工作台在表情库内。

| 案例 | 得到的可复用方法 | 对应证据 | 验证范围 |
| --- | --- | --- | --- |
| 静态参考＋原生 GIF | 独立配置、显式模型、Clash、输入/提示词/参数/回执一并保存 | 表情库 `output/imagegen/airboat-expression-study-20261120/calls/`、`manifest.json` | 29 张参考与 29 个原生 GIF 曾实际生成；未来模型可用性另核 |
| 无限画布语义工作台 | 场景 → 编排 → 语义 → 素材；播放、拖帧、镜像、替换清单 | `20261120-expression-workbench`；`tests/workbench.cjs` | 桌面/手机离线工作台 |
| 共享待机与连续切换 | 进入、完整表演、收尾分开，换情绪可从当前姿态接续 | `20261120-220030-expression-transitions`；`tests/transition-motion.cjs` | 对应历史过渡原型曾覆盖 841 个语义对；不等同当前设备 |
| 排查「似乎只装了过渡」 | 直接解码交付素材，按阶段标记与原版并排播放 | `20261121-expression-complete-review` | 资源包含主体和阶段预览；固件实际调度另验 |
| 清晰度与占用核查 | 同帧变更分辨率/色数，区分整体资源和个别语义，共享按去重统计 | `20261121-expression-quality-audit` | 原/新 EAF 实际字节及编码实验 |
| 480 分层 AFM | 背景程序绘制、局部覆盖图层、精确镜像复用、独立时序 | `20261121-expression-layered-480`；`tests/optimized-expressions.py` | 格式、解码、边界/坏输入与浏览器；设备解析待主线 |
| 双眼对称与完整惊讶 | 同源待机锚点；闭眼遮瞳；从原图完整高度提取 | `20261122-expression-contour-review` | 同帧、对称、首尾和裁切检查 |
| 表情各有自己的微动作 | 开心回弹、晕眩递减余震、张望瞳孔先动 | `20261122-expression-beat-study`、`20261122-expression-micro-motion-library` | 全库浏览器和指定节拍检查 |
| 大笑合理成月牙 | 下眼睑抬起遮瞳孔，再成弧；保留爱心错拍与两次回弹 | `20261123-laughing-eyelid` | 本地候选、首尾、逐帧和动态对照 |
| 默认待机丰富化 | 6.4 秒小瞥、慢眨回弹、不同轻重的双眨、呼吸回中 | `20261123-idle-micro-motion`；当前 `tests/contour-review.cjs` | 共享首尾像素保持、眨眼/视线检查 |
| 原表情瑕疵局部修补 | 以源眼弧和独立黑瞳孔为对象插值，保留原动作谱 | `20261123-expression-continuity` | 原时长/节拍、大小眼交换、疲惫幅度、未改表情对照 |
| 困倦/疲惫合并 | 旧语义经别名兼容，素材共用，UI只留一个疲惫 | 同上；`expression-contour-player.js` 与两个工作台 | 27 clip、29 兼容语义、28 可见入口，已软件核对 |
| 聆听条透明合成 | 指定灰度 mask 与当前 RGB565 底图混合 | `20261122-listen-overlay-transparency` | 全 RGB565 底色、500 组浏览器组合、实际播放器源码副本；设备黑框解决另验 |
| AirBoat/DeskBot 本机交接 | 配对 AFM+JSON、当前哈希、实际显示链接入和各自验收 | `20261123-expression-continuity/AIRBOAT.md`、`DESKBOT.md` | 交接卡和路径核对；各固件接入状态由各主线记录 |
| GitHub 代理发布 | Clash 推送、远端提交一致、CI、英文 description/双语 README | `20261122-expression-release`；历史提交 `5a70ba7` | 该发布版远端与 CI 已核过；后续本机候选未因此发布 |
| 对话产物清理 | 只列本任务具体候选，区分重复测试与源码/当前资源/证据 | `research/maintenance/20261121-expression-cleanup`（父项目路径） | 对应轮次范围与哈希核对；新清理先现场枚举 |

## 当前固定快照

详见 [current-pack.json](current-pack.json)。核验时为 1,884,289 B、27 个实际 clip、29 个兼容语义、1,473 个精灵；播放共 2,332 帧（含每段进入和收尾）。当前 AFM SHA-256 为 `f97deb06407f1549c142e81da1455a9380c9649f7fda74eff31ac21ea565aa7e`。

这份快照由标准库检查器读回生成；浏览器依据为父项目 `research/experience/20261123-expression-continuity/validation.json`。以后的代码或美术变化会更新数值，复用方法而非沿用旧结论。
