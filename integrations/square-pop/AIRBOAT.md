# AirBoat Square Pop 接入卡

资源为本目录上层的 `assets/square-pop/square-pop.afm` 与 `manifest.json`。当前 AFM SHA-256：`1b835f35bd1cb71d08590f3027fba25d2892a8ec5bb7f56a5145e3be16ea359b`；AFM 与目录共 `5,328,324 B`。

此包有21份独立动画和29个语义节点。`aliases` 只复用视觉素材，事件语义及优先级仍独立：`laughing → happy`、`crying → sad`、`question/insert → silly`、`delicious/eat → funny`、`sleepy → tried`、`neutral → idle`。困倦与疲惫都能从各自节点触发，读取同一份疲惫表演。

播放器依据 `authored_transitions: true` 使用 `entry_keyframes`、`keyframes` 和 `exit_keyframes`。进入/退出各19帧，25 fps；完整结构为共同软方待机、形变进入、主体完整循环、形变返回。绘帧只更新显示，不重发语音、事件或身体彩排。

俏皮使用固定 `#28cf60` 背景。它的48帧眼白和瞳孔图层经逐像素回归保持不变；清除的是透明背景区的伪绿色装饰。

接入前，按当前固件分区测量目录/素材占用、逐行合成所需工作缓冲和每帧耗时。接现有 `app_response → app_expression_view / app_expression_player → GSP` 所有者；先编译候选，再分别记录安装、实时版本与实屏验收。回归：`tests/square-pop.cjs`、`tests/square-pop-art.py`、`tests/contour-review.cjs`、`tests/validate_release.py`。
