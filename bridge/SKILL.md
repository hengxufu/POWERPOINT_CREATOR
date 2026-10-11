---
name: ppt-embedded-bridge
description: PPT制作的会话级bridge配置、网页观察与能力校验；仅用于本PPT技能的启动和结束。
---

# PPT内嵌bridge

每次用户在活跃Codex会话启动本PPT技能，都按其当前请求自动准备连接。不是Windows启动项、后台常驻服务或定时任务。先读本目录USER_POLICY.md，再按references/bridge-startup-contract.md执行。

scripts中包含从本机codex-chatgpt-bridge复制的workspace/controller/local核心程序；PPT只能通过上层scripts/ppt_bridge.ps1入口使用。上游原程序有公网、shell及写权限相关路径，复制不等于授权；本入口不调用这些路径，不默认启动未经技术限制的MCP服务。

连接分层：独立本地项目profile、实际浏览器控制、可见GPT-6选择器、实际图像入口/引擎证据。controller健康或返回0不能代替网页验证。模型隐藏时不声称精确引擎，需用户允许未核实型号；失败只保留草稿并报告步骤。

网页采用当前可用浏览器工具，仅读取本任务页面；Codex执行所有源修改与验证。页面登录/CAPTCHA由人完成。结束按ppt_bridge Off关闭本次控制会话；只关闭自己创建的浏览器标签页，不关闭用户已有窗口。

核心程序来源是本地安装版本（2026-10-11），未复制runtime、账户配置、状态目录或认证文件。第三方DevSpace/Node运行时不包含在包内，原程序的依赖与许可不被本包MIT许可重新授权。运行时启动能力未验证时不得报告MCP已连通。
