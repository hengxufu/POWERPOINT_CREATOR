# 每次启动的严格执行顺序

完整制作、重设计及新会话恢复制作均遵循此顺序。同一活跃会话内的微调复用尚有效的连接，不为每次改字重启。用户明确离线时保留其原话及原因，不能宣称网页流程完成。

1. 读bridge/SKILL.md及bridge/USER_POLICY.md。用当前实际项目根调用scripts/start_ppt.ps1；ProjectRoot与唯一AllowedRoot必须完全相同，新会话刷新连接ID。禁止携带上个项目profile、自动使用公网、计划任务或宽根例外。
2. start调用内嵌controller Configure（Tunnel none），只保存独立项目profile。成功仅为local_profile_configured，不是浏览器或模型成功。原DevSpace提供写工具/shell，不能把L1策略冒充技术隔离；默认不启动这个MCP服务，不绕过此限制。直接浏览器任务不需要把本地文件公开。
3. Codex立即用当前会话浏览器工具取得新鲜状态、定位本任务ChatGPT标签页、核实登录、查看模型选择器及图像入口。网页GPT-6负责规划，Codex修改源。不要读取无关聊天或认证输入。浏览器使用工具的文档约束优先；CLI替代仅在当前工具规则允许时使用。
4. 保存本任务可见的模型/入口观察到workspace/qa/web-observation.txt或本任务截图。登录、验证码、授权、配额或连接故障只能按实际状态处理。失败至多一次有依据的重置/重试，仍失败记阻塞，继续可执行本地准备但保持草稿，不盲发任务。
5. 记录观察并运行Check。observe只登记实际已看见的内容，不自动控制浏览器；禁止自编记录冒充页面。GPT-6需选择器证据，图像2.5需实际可见引擎证据。不可见时只有用户明确允许才使用--allow-unverified-image-note，交付仍标未核实。

```powershell
scripts/start_ppt.ps1 -ProjectRoot <精确项目根> -Workspace <项目内PPT工作空间> -Title <题目> -Profile research
# Codex在此执行实际浏览器操作和观察；不能跳过
python scripts/bridge_session.py observe --workspace <workspace> --planning-model <实际选择器文字> --image-model <实际可见引擎或unverified> --session-url <实际任务URL> --evidence <workspace/qa/web-observation.txt> --note <实际观察说明>
scripts/ppt_bridge.ps1 -Action Check -ProjectRoot <精确项目根> -Workspace <workspace>
```

6. Check通过后发送窄规划包，保存真实回复；逐项执行元素生成、下载、review、placement和compose。型号标签不可见的例外不等于模型已核实。资产生成成功需实际图片及最终PPT哈希，不以“连接成功”代替。
7. 原生内容/表格/图表、LaTeX源和公式、字体、内容证据、代表页与全篇审查照旧执行。delivery_gate在线模式会检查当前连接合同；未连接、旧连接、过期或被关闭时不能通过。连接观察默认4小时有效，过期刷新观察或重启，不擅自抬高时间窗口。
8. 最终校验完成、结束本次网页协作后调用ppt_bridge Off关闭该项目控制器并将连接合同标closed；保留此前生成的验收报告，closed后的再次交付需要新会话检查。只关闭自己创建的浏览器标签页，用户已有窗口保持。

硬性要求由启动和验收脚本核对，但skill不是对模型的系统级强制执行沙箱。不能保证模型永不忽略指令，也不能保证第三方网页登录、服务与型号永远可用。失败时必须说明具体阶段，不将未完成作品标为正式完成。
