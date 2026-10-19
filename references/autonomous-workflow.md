# 少提示词制作与恢复

适用于“做一份PPT”“继续”“优化这份汇报”等简短请求。Codex应自行执行下一步，不要求用户编写规划包、JSON、文件路径或重复提醒质量要求。

## 自动启动

在当前项目根运行 `scripts/start_ppt.ps1` 即可，参数均可省略。需要传达当前对话中的要求时用 `-Request`；已有明确参数则直接传入，不要求用户重述。

```powershell
& scripts/start_ppt.ps1 -Request '把现有材料做成15分钟科研汇报，详细解释公式'
```

入口先验证Python依赖；缺少核心包时只在当前项目的`.ppt-runtime/deps`安装requirements.txt，不修改系统Python或其他项目。随后调用 `auto_workflow.py prepare`，再刷新本任务Bridge profile。Codex继续调用Python脚本时沿用本项目`.ppt-runtime/deps`作为PYTHONPATH；部署失败保留错误并报告，不以控制器启动成功掩盖依赖缺失。Codex随后立即按启动合同操作实际浏览器，验证登录、选择器及图像入口。读取 `planning/automation-input.json` 中的 `planning_packet` 路径，使用自动生成的完整规划包。先读[必要资料交接](planning-material-handoff.md)，填好自动创建的material-selection.json再运行prepare生成GPT/Image资料包；planning_packet本身仅为提示词，实际发送planning_material_bundle里的message.txt及必要附件。不能把准备完成或状态输出当作任务结束。

## 自动补齐需求

优先级是明确参数、当前请求中可识别的要求、该工作空间上次保存的需求、材料文件名、默认值。自动保存每个字段的来源与历次用户要求；恢复任务时保留上次参数和已有素材任务。

- 默认科研汇报、20分钟、同行与课题组受众、16:9。
- 默认beihang-blue贯穿主题，自动带入本地模板源素材与身份预留区，详见[beihang-theme.md](beihang-theme.md)。无需用户再次提醒北航元素。旧工作空间启动时迁移主题合同并修订受影响布局；主题切换不清空已派发素材或网页证据。绿园/银杏可用-ThemeProfile选择；明确其他学校或关闭主题用none，并以-ThemeReason记录用户指令。
- 每页至少40个独立对象。脚本检测缺口后自动提出逐个网页版素材请求，Codex结合页面论证确定具体主体和摆放位置，将其加入实际规划并执行生成、审核和组装。不要只报告缺口后停止。修订后重跑计数与视觉检查。
- 请求中出现国奖/奖学金、挑战杯、创新创业/创业路演时选择对应场景；已有工作空间保持原场景，除非新要求明确改变。
- 题目优先使用《书名号中的题目》；否则沿用已有题目。新项目只有一个PDF/PPTX候选时可用其文件名作草稿题目，否则暂用项目名。
- 自动列出项目顶层与指定材料目录（sources/materials/input/inputs/资料/材料/参考资料）的候选文件元数据，上限200项；不自动递归读全仓库、不读认证文件、不上传文件。
- Codex按相关性实际阅读候选材料，核实题目、证据、图表和公式，再将适合公开的必要内容加入网页规划任务。文件清单不是已读内容，也不是科学事实。
- 配色、字号、布局、代表页、证据审查、逐个素材、原生数据对象、LaTeX与字体要求由规划包和现有技能自动带入，不等待用户逐项提醒。

题目措辞、默认时长和配色可先用于草稿，不必停下来问。只在关键事实缺失、材料之间的选择会实质改变论证，或存在多个工作空间且对话也无法确定目标时询问。先完成不依赖答案的工作。事实、实验结果、引用、用户授权和网页观察不能用默认值补造。

## 根据状态继续执行

已有主规划后，优先运行`auto_workflow.py advance --workspace <workspace>`完成可恢复的本地步骤，再按next_action继续真实操作。它会准备当前阶段缺失任务、输出内容/几何/美术报告；不会自动发送或填写通过。代表页与全篇分阶段执行见[art-direction-and-staged-review.md](art-direction-and-staged-review.md)。

advance同时输出按页定位的`revision-tasks.json`和可读的`revision-tasks.md`，路径见返回的revision_tasks。先核对证据缺口，再处理几何错误、内容/可读性、美术一致性和必要叠层复查；优先级只是修订顺序，不是已确认的错误等级。报告包含对象ID、具体观察与下一步动作。重新运行依据当前规划重算，不自动将消失的信号标成视觉通过；实际修订与查看记录保存在对应审查版本，不直接修改生成的任务单来通过检查。

```powershell
python scripts/auto_workflow.py status --workspace <workspace> --write
```

读取 `qa/workflow-status.json`，按 `next_action` 继续当前步骤：

| 状态 | Codex应执行 |
|---|---|
| observe_browser_and_check_connection | 实际观察、登记证据并Check；准备本地资料可并行进行 |
| prepare_planning_materials | 实际读资料，填写material-selection.json中GPT与Image两份范围；运行auto_workflow prepare生成版本化资料包 |
| transfer_planning_materials | 上传必要附件并发送完整message.txt，保存真实观察并登记material_handoff record |
| receive_actual_web_plan | 核对已交接资料，通过receive_web_plan接收真实回复，不能重复发送 |
| adopt_received_plan | 真实网页回复已接收但尚未进入工作空间主规划；验证来源哈希与几何后执行`auto_workflow.py adopt-plan --workspace <workspace> --received <workspace>/planning/received-vN` |
| select_received_plan_for_adoption | 存在多个已接收版本；按本次对话与版本证据选择，不能凭文件时间猜测 |
| recover_original_planning_conversation_do_not_resubmit | 规划发送超时且结果不明；恢复原任务页确认消息与回复，禁止在新对话重发；设计派发记录位于planning/web-design-dispatch.json |
| repair_received_plan | 根据具体错误修订规划，不重做已通过的素材 |
| repair_plan_geometry / repair_visual_plan | 修正具体几何或美术字段错误，再advance，不用自动移动对象掩盖问题 |
| prepare_asset_materials | 实际检查并补足当前素材所需资料，再advance |
| continue_representative_assets | 只推进代表页素材的真实网页生成、下载、审查与摆放 |
| render_and_review_representative_pages | 原生组装并渲染代表页，提供实际渲染索引创建审查板，实际查看后记录 |
| render_and_review_full_deck | 对最终版本渲染全篇并逐页审查，更新full审查记录 |
| inspect_orphaned_dispatch / inspect_interrupted_asset_preparation | 恢复已有发送意图或半完成目录；不覆写、不重发 |
| repair_asset_inventory / resolve_duplicate_asset_queues | 修复索引或实际比较候选，用select-job保存具体选择及理由；旧发送结果不明时先恢复，不能按时间猜测 |
| continue_asset_jobs | 按asset_actions逐个推进，实际查看图片后才能review |
| assemble_native_deck_then_render_and_run_delivery_gate | 原生组装、代表页与全篇渲染检查、运行交付检查 |
| repair_delivery_gaps | 修复实际delivery_check指出的缺项 |
| repair_recurring_beihang_theme | 修复规划section与主题合同，添加/更新四个贯穿对象，处理预留区冲突，再渲染与核验 |
| supplement_individual_web_elements | 将element_density中的缺口提案按本页内容具体化并登记到规划，逐个网页生成、组装、重渲染 |
| close_task_bridge_and_deliver | 关闭本次控制会话，交付已核验版本与来源 |

队列缺失时先生成任务；prepared仅代表待提交；submitted和submission_unknown先检查原会话，绝不自动重发；received必须实际视觉审查；accepted再placement与compose。未知或阻塞状态调查原因，不无界重试。重复request_id队列需确定保留版本，不能自动选择最新版本覆盖派发记录。

新准备素材带`plan_request_signature`，绑定主体请求与图像相关的主题、颜色、材质/光照和背景；仅修改原生正文的字号不会令图片任务失效。即使只有一个任务，出现plan_changed也必须实际对照新规划复查。素材仍适用时用select-job选择原目录并具体说明复查后的复用理由；不适用时明确建立新版本。不得修改原spec或伪造新生成记录。delivery_gate检查原始绑定或当前复用记录的目录、规划签名及原规格哈希，实际图片对象和视觉审查仍须分别通过。历史无绑定任务保留原有检查，不自动补写历史证据。

接收网页规划时可给`receive_web_plan.py --workspace <workspace>`，在来源哈希与几何检查通过后自动写入`planning/deck_plan.json`；接收目录和原始回复保留。已有不同主规划不会被覆盖。接收器同时输出`content-plan-audit.json`，状态器把内容浅薄、缺来源定位与缺讲稿列为`content_plan_review`信号；Codex实际读材料补足，不能用套话消除信号，也不将启发式报告当作事实核验。

状态器本身不操作浏览器、不调用模型、不授予权限，也不编写通过审查记录。它报告待执行动作。只有实际delivery_gate通过才产生review_evidence_complete，终稿审美与事实仍需真实检查。正式在线任务遵守原Bridge授权范围，不因自动化增加公网、shell、写权限或后台启动。
