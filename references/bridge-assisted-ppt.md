# GPT-6 + GPT Image 2.5 + 本地脚本的强制工作流

本流程用于新建 PPT 项目。目标是让网页端模型承担其擅长的规划与视觉素材生成，同时保持最终幻灯片的对象级可编辑性、证据边界和可审计性。

## 1. 初始化并连接

在项目根目录执行：

```powershell
& scripts/start_ppt.ps1 `
  -ProjectRoot <项目根目录> `
  -Workspace <新建的PPT工作空间> `
  -Title <汇报题目> `
  -Profile research
```

统一入口为scripts/start_ppt.ps1，新建与恢复均刷新任务连接。内嵌bridge通过ppt_bridge.ps1配置精确项目profile（Tunnel none），随后由当前Codex使用浏览器工具完成实际连接与模型观察；严格顺序见[bridge-startup-contract.md](bridge-startup-contract.md)。不使用上游Auto默认公网路线，不将本地MCP健康当作网页成功。连接记录保存在bridge-connect.json。

维护/离线测试不调用制作启动入口。用户明确要求离线制作时记录其授权及缺项；start_ppt.ps1不提供绕过在线验收的跳过开关。

## 2. 职责边界

初始化支持`-Profile scholarship|research|challenge|innovation`，分别面向国奖、科研、挑战杯和创新创业。默认research。生成的规划任务包含场景叙事与候选构图，实际模型回复仍需浏览器取得。需要详细坐标候选可用plan_workflow.py packet。

| 责任方 | 必须负责 | 禁止代替其他层完成 |
|---|---|---|
| 网页版 GPT-6 | 叙事结构、逐页规划、信息密度、讲稿、证据缺口、公式讲解要求、审稿与批评 | 不生成 PPTX，不设计成一张完整幻灯片图像 |
| GPT Image 2.5 | 每个任务只生成一个独立小元素：`ornament`、`concept`、`art_text`、`icon` 或 `cutout` | 不生成整页、完整信息图、图表、表格、公式、实验结果或多元素拼贴 |
| Codex 本地脚本 | 原生标题正文、引文页码、图表表格公式、节点连接线、版式、逐元素插入、渲染与 QA | 不把整页截图当作最终页，不把不可编辑内容伪装成可编辑对象 |

## 3. 规划到素材

1. 按[planning-material-handoff.md](planning-material-handoff.md)在规划阶段实际阅读并准备GPT/Image必要资料。用当前选定的内置浏览器或CLI上传附件，发送GPT资料包的完整message.txt并保存真实交接观察。
2. 用receive_web_plan.py接收真实规划回复（携带--materials），保存deck_plan.json和来源记录，不手写网页回复。
3. Codex 审核每个 `asset_requests`：只有确需生成且适合单主体图像的请求才进入后续任务。
4. 每个通过的请求单独建立一个带Image资料包的 `asset_job.py` 任务；在实际图像入口送达该任务的完整message.txt和必要附件，记录真实交接后再登记submitted；不得把多个元素放进同一生成任务后裁切。
5. 在 GPT Image 2.5 中生成透明背景或易于独立排版的素材，执行视觉审查和哈希审查。
6. 只有 `accepted` 或 `integrated` 的任务可以进入清单。

## 4. 元素清单与组装

`assets/asset_manifest.json` 中的每个条目必须独立：

```json
{
  "kind": "icon",
  "request_id": "slide-04-sensor-icon",
  "slide_number": 4,
  "job_dir": "../asset-jobs/slide-04-sensor-icon"
}
```

组装命令：

```powershell
python3 scripts/compose_elements.py `
  --pptx src/deck-native.pptx `
  --manifest assets/asset_manifest.json `
  --out build/deck-composed.pptx `
  --report qa/composition-report.json
```

脚本逐项读取已审核的 `job.json` 与 `placement.json`，验证种类、状态、位置、面积、文件哈希和对象名，然后分别调用 `python-pptx` 插入。单个生成素材默认不得覆盖超过页面面积的 55%。

`job_dir` 相对元素清单所在目录解析。placement 必须由 `asset_job.py placement` 生成；其对象标识、素材路径和哈希必须与已审核任务一致。组装时保持图片原始宽高比，跨页对象名也不得重复，PPTX 与审计报告必须使用不同输出路径。旧 placement 被拒绝后应重新计算，不能手改哈希绕过校验。

## 5. 最终 QA

完整制作还须按 [production-and-delivery.md](production-and-delivery.md) 执行delivery_gate，逐项核对所有素材请求和最终版本的逐页审查。初始化或浏览器连接成功不等于素材已生成；空元素清单也不代表视觉目标已满足。

- 渲染所有页面，检查遮挡、裁切、对比度、文本溢出和留白。
- 确认标题、正文、公式、数据图、表格、引文与页码仍为原生对象。
- 确认每个生成元素都是独立图片对象，名称为 `<slide_id>/<object_id>`。
- 检查 `qa/composition-report.json` 中 `whole_slide_generation_used` 为 `false`。
- 运行技能既有的 PPTX 结构检查与逐页视觉检查。
- 任务结束后按 bridge 技能要求断开当前连接并清理仅本次会话需要的临时服务。
