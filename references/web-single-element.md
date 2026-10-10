# 网页版单元素生成

此流程是“Codex 准备任务 → 当前会话自动操作真实网页 → 保存原始素材 → 校验与人工视觉评审 → 修改 PPT 源”的能力。`asset_job.py` 处理本地状态，不能单独驱动浏览器；不要把任务包生成成功称为网页版调用成功。

## 自动触发与范围

用户请求局部装饰、艺术字或概念插画时，在制作/微调当前 PPT 中自动选择这个流程。简单线条、箭头、流程节点、表格和常规图表优先原生对象。一个请求只生成一个独立主体；需要多个不同组件就拆成独立任务，不能通过一张拼图后裁切来冒充独立素材。

用户指定网页时保持网页路径；不可悄悄切换为内置 image_gen 或 API。网页执行失败就保留任务和阻塞原因；只有用户选定替代途径才使用替代。模型名在页面未显示时记为 `unverified`，聊天模型名称和模型自述不能作为图像引擎证据。

## 本地准备

可以先用 `scripts/asset_spec.py` 生成风格一致的单元素规格。支持 orbital_accent、spacecraft_concept、thermal_concept、section_wordart 四个预设；最后一个必须提供 --exact-text。例：`python scripts/asset_spec.py --preset orbital_accent --asset-id orbit-v1 --slide-id slide1 --object-id orbit-accent --out orbit.json`，再把 orbit.json 交给下方 prepare 命令。--palette 可覆盖主题。热红外预设是概念图，不能替代实测图；艺术字须保留原生语义文字。预设与 prepare 成功只代表任务包准备完成，不能称为已调用网页版或获得指定图像型号。

新建 PPT 工作空间必须先按 [bridge-assisted-ppt.md](bridge-assisted-ppt.md) 初始化连接，并由 GPT-6 在逐页规划中提出候选素材。Codex 仅接受确实适合图像生成的单主体请求，再分别建立任务。

使用 JSON 规格和任务目录。必填 `asset_id`、`element`、`kind`、`slide_id`、`object_id`。`kind` 为 ornament/concept/art_text/icon/cutout；艺术字须填 `exact_text`。可选 style/palette/aspect/transparent/min_width/min_height。这些只是要求，不是网页 API 参数。

任务通过 review 后，把该任务目录作为独立条目登记到 `assets/asset_manifest.json`，最终使用 `scripts/compose_elements.py` 逐元素写入 PPTX。每个生成结果只能对应一个图片对象；不得生成一张多元素图再切割复用。

```powershell
python scripts/asset_job.py prepare --spec element.json --job asset-jobs/atom-v1
```

输出 prompt.txt、job.json。若任务目录已经存在，拒绝覆盖，换一个版本目录。提示词自动限制单个主体、留安全边缘、无页面/正文/拼图/水印，保留用户明确的艺术字文字。审阅任务包，非敏感任务按已有授权直接发送；未发表科研材料或私人参考图的上传需遵守当前会话对指定资料和目的地的授权。

## 浏览器执行

优先使用当前可用的 `cua_repl` API；其启动失败并完成一次重试后，可按 [browser-connection.md](browser-connection.md) 切换到官方 Playwright CLI，通过已获用户授权的 CDP 或官方扩展接入真实网页。每种工具遵守自身文档，不能混用引用编号。不使用 cookie 抽取、隐藏内部端点、未经文档允许的下载请求或复制用户浏览器配置。

1. 获取浏览器和标签页清单，绑定已登录的 ChatGPT 页面。优先复用本任务专用会话，不在用户无关聊天里发送任务。页面观察失败最多一次重置/重试，仍失败就记 blocked_browser，停止重复提交。
2. 根据新鲜的可访问树选择图像生成入口；页面不存在图像入口或指定型号时，记录具体阻塞。不能猜坐标或盲发。若 UI 只显示“创建图片”而无 image-2.5，记录 engine unverified，并报告无法满足精确型号保证；按用户是否允许一般网页图像生成决定继续。
3. 发送 prompt.txt，一次只发一个任务。记录 session_url、提交时间、可见模型证据。若已有任务提交记录，先查看原会话是否已生成，禁止重试导致重复消耗。页面提交是否成功不明时记录 submission_unknown，不自动重新提交。
   官方CLI路径可使用 web_task.ps1 Submit，带已观察的SessionUrl。只有退出成功且网页出现消息后登记submitted；dispatch-intent标记阻止重发。不得无条件将后续event命令接在可能失败的提交命令后。
4. 生成可能耗时数分钟；检查可见状态，间隔观察，并每分钟以内给出必要进度。没有完成图像时不点击“重新生成”。登录/验证码/额度限制按可见页面处理；不绕过验证或购买额度。
5. 查看实际生成结果，确认单一主体、文字、风格、科研语义。按当前浏览器文档支持的下载控件取得原始文件。若工具不支持文件落地，记录 blocked_download，保留页面结果并报告缺少下载能力，不能以网页截图替代原始素材。
6. 用 `asset_job.py receive` 保存已下载的原文件并检查尺寸/透明通道，随后在 `view_image` 看本地文件。脚本不能判断主体数量、艺术字准确度或机制真实性。真实视觉/科学检查后使用 `review`；不合格用新版本任务与明确修改提示重做，同一目标至多两次自动修正，此后保留结果并与用户讨论。
7. 改写当前 PPT 的 asset_plan/outline/实际源文件，保留 slide_id/object_id 和旧版本，替换局部图。注意透明素材可能有大面积留白，视觉上确认裁切不伤主体。原生标题、正文、说明不能变成图片。

## 本地状态命令

可选 `visual_context` 字段包含 slide_background、lighting、material、placement、avoid，使提示词继承实际页面设计。

通过 review 后执行 `placement --job <目录> --box X Y W H --canvas 13.333 7.5 --min-ppi 180`，得到 placement.json。按原制作引擎修改源并重建后，执行 `event --status integrated --job <目录> --pptx <实际文件> --note <检查记录>`；会核对唯一 picture 的对象名与哈希。具体美观规则见 [visual-assets.md](visual-assets.md)。

```powershell
python scripts/asset_job.py event --job asset-jobs/atom-v1 --status blocked_browser --note "浏览器连接失败，尚未提交"
python scripts/asset_job.py event --job asset-jobs/atom-v1 --status submitted --session-url "https://chatgpt.com/c/实际会话" --engine unverified --note "页面显示生成中，图像型号未显示"
python scripts/asset_job.py receive --job asset-jobs/atom-v1 --file "实际下载.png"
python scripts/asset_job.py review --job asset-jobs/atom-v1 --verdict accepted --note "已查看本地素材：单主体，留白合适，无正文，语义核对通过"
```

`receive` 不下载网页、不编辑图片、不剥离背景。透明要求不满足时返回技术检查失败。通过 review 仍不等于已嵌入 PPT；修改实际 PPT 源并重建/检查后才使用 event 的 integrated 状态。最终说明真实引擎可见性、网页生成是否完成、技术/视觉检查、放置对象和剩余限制。
