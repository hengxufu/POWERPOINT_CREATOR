# GPT-6 + GPT Image 2.5 + 本地脚本的强制工作流

本流程用于新建 PPT 项目。目标是让网页端模型承担其擅长的规划与视觉素材生成，同时保持最终幻灯片的对象级可编辑性、证据边界和可审计性。

## 1. 初始化并连接

在项目根目录执行：

```powershell
& scripts/init_ppt_session.ps1 `
  -ProjectRoot <项目根目录> `
  -Workspace <新建的PPT工作空间> `
  -Title <汇报题目> `
  -Scenario <汇报场景> `
  -Audience <听众> `
  -DurationMin 20
```

初始化脚本先创建本地工作空间，再调用 `codex-chatgpt-bridge` 的工作空间包装器，以 `Auto` 能力连接网页版。连接记录保存在 `bridge-connect.json`。若连接失败，本地工作空间必须保留，但不得声称 GPT-6 或 GPT Image 2.5 已连接。

`-SkipWebConnection` 只允许用于自动化测试，或用户明确要求离线执行的场景；真实的网页协作任务不得使用。

## 2. 职责边界

| 责任方 | 必须负责 | 禁止代替其他层完成 |
|---|---|---|
| 网页版 GPT-6 | 叙事结构、逐页规划、信息密度、讲稿、证据缺口、公式讲解要求、审稿与批评 | 不生成 PPTX，不设计成一张完整幻灯片图像 |
| GPT Image 2.5 | 每个任务只生成一个独立小元素：`ornament`、`concept`、`art_text`、`icon` 或 `cutout` | 不生成整页、完整信息图、图表、表格、公式、实验结果或多元素拼贴 |
| Codex 本地脚本 | 原生标题正文、引文页码、图表表格公式、节点连接线、版式、逐元素插入、渲染与 QA | 不把整页截图当作最终页，不把不可编辑内容伪装成可编辑对象 |

## 3. 规划到素材

1. 将 `planning/gpt6_task_packet.md` 交给当前可见的 GPT-6 对话。
2. 按 `planning/deck_plan.schema.json` 保存 `deck_plan.json`。
3. Codex 审核每个 `asset_requests`：只有确需生成且适合单主体图像的请求才进入后续任务。
4. 每个通过的请求单独建立一个 `asset_job.py` 任务；不得把多个元素放进同一生成任务后裁切。
5. 在 GPT Image 2.5 中生成透明背景或易于独立排版的素材，执行视觉审查和哈希审查。
6. 只有 `accepted` 或 `integrated` 的任务可以进入清单。

## 4. 元素清单与组装

`assets/asset_manifest.json` 中的每个条目必须独立：

```json
{
  "kind": "icon",
  "slide_number": 4,
  "job_dir": "../../asset-jobs/slide-04-sensor-icon"
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

## 5. 最终 QA

- 渲染所有页面，检查遮挡、裁切、对比度、文本溢出和留白。
- 确认标题、正文、公式、数据图、表格、引文与页码仍为原生对象。
- 确认每个生成元素都是独立图片对象，名称为 `<slide_id>/<object_id>`。
- 检查 `qa/composition-report.json` 中 `whole_slide_generation_used` 为 `false`。
- 运行技能既有的 PPTX 结构检查与逐页视觉检查。
- 任务结束后按 bridge 技能要求断开当前连接并清理仅本次会话需要的临时服务。
