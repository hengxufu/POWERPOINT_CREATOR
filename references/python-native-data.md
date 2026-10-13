# Python原生表格与图表

复杂实验数据图见[experimental-data-figures.md](experimental-data-figures.md)：复用本地Nature数据模板与QA，常规原生路径仍优先，不把图片内曲线宣称可逐对象编辑。

`scripts/native_data.py`提供可复用add_chart/add_table函数，以及从JSON新建PPT的CLI。它写入PowerPoint原生chart/table，图表带嵌入工作簿，可修改数值、序列和标签。支持column、bar、line、area、pie、doughnut、scatter。不是将Matplotlib截图伪装成可编辑图表。

已有制作引擎优先沿用，并移植这些数据对象逻辑；不要用新建小工具round-trip含复杂数学或AlternateContent的旧PPT。原生形式无法表达的复杂科研图可另用Matplotlib等生成，保留数据与绘图脚本，并明确图像内的曲线和字不可逐对象编辑。

```powershell
python scripts/native_data.py --spec examples/native-data.json --out build/data-demo.pptx
python scripts/typography_check.py build/data-demo.pptx --out qa/fonts.json
```

JSON的每页含title、takeaway、notes与items。每个item需要id、type、box（英寸）、source、unit。chart另含chart_type、categories、series（name/values）；scatter的series改为name/points，每点[x,y]，可给x_unit。table含矩形rows，可给column_weights与font_size。

表格采用原生表头、交替浅底和可调列宽。数据图使用统一配色、坐标与单位；不要绘制伪3D柱形，不默认补显著性、误差条或缺失值。饼/环图只有非负且总量有效的组成数据适用，比较多个数值优先条形图。

渲染核对坐标轴、标签、数值是否与源一致，长表必要时分页。使用新输出路径，保留输入JSON；修改其中一个数值和单元格后重建并核对嵌入工作簿，是编辑性验证的一部分。样例数据全部合成，不作为科学发现或真实获奖材料。
