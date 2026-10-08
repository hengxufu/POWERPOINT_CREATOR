# paper2ppt整合说明

读取来源：本地安装的nature-paper2ppt，manifest 2.0.0；读取其核心、六种paper_type片段、三个按需参考、质量审计程序，以及nature-shared术语规则。

本模块将论文论证、两遍阅读、关键证据选择、术语表、九步流程、裁剪检查、备注与修正验收整合到现有技能。六类叙事与按需加载由paper_manifest.json管理。辅助程序为本项目实现，未打包上游完整源码；可选上游审计保持其原位置与许可，不因本项目MIT许可而重新授权第三方材料。

取舍：保留用户既定字体与LaTeX/OMML策略、可编辑对象和艺术字要求；论文结果页证据优先，不机械采用禁装饰/小字号规则；不强制更换已有制作引擎。原文图不由生成模型重画数据，新增单元素仅用于装饰或明确概念图。

新文件：paper_manifest.json、paper-workflow、terminology-ledger、paper-evidence-and-quality、六个paper-types参考、paper_source.py、audit_paper_deck.py、示例计划和可选PDF依赖。
