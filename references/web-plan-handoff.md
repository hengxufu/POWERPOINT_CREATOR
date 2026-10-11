# 网页规划回复接收与逐元素执行

先按 bridge-startup-contract.md 取得本会话连接证据。通过当前允许的浏览器工具提交 planning/gpt6-task-packet.md；读取实际助手回复，保存为 assistant-reply.txt，同时保存可见模型标签、对话地址和浏览器观察文件。不要用任务提示词、整页包含用户消息的抓取文本或本地编写内容冒充助手回复。

运行：

```powershell
python scripts/receive_web_plan.py --reply assistant-reply.txt --evidence browser-observation.txt --session-url https://chatgpt.com/c/实际对话编号 --model "实际可见的GPT-6标签" --out planning/received-v1
python scripts/plan_workflow.py jobs --plan planning/received-v1/deck_plan.json --profile research --out assets/web-queue-v1
```

接收器接受纯JSON或单个JSON代码围栏，检查连续页序、具体内容块、有限坐标与画布边界、唯一请求与对象、允许的单元素类型、艺术字准确文字。输出保留回复与观察文件的哈希；这不是后端型号认证，也不能证明内容正确或版面美观。接收后实际审阅事实与版式，再将获准规划用于本地源文件，并在delivery_review.web_planning登记实际回复路径与对话地址。

每个队列任务顺序执行：查看job状态及dispatch-intent→在实际图像入口提交prompt.txt→确认提交再登记submitted→等待并下载原图→receive技术检查→实际查看图标边缘、艺术字逐字准确、配饰和背景的协调性→review→placement→登记manifest→原生组装→核对实际PPT对象后integrated。submitted或submission_unknown不可自动重发；网页失败保留任务以供恢复。一个任务只生成一个元素，不批量拼图再裁切。艺术字位图另保留原生可编辑语义文本。

每次调整配色、材质、光照或艺术字字形，建立新任务版本，保存旧原图和审查记录。不能因为已有队列或文件路径就宣称生成或入稿完成。连接失败时继续原生排版和资料整理，但保持网页生成缺项。

浏览器控制必须遵守当前会话工具规则；已有CLI只是备用实现，不得绕过当前工具限制、浏览器授权或登录。扩展传输失败与未登录是不同状态，不能反复要求用户登录来代替排查。
