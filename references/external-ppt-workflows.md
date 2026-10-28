# 外部 PPT 能力接入制作流程

本文件在规划接收后、选择组装路线前读取；适用于模板填充、已有 presentation-skill 工作空间和 HTML 来源页面。这里定义流程接入，不表示外部运行时已安装或已通过本项目测试。默认仍使用项目原生组装流程；所有路线执行相同的网页规划、素材、主题、40元素和 delivery_gate 合同。

## 路线选择与记录

在工作空间保存 `assembly-route.json`，记录 `route`（native / presentation_source / template_patch / dom_export）、选择理由、源文件绝对路径、源文件SHA256、外部仓库提交、实际运行命令、输出路径、验证状态和未解决问题。缺失运行时先做本地可执行准备，不把候选路线记为成功。

1. 有 outline.json 和对应制作源：选择 presentation_source，读取该仓库 editing 与工作空间参考，使用其固定运行时的 doctor、build/finalize 和 repair_packet 修订循环。保留 outline、evidence_plan、asset_plan 与 deck_ir；项目 deck_plan 仍承载网页规划与素材请求。按 slide_id 建立两份规划的页序映射，核对标题、来源、数据和讲稿后组装。
2. 有指定 PPTX 模板：先执行 `deck_objects.py inspect`，实际查看模板渲染，记录显示页序、对象ID、母版/布局、占位符与保留区域。简单文字替换使用现有带输入哈希和旧值预条件的 patch；跨run标签、多段落、继承样式和幻灯片重排进入制作源或专用OOXML实现，不直接全包字符串替换。选择幻灯片库时必须保留页面及其布局、母版、图片、图表、工作簿、备注的关系闭包；未验证闭包的工具不得用于正式合并。
3. 用户提供 HTML 或明确需要浏览器布局：dom_export 作为可选转换路线，先做一个真实代表页转换试验。保留HTML/CSS、字体、资源、固定依赖版本及导出命令；等待字体和图片加载后导出。普通新建科研PPT不因该工具存在而自动转HTML。

## DOM转换执行与修复

在当前项目内配置固定版本依赖，使用仓库对应版本的导出CLI；先检查 `--help`，再以本地HTML和显式输出路径执行，不运行全局skills安装器。不得默认使用latest CDN。浏览器加载的外部资源要记录来源，敏感资料遵循既有资料交接要求。

保留单页容器与稳定对象标识；讲稿通过 `data-pptx-notes` 传入，导出后逐页核对实际notes文本。模板模式按实际布局名选择，核对输出尺寸；该模式保留模板原有页并追加新页，必须在源模板副本中明确安排预期页数，不能把多出的旧页当作交付内容。

CSS伪元素、渐变和复杂效果可能成为SVG或位图，逐项检查输出对象。SVG不等同于Office原生图表，统计图、表格和公式仍使用项目native_data与数学流程；转换后需要时在制作源补回原生对象。字体自动嵌入需检查实际结果和字体许可，不能以浏览器显示正常证明PPT字体可用。动画仅在有需求时采用，并在目标PowerPoint实际播放；静态渲染不证明动画正确。

## 所有路线的共同验收

先比较规划与最终显示页序，逐页核对关键值、单位、条件、来源及实际备注。检测未替换的占位文字；合法的代码/公式花括号需按语境判断。逐图检查嵌入工作簿，运行编辑性、字体、元素密度与来源审计。按实际PPTX重新渲染代表页和全篇，查看裁切、换行、重叠、伪元素、模板页脚与内容的冲突。修改源后重建并更新哈希及审查。最后执行现有delivery_gate，任何外部工具的成功收据不能代替本项目验收。

## 依据与许可边界（2026-10-28）

- [siril9/presentation-skill](https://github.com/siril9/presentation-skill)，提交 `efd899c5ddf866af2ce0001c4c9340af775d4d55`：参考 source-first、语义IR、repair_packet及源字段保留检查；已读SKILL.md，根LICENSE为MIT。
- [jwynia/pptx-generator](https://github.com/jwynia/agent-skills/tree/main/skills/general/document-processing/presentation/pptx-generator)，提交 `e02ec7e226a6e4f8419fd3b88a1d8e472d421b32`：参考模板清单、占位符、布局继承和页面库流程；SKILL声明MIT，但本次未找到根LICENSE，因此不复制其实现。其缩略图提取不等于逐页渲染。
- [atharva9167j/dom-to-pptx](https://github.com/atharva9167j/dom-to-pptx)，提交 `e1805f5d1314388212eea8d92bb077c511385a39`：参考Readme和docs/template-support.md中的DOM转换、讲稿、模板追加及局限；根LICENSE为MIT。尚未执行本项目导出运行测试。

本次以独立编写的流程规则整合，不复制或捆绑上游代码。未来若引入代码，保存对应许可证及版权声明，并针对实际采用的版本验证，不继承上游宣传中的精度或编辑性结论。
