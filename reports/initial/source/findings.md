# 当前 SFD 轮廓与组件检查

> 历史检查快照：结论与源码行号对应当时的字体版本。报告已从 `audit/` 迁移；旧复现命令与未单独展开的中间文件完整保存在[原始证据压缩包](../../archive/font-audit-2026-09-29.zip)，解压后可还原原目录。最新结论请看 reports 的总索引。


检查对象：`00_Regular.sfd`；FontForge 20251009。源文件未修改。标准 `font.generate()` 导出到 `audit/generated/Photonico-current.ttf`。

## 已复核的用户截图项目

- **1 已修复**：`oe` 从第 16654 行开始，前景为 3 个正常闭合轮廓，可见边界 `(-80, -20, 1268, 980)`，不再有上移的整字副本。额外层中的历史轮廓不应计入发布字体。
- **2 仍存在**：`yacute` 的 acute 平移 `x=2592`（18206 行），`ydieresis` 的 dieresis 同样为 2592（18232 行）。前景最右分别到 3432、3517，但 advance 均为 1200，因此重音实际落入右侧第三个字符格。
- **3 仍存在**：`Ldot` 的 dotaccent 组件偏移 `(1272,-672)`（10554 行）；可见最右到 2012，advance=1200。
- **4 仍存在**：`dollar.spacer` 宽度 1206（65046 行）且有完整可见轮廓（65051 行起）；`dollar.ss04` 宽度也为 1206（65087 行）。全字体只有这两个非零 advance 不等于 1200：2206 个为 1200，21 个为 0，2 个为 1206。0 宽度不能整体视为错误，组合音标/控制字符可合法为 0。
- **9 仍存在，数量更新**：当前前景 48 个字形含 76 个单点轮廓。`G` 有 12 个，其中 `(179,-911)` 在 9643、9644、9647、9648 行；`<!--` 连字孤点 `(-3230,2238)` 在 56740 行。这些点没有填充面积；FontForge 的可见 bbox 会忽略它们，但导出 TTF 的 glyf bbox 仍可包含孤点（请以 root 的 fontTools 导出检查为准）。
- **10 不能照搬旧数量**：当前 FontForge `g.validate(True)` 返回 395 个 direction 标记、230 个 intersects 标记、64 个 flipped reference 标记。工具旗标属于排查入口，不能等同于 395 个渲染缺陷；重复组件、镜像和重叠也可能是设计意图。官方定义：https://fontforge.org/docs/scripting/python/fontforge.html#fontforge.glyph.validation_state
- **11 仍存在**：`Ohungarumlaut`/`Uhungarumlaut` 可见 ymax=1935（11144 / 12539 行），`lacute` ymax=1974（15688 行），而 SFD 的 Win/Typo/hhea ascent 均为 1800（36–48 行附近）。潜在裁切取决于渲染器，应区别于已实测 Windows 裁切。157 个前景字形超过 1800，107 个低于 -600，其中大量是框线、分段括号或连字扩展，不能一概压回行框。

## 新增结构问题

- **Ccedilla 的两个组件同时启用了 USE_MY_METRICS**：9056 和 9057 行的 Refer 最后标记均为 3；fontTools 检查当前导出 `Ccedilla` 的 cedilla、C 组件 flags 均为 `0x1204`，同时带 `0x200`。遍历所有复合字形只有这一处；FontForge/fontlint 将其报告为 `Use-my-metrics flag set on at least two components in glyph 138`，并汇总 `Bad glyf or loca table`。这不等于整个字体无法显示，但应该修复无歧义的双 metrics 标记。
- **6 个多点开放轮廓**：`.notdef`（8319 行）、`backslash.ss06`（45816）、`uni2BD1`（89314）、`uni2370`（89450）、`uni225F`（109022）、`uni2057`（115032）。`backslash.ss06` 路径端点数值相同但没有闭合标记；其余几处有小的游离线段。最终外观风险需分别核对，不应自动全局 close/simplify。

## 复现和数据约定

运行 `fontforge -lang=py -script audit/source/inspect_source.py`，随后运行 `fontforge -lang=py -script audit/source/foreground_check.py`。完整记录见 `source_geometry.json`。

- `bbox` 是递归解析组件后的**前景可见边界**，忽略单点轮廓；`all_layer_bbox` 是 FontForge `glyph.boundingBox()` 的原值，包含辅助层，因此不得用其判断成品墨迹溢出。
- `validation` 是对原 SFD 执行的原始校验位掩码，没有把警告自动认定为可见缺陷。
- `lines.start` 指向原 SFD，`one_points` 保留孤点坐标；为控制体积，没有保存所有曲线控制点。
- 加载仅产生缺失 `pkg_resources` 和插件配置写入受限的警告，未影响导出；没有保存原 SFD。
