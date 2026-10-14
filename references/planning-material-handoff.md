# 规划阶段的必要资料交接（两条路线共用）

完整制作与恢复时，先实际读资料，再准备GPT与Image两份最小充分的资料集合。这个要求不随浏览器、CLI、聊天或模型改变。Codex替用户整理和填写清单，不要求用户写JSON。技能维护可用明确标注的合成材料验证此流程，不创建无关网页任务。

## 资料范围

| 接收方 | 必需内容 | 按项目需要附上 |
|---|---|---|
| 网页GPT规划 | 用户目标、受众、时长、页数/规则、事实与证据、已有结论和缺口、设计要求 | 论文选页/原文摘录、数据及单位/样本量说明、公式与符号解释、参考PPT代表页、真实模板、引用来源 |
| 网页Image | 当前单个主体、用途与使用页、造型/机制边界、风格、配色、材质/光照、比例/尺寸/背景、留白和禁止项；艺术字逐字原文 | 必要的产品/设备参考照、用户指定参考图、经过挑选的模板局部或风格样本 |

两份集合在规划阶段一起准备。Image的共用资料预案不单独触发生成；从GPT规划拆出每个素材任务时，补齐该元素的具体要求、选用相关资料ID，并随该任务实际送到图像入口。不能假设Image能看到GPT另一个聊天里的材料。相同聊天复用附件，也要在新任务中明确指向仍然可读的附件并保存观察。

只传本任务需要的资料。用户已指定用于网页版协作的项目材料按既有授权执行，不重复询问普通上传；不附带其他项目、无关个人信息或认证资料。大文件选页/分段，保留页码、图号、来源及必要上下文。看不清、无法提取或确实缺少的关键资料列为缺项；可先做不依赖它的本地工作，不能凭空补齐。没有外部证据的纯概念任务，可以只提供完整设计brief并在coverage解释，不强制虚构论文/数据。

PDF、图片、模板参考不能只给本地路径或文件名。文字资料可在消息中提供真实内容；视觉参考用实际附件。网页无法读取链接时下载允许使用的资料到项目内或提供可追溯内容摘录。二进制PDF不能冒充inline文本，截图也不能替代需要精确数值的源数据。

## 准备包

`auto_workflow.py prepare`首次创建`planning/material-selection.json`待填写清单。Codex完成资料阅读后更新清单；保留版本，`missing`只能在真实缺口已解决时清空。路径相对唯一项目根解析。

```json
{
  "schema": "web_material_selection_v1",
  "coverage": {
    "gpt": "已提供当前需求、核实过的论文方法/结果摘录及参考页；未完成的实验明确列为待验证。",
    "image": "已提供器件外观与蓝白设计brief；不绘制实验数据。"
  },
  "missing": [],
  "materials": [
    {"id":"brief","path":"outputs/research-ppt/sources/brief.md","targets":["gpt","image"],"purpose":"任务与设计边界","locator":"当前用户需求与设计决定","mode":"inline"},
    {"id":"evidence","path":"outputs/research-ppt/sources/evidence.md","targets":["gpt"],"purpose":"论证依据","locator":"原论文第3至5页，图2与表1","mode":"inline"},
    {"id":"device","path":"outputs/research-ppt/sources/device.png","targets":["image"],"purpose":"器件外观参考","locator":"用户提供照片，全图","mode":"attachment"}
  ]
}
```

这是格式示例，内容必须替换为真实项目资料。准备命令不操作网页、不生成发送证据：

```powershell
# 自动流程：更新资料选择后重建版本化规划包，查看返回的两个bundle路径。
python scripts/auto_workflow.py prepare --project-root <项目根> --workspace <工作空间>
# 独立规划入口也支持同一资料合同。
python scripts/plan_workflow.py packet --brief <brief.md> --profile research --project-root <项目根> --materials <material-selection.json> --out <新规划目录>
# 真正取得网页规划后，将Image所需材料写入每个独立任务。
python scripts/plan_workflow.py jobs --plan <deck_plan.json> --profile research --project-root <项目根> --materials <material-selection.json> --out <新队列目录>
```

每包包含`packet.json`、完整待发送`message.txt`、`files/`中的必要资料副本。规划目录分别生成`gpt-materials`与`image-materials`；每个图像任务生成`materials/`。`material_ids`可缩小当前元素使用的Image资料集合，必须包含理解该元素所需的设计brief和参考内容。省略则使用清单中所有Image条目，Codex仍应检查是否过多。

已有单元素任务可直接用`material_handoff.py prepare --project-root <根> --selection <清单> --target image --prompt <job/prompt.txt> --out <job/materials> --task-id <asset_id> --material-ids <相关ID...>`补资料。GPT对应target=gpt、task-id=gpt-planning、prompt为完整规划提示词。不能只提交原prompt跳过资料正文。

## 实际交接与观察

1. 用选定浏览器路线观察本任务页面。需要附件时，通过当前工具文档支持的文件选择/上传接口逐个附上`files/`文件；查看文件名和上传完成状态。CLI可用官方`upload`，但必须先操作已观察的上传控件。内置工具没提供上传能力时，切到具备能力的CLI；不能给图片路径代替图片。
2. 发送完整`message.txt`。保存实际发送内容与附件的页面观察到项目内`qa/`。发送动作前记录dispatch intent；结果不明先找回原任务，不能换路线重发。重复上传与已发送消息分别检查。
3. GPT回复先核对引用的资料/来源位置是否正确；Image先查看参考是否影响主体与样式。网页报告资料不可读时修复，不将空白回复或“收到”自述当作完整阅读保证。
4. 根据真实UI观察保存JSON，调用record。下面字段只是格式示意，不可拿示例文字充当证据：

```json
{
  "route": "builtin_browser",
  "session_url": "https://chatgpt.com/c/实际对话编号",
  "message_visible": true,
  "note": "实际观察到的发送情况及附件可用状态",
  "evidence_file": "outputs/research-ppt/qa/实际浏览器观察.txt",
  "materials": [
    {"id":"brief","mode":"inline","visible_note":"消息正文中的资料段位置与核对结果"},
    {"id":"device","mode":"attachment","visible_note":"已发送附件的真实文件名与完成状态"}
  ]
}
```

只列该包确实包含的全部条目；CLI路线写`playwright_cli`。不能把准备好的files、上传中的附件或本地文件存在写成已传。

```powershell
python scripts/material_handoff.py record --bundle <资料包> --observation <实际观察JSON>
python scripts/material_handoff.py check --bundle <资料包> --target gpt --session-url <实际任务URL>
python scripts/receive_web_plan.py --reply <真实助手回复> --evidence <真实观察> --session-url <实际任务URL> --model <实际型号标签> --materials <gpt-materials> --out <新接收目录>
```

`record`不执行上传，只登记观察。哈希只检查版本一致性，不能独立证明网页读取或模型身份。材料/提示词/附件/观察被改动，或换聊天/任务，校验会失败，必须重新准备版本并实际交接。仅更换传输工具、仍在同一聊天时，可核对原来的发送记录复用，不能盲目重发。

## 验收与旧任务迁移

`receive_web_plan`要求本次规划对话的GPT资料交接记录；`asset_job event submitted`要求当前图像对话和asset_id的Image资料记录。`web_task.ps1 Submit`只自动发送无附件的完整资料消息；有附件时改用实际UI上传并发送，不能静默漏掉附件。`delivery_review.web_planning.material_bundle`登记接收器provenance中的资料包路径；`delivery_gate`检查GPT包及每个入稿Image任务的资料、消息、观察哈希与目标对话。

旧任务没有资料交接记录，不能补写虚构证据。先回原聊天核查真实发送内容和附件，能够真实补齐记录才迁移；否则发补充资料并取得修订规划/素材。无需网页生成的任务不强行产生Image发送记录，但仍准备必要Image上下文并说明不需要生成的理由。用户明确离线只允许如实交付离线范围，不宣称已完成网页交接。
