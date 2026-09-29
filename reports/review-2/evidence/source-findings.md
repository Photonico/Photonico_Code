# 最新 Claude 修改：字形与轮廓复核

未发现新增字形、几何或填充回归。检查对象为最新 SFD 快照 SHA-256 `c1db32b7c031ff93e4417891bb73fc2e04790188947b4297151f56d43d557ee2`，对照上一轮审计的 `e566eaa94d4e4f9109c51a02e8b17a7fdd097b768a587761586cac47301c6e7d`。

- 源码字形数保持 2229；成品字形数保持 2230；cmap 保持 1784 个映射，零增删、零重映射。
- 全部源码字形的实际曲线、轮廓方向/闭合状态、组件引用与变换、advance 宽度、前景可见边界均与上一轮相同。
- 上一轮成品与最新成品的全部 2230 个字形，在相同 FreeType 渲染器、240 px、显式 `FT_LOAD_NO_HINTING | FT_LOAD_NO_BITMAP` 下，逐像素完全一致：0 差异。此检查隔离了单字形几何，不包括组合文本的 GPOS，也不代替小字号 hinting 检验。
- 变化集中在 2205 个字形的锚点记录，净增 2338 个锚点；组合音标/叠加行为由 shaping 检查覆盖。FontForge 的几何警告计数不变；缺失 anchor 的原始校验标记从 594→660，不应将这一工具计数单独当作显示回归。

此前修复仍保留，最新源码位置：`yacute` 14514、`ydieresis` 14542、`Ldot` 6710、`Ccedilla` 5196、`dollar.spacer` 62017、`dollar.ss04` 62026。

垂直度量本轮没有调整：Win/Typo/hhea ascent 仍为 1800，`Ohungarumlaut` / `Uhungarumlaut` yMax 仍 1935（7319 / 8725 行），`lacute` 1974（11955 行）。这是此前已知的高度边界，没有在此轮增加。

复现材料仅写于本临时目录：`compare_geometry.py`、`geometry_comparison.json`、`geometry_changes.json`、`ft_nohint_compare.c`、`raster_nohint_changes_240px.json`。源文件、仓库及先前审计文件未修改。
