# 内嵌来源与范围

来源：本机已安装的codex-chatgpt-bridge（2026-10-11读取）。逐字复制scripts/bridge_controller.ps1、scripts/local_bridge.ps1、scripts/workspace_bridge.ps1作为核心控制程序，未更改原程序。PPT专用策略与上层适配器是本次新增。

没有复制runtime、node_modules、StateDir、用户账户配置、浏览器profile、cookies、令牌、认证状态、Cloudflare凭据或密钥。默认只执行Configure/Off，不启动未经技术限制的MCP工具集。PPT的统一上层入口是scripts/start_ppt.ps1及ppt_bridge.ps1，不直接采用上游Auto公网示例。

本机上游skill根未提供独立LICENSE文件。本地整合不构成对上游或其第三方依赖的重新许可；对外发布前应确认其分发许可。PPT自编代码的MIT声明不自动覆盖这些内嵌上游文件。
