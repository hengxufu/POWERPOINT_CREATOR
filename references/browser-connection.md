# 网页连接路线选择

两条路线统一遵守[必要资料交接](planning-material-handoff.md)。本文件是当前路由规则；历史成功、控制器配置和CLI版本输出均不能代替本会话网页实测。

## 默认选择

| 路线 | 优点与适用条件 | 切换条件 |
|---|---|---|
| A：Codex内置浏览器 | 默认优先；当前工具直接管理页面与可见控件，减少外部会话与环境依赖。可复用本任务已登录标签页 | 工具不可用，或一次有依据的重置/重试后仍失败；或当前工具缺少本任务必需的附件上传/原图下载能力 |
| B：内嵌bridge协调的官方Playwright CLI | A受阻时使用；支持明确会话、上传与下载，在授权的现有浏览器或独立会话中操作网页 | CLI本身不可用、接入失败或尚需登录/浏览器授权时，记录具体阻塞；不能仅因CLI可运行就说模型已连通 |

优先选当前已实测能够完成“资料送达→规划/生成→原始结果取回”的路线。如果用户指定浏览器/路线，遵从指定；不能为使用默认路线覆盖用户选择。A是默认首选，不是永远最快/最稳定的保证。B在A实际受阻且自身具备所需能力时成为本次最佳路线。已有提交或结果不明时，先恢复原任务会话，不能用换路线规避防重发。

用户说的CIL按CLI（命令行接口）理解。这里“官方”指Microsoft维护的Playwright CLI（@playwright/cli），不是OpenAI官方bridge命令行产品。内嵌bridge负责本项目profile、观察合同与结束清理；浏览器CLI负责网页交互。DevSpace/MCP是另一个能力层，不是浏览器生成必需项。默认不启动MCP、不开放公网、不授予shell或本地写权限。

## A：Codex内置浏览器

按本会话cua工具文档选择入口。初次调用只执行规定的一个入口；已知任务URL直接选该页，需要库存才getState。新页面可用`cua.createBrowserTab('iab', 'https://chatgpt.com', {visible:true})`。成功后先读工具返回的文档，再操作已观察控件；不要假设不同版本具有同样的上传/下载接口。

绑定本任务专用聊天，观察登录、模型选择器与图像入口，确认附件/正文已送达。工具启动失败与未登录是不同问题，不能让用户反复登录来修复工具超时。失败最多一次有依据的重置或重试，记录结果后切B。不能用CLI探查Codex内部端点或认证状态来修理内置浏览器。

## B：官方CLI备用路线

先读当前可用的playwright技能；当前工具规则优先。项目固定`@playwright/cli@0.1.22`，版本与能力重新查验，不自动追随latest。使用唯一任务Session，避免默认会话撞入其他任务。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/web_connection.ps1 -Action Version
# 仅在用户已允许现有浏览器调试时：
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/web_connection.ps1 -Action AttachCdp -Browser msedge -Session <任务会话>
# 或用户已安装并授权的官方扩展：
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/web_connection.ps1 -Action AttachExtension -Browser msedge -Session <任务会话>
# 若需独立任务窗口，既有授权范围内可自动打开；用户自行登录：
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/web_connection.ps1 -Action OpenIsolated -Browser msedge -Session <任务会话>
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/web_connection.ps1 -Action Snapshot -Session <任务会话>
```

不要遍历无关聊天。先读取本任务新鲜snapshot，再click/fill/press控件；UI变化后刷新引用。上传先打开已观察的文件选择控件，再用CLI `upload <必要文件>`；观察上传完成及发送后的附件状态。下载用可见原图下载按钮与官方download事件/saveAs，不猜隐藏图片接口。内置浏览器与CLI不共用控件引用编号。

`web_task.ps1 ReadTask/Submit/Download`是项目辅助器：Submit保存dispatch-intent，拒绝已提交/结果不明的重发；检查Image资料包并发送完整message.txt。有附件时该辅助器明确阻止自动发送，改走上述UI上传流程，保留同样的派发记录。Download要求唯一可见图片预览和下载按钮，文件落到本任务目录且不得覆盖旧文件。运行成功仍需实际查看网页、登记资料交接、接收和视觉检查。

不使用cookies导入导出、不复制日常用户配置、不读取认证文件、不抓取隐藏接口。真实登录/CAPTCHA/新权限由用户处理，失败不无限重试。API或内置image_gen是不同路线，不能静默替换用户要求的网页版生成。

## 两条路线共有的证据与结束

分别记录浏览器可操作、资料送达、实际模型标签、提交成功、真实回复/图片、原图下载。模型自述不作型号证据；界面隐藏型号时按启动合同处理未核实型号许可。保留本任务观察、时间、URL、输入/输出哈希；不能将截图当原始生成素材或将准备包称为真实回复。

`bridge_session.py observe`必须填写`--route builtin_browser|playwright_cli --route-reason <本次选择依据>`。Check通过后才推进规划；资料交接仍是独立检查。当前连接失效时重新观察，不从旧项目记录推断。

通过attach接入的用户浏览器结束用Detach；仅本次open的专用会话用Close。绝不close-all/kill-all。内置浏览器只关本次明确创建的标签页，未知创建结果不猜标签ID、不关闭用户窗口。若本次准备了PPT bridge合同，最后执行ppt_bridge Off；维护任务未启动bridge就如实记未启动。

## 维护验证的边界

2026-10-13技能维护：内置工具库存调用和一次定向iab打开均超时，未取得UI状态；固定CLI版本0.1.22和命令帮助可运行。未发送规划或生成请求，未验证当前登录、GPT具体型号、Image型号或原图下载。这个结果支持本次转向CLI诊断，不构成永久路线排名或生成成功证据。后续制作必须重新实际验证。

官方参考：[Playwright CLI仓库](https://github.com/microsoft/playwright-cli)、[Attach/Detach](https://playwright.dev/agent-cli/commands/attach)。固定版本帮助是执行命令的直接依据；官方文档说明attach前提和detach保留外部浏览器的语义。
