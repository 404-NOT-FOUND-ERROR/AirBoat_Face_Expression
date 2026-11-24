# DeskBot Square Pop 评估卡

AirBoat Square Pop 资源可从同机表情库的 `assets/square-pop/` 读取。当前 AFM SHA-256：`1b835f35bd1cb71d08590f3027fba25d2892a8ec5bb7f56a5145e3be16ea359b`，配对资源 `5,328,324 B`。采用时复制到 DeskBot 自己的素材目录并记录哈希。

这是为 AirBoat 指定语义制作的轻量映射。可复用其21段 AFM 表演与软方待机；先对照 DeskBot 自己的语义表，再决定哪些事件共用视觉动画，不照搬 AirBoat 的 `laughing/question/insert` 等别名。

保留两个状态语义但共用同一表演的机制：目录的 `aliases` 只负责视觉资源解析，调用事件名和优先级仍由应用保留。播放器需要识别 `authored_transitions: true`，并按19帧进入、完整主体、19帧返回播放。

DeskBot 若使用360圆屏，等比派生画面后量测裁切、字幕留位、资源大小和帧耗时。实机前验普通对话、触摸取消、休眠恢复和表达语义；身体动作继续由原事件触发。该表情支线不代表 DeskBot 固件已接入。
