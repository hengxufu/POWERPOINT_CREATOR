# 复杂科研图的局部精修

适用于图片重建和后续的“改第三个流程框”等请求。不要以原生对象数量替代视觉判断。

## 定位与修改

`python scripts/deck_objects.py inspect deck.pptx --out objects.json`

清单按 presentation.xml 中的实际显示顺序解析，列出 `S页面.对象ID`、对象名、文字 runs、图片替代文本和连接线绑定信息。组内对象 ID 仍属于该页；不要拿组对象的聚合文字当成单个文本框。重建后 ID 可能改变，必须重新生成清单。

局部文字或元数据可用预条件补丁，保留全部非目标页面及原始媒体的字节：

```json
{"input_sha256":"从清单复制当前文件哈希","operations":[
  {"page":15,"id":"42","action":"text_run","run_index":0,"expected":"当前原文","value":"修改文字"},
  {"page":15,"id":"43","action":"rename","expected":"Picture 43","value":"S15.43-可见光航天器"},
  {"page":15,"id":"43","action":"alt_text","expected":"","value":"用于说明可见光观测外观的航天器图像，非实测结果。"}
]}
```

`python scripts/deck_objects.py patch deck.pptx --plan edits.json --out next-version.pptx`

脚本需要 defusedxml。它拒绝输入哈希不符、旧文本不符、已有输出文件和组级文字替换。文字改动后需渲染；仅修改对象名和替代文本不改变可见内容。多段落重排、图表、表格、位置、分组和连线修改仍在原制作源中完成。

可为已有原生连接线增加显式绑定：`action: bind_connector`，`expected` 使用清单中的 bindings，`start/end` 各为 `{"id":"节点ID","site":0}`。仅支持同一页的 rect/roundRect/ellipse，site 0/1/2/3 为上/左/下/右；不自动推断语义、路由或坐标，不支持跨组坐标的自动调整。新增绑定后渲染并在PowerPoint实际移动节点验证；仅有XML绑定不能声称动态移动测试通过。

## 连接线与语义分组

- 能绑定节点时创建真正的连接线，并在制作源绑定 begin/end 节点。普通分段线不自动跟随节点；在交付说明中区分“可编辑”和“移动节点后自动跟随”。不根据最近距离猜测端点。
- 模块的背景、标题、文字和局部图像可组成语义组，保持文字可单独编辑。不要将含表格、图表或嵌入对象的组强行扁平化。
- 对象名描述角色；图片替代文本描述信息用途。证据图说明来源和实测/示意身份，装饰图不要写成研究结果。
- 阅读顺序按标题→问题/结论→证据或方法→说明→来源核对；XML 绘制顺序不等于已经通过屏幕阅读器测试。

## 投影与内容检查

清单中的 small_normalized_font 以13.333英寸宽画布折算，14pt仅是复核信号。字号继承、组缩放、公式脚标和文献脚注可能例外。密集表格和流程页优先增加空间、拆分到补充页或精简重复内容，不自动删掉术语、条件、单位和不确定性。

每个科学主张记录：页面与对象ID、原文、类型（事实/假设/预期效果）、来源页码或图号、单位/样本量（适用时）、核验状态。缺少来源标记待核验；假设和预期验证不能改写为已实现效果。统计报告规则按领域和研究设计选择，不能把临床试验清单普遍套用到航天/工程汇报。

图片重建逐项核对文字、条件、方向、闭环、公式、图例和底部结论，保留原图对照。照片只裁出无正文的局部资产；图片中坐标、标签、数值应另建原生对象，不能重新烘焙进图片。

## 已核实来源

- [微软：连接线](https://support.microsoft.com/en-us/powerpoint/draw-or-delete-a-line-or-connector)：绑定节点的连接线可随节点移动。
- [微软：选择单独对象](https://support.microsoft.com/en-gb/powerpoint/select-individual-objects-on-a-slide)：选择窗格帮助定位被遮挡的对象。
- [微软：阅读顺序](https://support.microsoft.com/en-us/powerpoint/make-slides-easier-to-read-by-using-the-reading-order-pane)：复杂页需检查阅读顺序和替代文本。
- [微软：组合与取消组合](https://support.microsoft.com/en-gb/office/graphics-visuals/group-or-ungroup-shapes-pictures-or-other-objects)：组合适用于多个可选对象。

本轮核实日期2026-10-08；以上支持PPT对象操作，不证明科学内容正确。
