# Nature 实验数据绘图融合

本模块融合本地nature-figure的科学论证、CSV模板、向量导出和渲染检查，并采用nature-statistics的实验单位、重复与误差报告边界。它不是将科研图交给网页图像模型绘制。用于真实实验/模型评估数据图；技能维护只跑隔离的合成测试，不制作无关科研成果。

## 两条路径与语言选择

常规柱形、折线、散点、面积和表格仍优先native_data：保留PowerPoint原生对象与嵌入工作簿。复杂分布/配对/多面板/不确定性图由nature-figure的数据绘图路线完成，保留可重建源、数据及SVG/PDF，再作为独立证据图入稿；图内曲线、坐标文字不声称是PPT原生对象。外部标题、解释、来源继续可编辑。图表不进入generate_web素材队列。

绘图后端遵守nature-figure：当前请求明确选择→语言专属输入流程→本任务已确立选择→其保存偏好；仍未确定才一次询问Python/R，且仅暂停依赖绘图的步骤。记住选择需使用其后端脚本，不为技能维护偷偷改全局偏好。当前包是Python专属工作流，下面的适配器仅支持Python；用户选择R时加载nature-figure R路线，不用Python出替代图。缺运行时或依赖则明确阻塞，不自动安装。

## 每图合同

每图先确定scientific_question、bounded_claim（假设/描述性结论也可）、evidence_role，再确认source_ref、原始或汇总数据、字段→含义→单位、独立实验单位、n定义、配对/嵌套/重复测量关系、中心和误差含义。SD/SEM/CI不同，不自动猜测；没有检验结果不补星号、p值或显著性。缺项写AUTHOR_INPUT_NEEDED并在图注披露，不能假装统计报告完整。

多panel围绕一个问题赋予不同证据角色；主证据突出，控制、负结果与边界不能为美观隐藏。配对设计优先配对连线或差值；热图注明缩放/归一化/聚类规则；箱线/小提琴解释边界、须、核密度与独立单位。多seed/fold比较一致使用同种误差定义，或给具体原因。不默认开展新的假设检验或模型拟合。

## 已接入的CSV模板

| plot_type | 科学用途 | 必需mapping |
|---|---|---|
| roc | 已计算FPR/TPR的判别曲线 | fpr-col、显式tpr-cols（逗号分隔） |
| paired | 完整的两条件配对观测 | id-col、condition-col、value-col |
| volcano | 已提供效应量与校正p值 | gene-col、effect-col、p-col |
| dotplot | 行列矩阵的大小/颜色双编码 | row-col、column-col、size-col、color-col |
| marginal | 二维观测与边际分布 | x-col、y-col；有分组时显式group-col |

这些是科学含义匹配后才用的模板，不是任意数据通吃的自动统计器。其他时间序列误差带、残差、消融、热图、分布和定制多panel直接走nature-figure源代码路线；不能声称适配器已经覆盖全部图型。ROC模板会计算描述性AUC，火山图使用给定阈值，均不执行新的假设检验。

## 准备与运行

```powershell
python scripts/experimental_figures.py prepare --spec <figure-spec.json> --csv <observations.csv> --nature-skill <本地nature-figure目录> --out <workspace>/data-figures/figure-v1
python scripts/experimental_figures.py run --bundle <workspace>/data-figures/figure-v1
```

本机已安装的nature-figure会自动发现，通常可省略--nature-skill。先检查所用Python有NumPy、Matplotlib与PyMuPDF；本机若捆绑Python缺绘图库，可用已有Anaconda Python，仍是同一Python后端，不为此安装依赖或改全局默认。优先用完整解释器路径保证重建环境一致。

spec包含figure_id、backend=python、plot_type、scientific_question、bounded_claim、evidence_role、source_ref、unit、independent_unit、n_definition、uncertainty_definition、mapping、options及size_inches。模板参数只允许白名单，不接受shell命令或任意CLI参数；ROC不能自动猜所有其余列。CSV全量保留；缺失/非有限值由模板阻止，不自动删行。确需排除时用另行审阅的绘图源，写明确规则和前后计数。

prepare把CSV、规范、绘图源、QA工具和本包runner复制到版本目录，逐个哈希锁定，状态prepared_not_rendered。保留上游源码说明，不改本地Nature技能。run拒绝变更输入和重复运行；修改数据/样式后准备新版本。输出SVG/PDF/600dpi TIFF及300dpi PNG，保留模板数据计数QA。缺依赖/对齐不可审计/渲染失败会保留日志，不冒充成功。

原始模板另存upstream快照；工作副本在导出函数中接入真实对齐调用，便于源预检与运行行为对应。NumPy 1.x以同义trapz兼容trapezoid，不变换观测或积分规则。上游导出结构变化时适配器拒绝自动套用，须重新审阅。

适配器采用白底、可选中文字库、18pt轴标签和16pt刻度/图例作为PPT起点；模板局部写死字号仍由PDF实测发现，不保证自动放大成功。设置size_inches为预期入稿大小，缩放入稿后再次检查实际字号；不能照搬期刊5–7pt到投影页。科学颜色编码优先于北航主题，原生页面身份层继续保持。

## 检查、入稿与交付

run先执行Nature源预检；布局最终draw后调用其1.5pt严格面板对齐gate；导出后运行PDF实际文字字号与严格碰撞审计。新生成或修改数据、坐标、图例、误差条、字体、面板布局后全部重跑。FAIL/NOT AUDITABLE阻止通过，WARN须查看并说明，不能放松全局阈值掩盖问题。边际分布等复杂布局若无法推断比较组，应在专属源中声明精确组，不广泛豁免。

自动检查全通过也只到rendered_requires_visual_review；blocked_qa需修复。实际查看各panel和全图、核对数据/单位/误差含义、最终大小和图例后，才登记人工审查。工具从不自填视觉pass；不能把合成测试记录当项目审查。

入稿沿用当前PPT生成器：以稳定slide_id/object_id插入通过审查的figure.png或经引擎实测支持的矢量文件，保持比例，不裁掉坐标/图例/误差条。建立data_figure_manifest，记录figure_id、bundle清单哈希、输出文件哈希、目标box_inches、实际picture名称、编辑性边界及审查记录；构建后核对实际PPTX图片字节。复杂图是一张独立图片，不拆子panel凑40对象。该模块不使用AI素材的engine/session字段，也不将本地数据图冒充网页生成。

交付时保留CSV、绘图源、figure-spec、SVG/PDF、入稿图与QA记录；审查未完成只交草稿。论文投稿时另查目标期刊当期规则；此融合不声称符合Nature投稿规范，也不沿用其论文物理尺寸替代PPT可读性。
