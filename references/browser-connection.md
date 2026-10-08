# 网页连接与验证

用户要求 GPT-6 规划和网页版 image2.5 时，分别验证聊天模型、图像入口、提交、回复和文件下载。程序安装成功或浏览器接入成功不代表生成成功。当前会话执行，禁止后台自动启动、计划任务和无限重试。

## 已验证的环境与限制（2026-10-08）

- 原 cua_repl 重置后仍因 Windows sandbox setup 失败，尚未接入网页。
- Node.js v24.19.0 和官方 @playwright/cli 0.1.22 可运行。
- Chrome CDP 接入失败：DevToolsActivePort 未找到；需要用户在 chrome://inspect/#remote-debugging 启用浏览器允许远程调试。
- Chrome 官方扩展接入失败：Playwright Extension 未安装。不能把这次失败写成授权成功。
- 用户指定后改用 Edge：固定版本 CLI 已实际运行；CDP 同样缺少 DevToolsActivePort，官方扩展也未安装。当前首选 Edge，等待用户在 edge://inspect/#remote-debugging 允许连接；不能沿用 Chrome 作为当前目标。
- 用户随后开启 Edge 调试。已确认 127.0.0.1:9222 监听进程为 msedge，CLI 能解析到 ws://localhost:9222/devtools/browser；通道自动发现与明确 127.0.0.1 WebSocket 地址均握手超时。/json/version 返回404，不能据此判定新版调试服务不存在。未完成网页接入，仍需区分浏览器连接确认与协议问题。检查端口只读取进程名和端口，不读取用户认证文件。
- 用户允许后再次连接现有 Edge 仍超时。替代路径已实际成功：`open https://chatgpt.com --browser=msedge --headed` 创建独立会话 ppt-edge-isolated，页面导航与可访问树读取成功。页面显示未登录，并明确登录后可创建图片。需要用户在此窗口自行登录；尚未验证 GPT-6、提交回复、image2.5及下载。
- 随后用户自行登录。模型选择菜单显示 GPT-6 为 checked，专用任务聊天已成功发送规划包并收到完整回复。用户允许在图像型号不可见时测试网页版图像，实际生成并通过可见下载按钮保存轨道 PNG（1254×1254）与“融合感知”艺术字 PNG（2172×724），均通过尺寸、真实alpha和本地视觉检查。两项素材实际插入18页PPT新副本封面，哈希和对象名校验通过，封面渲染已查看。image2.5精确型号仍为 unverified；此成功不能作为型号证据。
- bridge 已将 ProjectRoot 与唯一 AllowedRoots 设置为 D:\CODEX\2026-10-08\dia，Tunnel none，保持 Off。上述记录是当次证据，下次重新检查。

## 路径选择

1. 原网页工具可用时复用本任务标签页。失败最多重置一次。
2. 首选现有已登录浏览器经用户允许的 CDP：运行 scripts/web_connection.ps1 -Action AttachCdp。若需要人为允许连接，等待用户完成；不能更改安全设置来绕过。
3. 可改用官方 Playwright 扩展：用户安装并选择授权标签页后运行 -Action AttachExtension。扩展地址和安装步骤以官方文档为准。
4. 可运行 `scripts/web_connection.ps1 -Action OpenIsolated -Browser msedge -Session ppt-edge-isolated` 启动独立浏览器。不要指定日常用户配置目录，不复制 cookies、令牌或登录状态；验证码、账户登录由用户完成。登录期间不读取认证界面的输入。此路线已验证能打开网页及读可访问树，认证后的生成能力另行验证。
5. 远端只读 MCP 是另一个能力层，不能替代浏览器图像生成。ChatGPT 的 Secure MCP Tunnel 可研究作为私有服务接入路径；仅有说明文档不算已打通。依当前 bridge 政策配置精确项目根，核对服务实际工具表，默认禁止写文件与 run_shell。公开隧道、OAuth 或额外权限按用户政策办理，不能自动升级。

## 接入后的闭环

执行 Snapshot 读取新鲜页面。绑定本任务专用会话，检查模型选择器是否显示 GPT-6；模型自述不能作为证据。向网页发送窄 Task Packet：目标、已知材料、对象清单、约束、所需建议。网页负责规划/评审，Codex负责源修改与验证。

图像生成沿用 web-single-element.md 和 asset_job.py。一次一个元素，发送前查任务状态；submitted 或 submission_unknown 必须回原会话查结果，不能重复发送。图像型号不可见时 engine=unverified，不能从聊天模型推断 image2.5。

先观察 UI，再使用官方 CLI 可见控件的 click/fill/press。下载使用页面下载按钮；CLI run-code 可等待 Playwright download 事件后 saveAs 到任务目录。不要抓取 ChatGPT 隐藏接口或认证请求。保存原始文件，检查尺寸、透明通道、真实文字、科学语义与哈希，随后登记 PPT 的 slide_id/object_id。截图只作界面证据，不能当下载素材。

所有成功均保存非敏感证据：时间、工具版本、页面可见模型、任务URL、任务状态、素材路径/哈希和检查结果。截图可能包含私人聊天，应仅截本任务区域，不写入可复用技能。技能保存通用流程及脱敏结论。

结束用 Detach 离开通过attach接入的用户浏览器，不能 close 用户已有浏览器。自己通过open启动的专用会话不支持detach，使用CLI close停止该专用窗口；本轮已实测这一区别。临时专用会话的下次登录需重新确认，不导出登录状态。若本次启动 bridge，结束通过 controller Off 停止；不新增自动启动。

## PPT视觉策略

继续执行 visual-system-and-math.md：中文微软雅黑，西文 Times New Roman；公式保留真实 LaTeX 源，优先原生 OMML，兼容显示副本明确说明公式位图限制；多样化原生几何与局部生成素材形成统一蓝色视觉语言。艺术字必须实际生成并入稿，保留原生语义标题。第15/17页的文字、节点与连线保持可编辑。不能将整页生成图当作PPT页面，不用虚构数据提升视觉。

## 官方来源

- https://playwright.dev/agent-cli/commands/attach
- https://playwright.dev/docs/api/class-browsertype
- https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt
- https://help.openai.com/en/articles/11084440-images-in-chatgpt

API 图像调用是单独计费及授权路径，不能冒充网页版会员生成，也不能静默作为 fallback。

## 已实测的任务辅助程序

`scripts/web_task.ps1` 使用固定版本 CLI，仅读取本任务可见 main 内容，或操作已观察的输入框、图像预览下载按钮。不提供 cookie、认证文件、隐藏接口或远程 shell 能力。参数 Job 是已准备的单元素任务目录。

```powershell
# 先用 Snapshot 观察本任务；模型菜单与入口需要实际核实。
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/web_task.ps1 -Action ReadTask -Job <任务目录>
# SessionUrl必须是刚观察到的任务会话，禁止其他聊天。
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/web_task.ps1 -Action Submit -Job <任务目录> -SessionUrl https://chatgpt.com/c/<实际会话ID>
# 查看提交结果及网页状态，成功后用asset_job.py event登记submitted。
# 生成完成后打开对应图片预览，再下载原图。
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/web_task.ps1 -Action Download -Job <任务目录> -OutputFile <该任务目录内的绝对PNG路径>
```

Submit 会在发送前保存 dispatch-intent.json；已有标记或 submitted/submission_unknown 时拒绝重发。脚本失败不得继续登记成功。若错误明确发生在fill之前，复核任务页面确实没有消息，保留失败证据后建立新版本任务。结果不明时只回原会话查看。ReadTask、Submit和Download已实测；辅助程序并不替代观察模型、判断生成完成、视觉评审和PPT渲染。

本轮修复两个Windows兼容问题：PowerShell 5.1脚本中的中文控件名用Unicode表达避免UTF-8无BOM误读；提示词用.NET ReadAllText读取纯字符串，避免Get-Content提供者元数据被ConvertTo-Json展开为对象。下载限定唯一图片预览dialog和唯一下载按钮，路径必须位于Job目录，拒绝覆盖既有文件。若“滚动到底部”悬浮按钮遮挡图片，先正常点击滚动按钮，再打开图片；不能用force或盲点绕过。
