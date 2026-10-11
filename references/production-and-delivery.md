# 从制作到交付：内容、素材和视觉的闭环

完整制作与重设计任务读取本文件。局部改字沿用既有计划，复查受影响页即可；不要为微调强制重新生成素材。

## 先确定可见的设计目标

根据用户模板或实际查看的参考图，记录配色、字体、留白、主视觉比例、图文关系和页面节奏。商业宣传图只作构图参考，不抄其内容、不把宣传图直接铺成页面。不能用“高端、大气”替代具体目标。

建立三张代表页：封面、最关键的技术/机制页、证据最密集的结果页。先渲染并查看，再将设计延伸到全篇。避免只先做好最容易的封面。

不同内容应有相应表达：方法用原生结构与局部实物/概念元素，结果用真实证据和可编辑解读，对比用共用尺度，结论用明确的发现与边界。允许必要的复杂度，但不按对象数、图片数或字数机械判定质量。不要将每页都做成同一种三卡片布局。

## 内容不能只剩目录与口号

规划每页写出具体问题、论点、支持材料、推理和讲稿。每个content_block至少提供text、data_ref或source_ref，不能只有“研究背景”“创新点”等标签。材料不足时记录缺口或向用户索取关键材料，不编实验数据、不编引文、不用通用套话凑页。

每页增加layout_family和visual_rationale，说明构图如何帮助读者理解。连续单调页需要重排视觉重心；全篇至少比较封面、方法和结果的构图是否真正不同，特定模板必须重复时写明理由。

## 真正执行网页版单元素生成

asset_requests中每项写request_id、kind、purpose、single_subject_prompt。默认decision为generate_web。依次执行现有asset_spec/asset_job及web_task流程：准备 → 实际提交 → 等待原对话结果 → 下载 → 技术与视觉检查 → placement → manifest → compose → 核对最终PPT中的对象与哈希。先完整阅读web-single-element.md和browser-connection.md，按实际可用入口执行；不要把任务规格或连接成功当成素材生成成功。

assets/asset_manifest.json每项补充request_id，对应唯一请求。不要只给封面生成一个装饰，然后忽略其他页已经规划的需求。保持每次只生成一个元素，不用整页图、不用拼贴后裁切。已有适用资产可以复用并追溯，不因重复使用而重新计为新生成。

确实更适合原生对象或真实来源图时，request的decision可为native_or_source，同时记录decision_reason与replacement_object；检查最终页存在该对象。不要为通过验收添加无意义生成图；结果页以证据图为主。

网页连接失败时记录具体步骤和错误，继续不依赖连接的本地工作，未完成项保持draft。用户明确选择离线时记录原话和原因，不擅自替换生成渠道。实际型号不可见时记录未核实，不将请求的Image 2.5当成已验证引擎。

## 最终作品证据核对

初始化产生qa/delivery_review.json空记录，默认未验收。完成最终组装后按实际页面顺序补充：

- 顶层pptx_sha256；web_planning的session_url和实际response_file。离线例外使用offline_user_authorization.instruction与reason。
- 每页slide_number、render_file、render_sha256、rendered_from_sha256。先渲染、实际查看后填记录；修改PPT后旧审查失效，需要重渲染并更新。
- content_review、visual_review、evidence_review分别包含status和具体note。内容检查解释是否空洞；视觉检查记录层级、图文关系、留白、遮挡、对比及与参考的差距；证据检查来源与结论边界。没有科学论断的封面也应说明该项为什么通过。
- unresolved_issues列出尚未处理的问题；全部解决后才设为空数组。没有生成需求时填写no_generated_assets_reason，构图需要高度重复时填写layout_repetition_reason。

```powershell
python scripts/delivery_gate.py --workspace <workspace> --pptx <final.pptx> --out <workspace>/qa/delivery-gate.json
```

返回非零表示证据未闭环，只能交付草稿及具体缺项。即便返回零，也只是记录、素材、页数和版本对应完整，不能自动证明美观和事实正确。仍须运行字体、编辑性和来源审计。

交付时说明实际使用了哪些网页素材、哪些页已查看、哪些问题尚未完成。禁止声称“达到商业级”却不给代表页预览或缺乏实际视觉评估。不要为通过检查而编造截图、网页回复、审查意见或用户授权。
