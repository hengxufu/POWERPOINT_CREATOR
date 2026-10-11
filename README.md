# POWERPOINT_CREATOR

每次制作或新会话恢复，入口为`scripts/start_ppt.ps1`。内嵌bridge核心控制程序位于bridge/scripts；严格顺序见[bridge-startup-contract](references/bridge-startup-contract.md)。启动先配置精确项目profile，再由当前Codex会话操作浏览器并核实模型/图像入口；本地配置成功不等于网页连通。在线delivery_gate会拒绝缺失、过期或关闭的连接记录。结束运行ppt_bridge Off。新增连接回归：`python scripts/test_bridge_session.py`。

新增中国高校答辩/竞赛方案：scholarship（国奖）、research（科研）、challenge（挑战杯）、innovation（创新创业）。调研来源与适用边界见[场景参考](references/chinese-defense-and-competition.md)。

```powershell
# 准备待发送的GPT-6任务包与10种构图坐标；此步不调用网页
python scripts/plan_workflow.py packet --brief brief.md --profile challenge --out planning-request
# 实际取得网页版规划后，将素材需求拆为单个任务；此步尚未提交
python scripts/plan_workflow.py jobs --plan planning/deck_plan.json --profile challenge --out asset-jobs-v1
# 按web-single-element实际提交、下载、审查与入稿，再运行delivery_gate
# Python生成原生图表和表格，保留内嵌工作簿与原始JSON
python scripts/native_data.py --spec examples/native-data.json --out build/data-demo.pptx
```

`asset_spec.py`新增图标、产品概念、飘带、里程碑、项目艺术字及研究对象插画预设。`layout_catalog.py`提供可调整的构图起点。新能力离线验证：`python scripts/test_planning_and_data.py`。样例图表全部合成，不能当成真实项目结果或最终视觉标准。

完整制作的执行规范见[production-and-delivery](references/production-and-delivery.md)。新增`delivery_gate.py`将规划中的网页素材需求与最终PPT图片对象、哈希和逐页审查记录对应；初始化会创建尚未通过的审查模板。组装输出默认仍是草稿，不能仅凭结构检查通过就宣称视觉完成。离线回归检查：`python scripts/test_delivery_gate.py`。
一个PPT水货的探索


## 论文到PPT模块

Python工具测试环境为Python3.12；在项目环境安装核心依赖：`python -m pip install -r requirements.txt`。处理PDF时再安装可选requirements-paper.txt。依赖不随技能目录捆绑。

已整合本地nature-paper2ppt 2.0.0的叙事与证据流程。入口见SKILL.md与paper_manifest.json；包含六类论文叙事、术语表、PDF选页/证据提取、论文PPT审计，继续沿用中文微软雅黑、西文Times New Roman、LaTeX/OMML和可编辑对象策略。PDF可选依赖：`python -m pip install -r requirements-paper.txt`。完整取舍见PAPER2PPT_INTEGRATION.md。
