---
name: chinese-research-ppt
description: 制作、优化和逐页打磨中国科研汇报的可编辑 PPTX；新项目自动初始化网页版 GPT-6 规划与 GPT Image 2.5 单元素素材流程，最终由本地脚本逐对象组装并检查证据和编辑性。
---

# 中国科研汇报 PPT

## 完整制作任务的完成条件

完整制作或重设计时，先读 [references/production-and-delivery.md](references/production-and-delivery.md)。内容必须有具体论证与来源，构图围绕内容变化，素材需求必须实际生成、审查和入稿；不能用通用文字、空素材清单或单一三卡片模板完成全篇。先查看封面、关键技术页和密集结果页的渲染，再推广全篇。

交付前运行 `scripts/delivery_gate.py`，核对逐页规划、网页生成任务、最终对象哈希及最终版本的逐页视觉审查。失败时保持草稿状态并明确缺项，继续完成可执行的修订。脚本通过只表示记录闭环，不代表自动判定美观；不得用自填审查记录代替实际查看渲染。

## 强制初始化流程

每次在新活跃会话启动制作或恢复制作，必须先读内嵌 [bridge/SKILL.md](bridge/SKILL.md)、[bridge/USER_POLICY.md](bridge/USER_POLICY.md) 与 [references/bridge-startup-contract.md](references/bridge-startup-contract.md)，运行`start_ppt.ps1`，然后立即使用浏览器工具验证本任务登录、GPT-6选择器与图像入口。用户已要求此会话级自动流程，不重复询问普通连接准备；登录、公开隧道与权限升级仍遵循其授权边界。缺失或过期的连接合同不能通过在线delivery_gate。脚本退出0只代表对应步骤成功，不能笼统宣称两个模型已连通。

新工作空间由start入口调用init_ppt_session.ps1创建；随后刷新内嵌bridge项目profile，并由当前Codex会话执行实际网页连接与验证。完整流程见 [references/bridge-assisted-ppt.md](references/bridge-assisted-ppt.md)。失败保留工作空间和bridge-connect.json，保持草稿。`-SkipWebConnection`仅限测试或用户明确离线；不能用它绕过正式在线交付检查。

网页版 GPT-6 负责叙事结构、逐页规划、信息密度、讲稿、证据缺口和全稿审查。GPT Image 2.5 只生成一个任务对应的一个独立小元素，允许类型为 `ornament`、`concept`、`art_text`、`icon`、`cutout`。严禁生成整页 PPT、完整页面布局、整页信息图、带标题正文页脚的合成画面、图表、表格、公式、实验结果图，或生成多元素拼贴后裁切。

Codex 本地脚本必须负责原生标题正文、引文页码、图表表格公式、流程节点与连线、最终版式，以及把每个已验收元素作为独立图片对象写入 PPTX。GPT-6 的素材建议必须由 Codex 筛选；每个通过的元素分别建立任务、审查并登记到元素清单，再由 `scripts/compose_elements.py` 逐项插入。

目标是论证清楚、证据可查、投影可读、对象可编辑，并支持人与模型持续修改。用户的学校模板、时间限制、评审通知优先于默认建议。

## 制作与交互

提高视觉丰富度或完整重设计时，读 [references/visual-composition.md](references/visual-composition.md)，使用扩展布局库，将主证据、局部放大、原生解读、同口径比较与单元素素材组合。网页规划须给出design_system、代表页及每页视觉层次；复杂程度服务于论证和可读性，不用装饰数量替代设计。

网页规划取得后，必须按 [references/web-plan-handoff.md](references/web-plan-handoff.md) 使用`receive_web_plan.py`接收真实助手回复并保留观察证据，再拆分独立素材任务。解析或布局检查失败则修订规划，不直接进入全稿组装；素材任务按实际状态恢复，提交不明时禁止自动重发。

国奖答辩、科研汇报、挑战杯和创新创业路演，先读 [references/chinese-defense-and-competition.md](references/chinese-defense-and-competition.md) 选择叙事与构图方案，并查用户当届规则。使用 `plan_workflow.py packet`准备网页版GPT-6规划任务；实际取得回复后，使用`jobs`拆成逐个元素任务。新增图标、产品概念、飘带和字标预设见asset_spec；不能把队列准备称为网页生成。Python原生图表和表格按 [references/python-native-data.md](references/python-native-data.md) 使用native_data.py，保留输入数据和嵌入工作簿。

1. 确认场景、受众、时长、材料和学校/项目要求；已有信息不再询问。资料不足时只问会改变论证的关键问题。阅读 [references/research-and-design.md](references/research-and-design.md) 选择场景主线。
2. 建立每页的 `slide_id`、核心问题/结论、来源、证据图、讲稿、预计讲述时间。结论标题必须受证据支持，未完成的研究用问题或假设标题。参考文献和研究图不能被装饰掩盖。
3. 先做代表页：封面、方法、结果；给出预览让用户选择风格，或在偏好已明确时直接继续。形成少量稳定设计规则，不强制所有页套同一种布局。
4. 建立可重建源文件，保存稳定 `object_id`、位置、样式、数据、来源和锁定状态。用户说“第3页右侧图放大”，先解析成明确对象和局部变更；只有对象歧义会影响结果时询问。保留旧源文件与修改记录，更新关联标题/讲稿和证据说明。
5. 重建受影响内容，渲染检查受影响页及相邻页；最后检查整体节奏。用户可在任何阶段修改内容、图表、配色、素材、间距，不要求一键成型，不在每个微调后增加审批。

## 复用已有技能

- 有 `presentation-skill` 工作区时，沿用其 outline、证据计划和 deck_ir，修改源文件，使用其 build/finalize/repair 流程，不能用本技能样例生成器替代现有源文件。
- 论文/文献汇报进入本包的论文模块：读取 [paper_manifest.json](paper_manifest.json) 及其always_load，只加载识别出的paper_type参考。遵循 [references/paper-workflow.md](references/paper-workflow.md) 的九步流程、术语表、证据图提取和修正验收。已有论文PPT仅做局部修改，不重新摄取整篇。
- 新建独立 PPT 使用 `pptx` 的 PptxGenJS，或 `nature-paper2ppt` 允许的 python-pptx，保留生成源文件。
- `scientific-slides` 的论证和演讲建议可以参考；其整页图片/PDF 默认路线与本任务编辑性要求冲突，不采用。
- 新建工作空间必须按强制初始化流程连接网页版并让 GPT-6 承担规划；已有工作空间的局部修改可复用已记录的有效会话。连接失败则明确报告，没有网页版回复不能宣称已获规划，随后仅按用户授权继续本地工作。

## 论文来源与验收工具

`paper_source.py intake`读取指定PDF页或文本并保存可追溯源包；`crop`仅提取指定证据区域，裁剪状态默认为pending，实际查看后才能通过。PDF功能使用可选requirements-paper.txt。用 `audit_paper_deck.py`按显示页序检查结构和可选paper-plan来源记录，再结合编辑性、字体和渲染检查。详见 [references/paper-evidence-and-quality.md](references/paper-evidence-and-quality.md)；整合依据与取舍见 [PAPER2PPT_INTEGRATION.md](PAPER2PPT_INTEGRATION.md)。

## 编辑性边界

当需要统一中西文字体、LaTeX公式或提升图案与艺术字表现时，阅读 [references/visual-system-and-math.md](references/visual-system-and-math.md)。按用户要求同时设置中文与西文字体；公式保存LaTeX源并优先转为Office原生公式。实际接入生成资产后再称已使用艺术字。运行 `scripts/typography_check.py`，同时检查字体冲突和缺失声明；需要修复现有PPT时用 `--normalize-to` 写入新文件，保留数学节点与非字体部件。修复后结合代表页与全篇渲染检查，不能把字体审计通过等同于视觉合格。

涉及截图重建、复杂流程图、对象定位或局部文字精修时，阅读 [references/editable-refinement.md](references/editable-refinement.md)。使用 `scripts/deck_objects.py inspect` 按实际显示页序建立对象清单；简单文字和元数据修改可使用带哈希与旧值预条件的 patch。清单还提示未绑定连接线、较小的折算字号和图片替代文本缺失，警告需结合渲染人工判断。

标题、正文、脚注、页码、普通表格、常规图表、流程节点与连线使用 PowerPoint 原生对象。常规图表保留嵌入数据。公式优先 OMML/原生公式；工具不支持时保留 LaTeX 源和替换入口，并披露不可直接编辑的部分。

显微图、照片和文献原图允许作为证据图使用；不能凭像素猜数字重画结果，不得改动比例尺或隐去必要坐标/图例。复杂图可保留原图，但标注、解读和来源文字独立可编辑。

禁止把一整页 PPT 渲染图、截图或生成图作为内容页。大面积证据图不等于整页截图，检查工具只能发出需人工判断的警告。不得以原生对象数量或编辑率百分比作为唯一合格依据。

## 局部 AI 素材

网页工具失败或需要恢复连接时，阅读 [references/browser-connection.md](references/browser-connection.md)，使用经实测的官方 Playwright CLI 替代连接。接入、发送、生成和下载分别验证；等待必需的浏览器人为授权时继续本地准备，不虚报网页版已连通。

当用户要求网页版 image2.5/image-2.5 单元素生成，或正在制作的 PPT 确实需要局部位图素材时，阅读 [references/web-single-element.md](references/web-single-element.md)，可先用 `scripts/asset_spec.py` 生成主题一致的单元素规格，再用 `scripts/asset_job.py` 准备任务、检查下载素材并登记替换位置。这个流程由当前 Codex 会话通过浏览器工具执行，不是后台服务；不需要开启本地文件 bridge 或公开隧道就能发送非敏感提示词。已有授权覆盖同范围生成和微调，不重复询问。

网页版 image-2.5 的实际可用性需在 UI 核实；仅用于装饰、局部概念插画或艺术字。记录模型（可见时）、提示词、源文件、版本、透明背景、使用页和替换对象。提示词写清：单个组件、无页面布局、无正文、透明背景/所需背景、色系、留白和输出比例。中文艺术字保留可编辑语义文本；科学机制插画必须逐项核对，不作实验事实或实测结果。

## 验收

局部生成素材的配色、光照、尺寸和视觉验收按 [references/visual-assets.md](references/visual-assets.md) 执行。素材通过 review 后，使用 `asset_job.py placement` 计算比例和有效分辨率；将任务登记进 `asset_manifest.json`，再由 `compose_elements.py` 逐个插入为独立 picture。图片生成不能取代原生排版。integrated 状态必须提供实际 PPTX 核对对象名和图像哈希。

运行对应制作技能的结构验证和渲染检查，再运行 `python scripts/audit_editability.py deck.pptx --out editability.json`。这个脚本只证明包内对象与数据部件存在，不能证明事实正确、图表数据可用或视觉美观。所有结果页人工核对来源、单位、样本量、误差条/检验含义及结论边界；未提供统计信息不得自动补全。

交付 PPTX、可重建源、数据/来源、实际使用资产和 QA 记录。写明实际查看过哪些渲染页、哪些检查未完成；无可靠渲染器时不得宣称视觉验收通过。操作演示至少包含改一个中文标题、更新图表数值、改表格单元格，重建后再次检查。样例脚本 `scripts/demo.py` 仅用于能力演示，所有数值标注为示例。
