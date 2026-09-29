# Photonico Code 字体检查报告

**最新：[横杠对齐几何中心](overlay-alignment/README.zh-CN.md)。** 按指定调整 `x`、`--`、`𝔼`、`◌` 的组合横杠位置，并保留等宽附着。上一轮完整检查见 [Claude 第二轮修正复查](review-2/README.zh-CN.md)，其中少用组合、多重音标堆叠及 ZWJ 控制符边界仍为已知事项。

- [横杠对齐：修改结果与前后图片](overlay-alignment/README.zh-CN.md)
- [第二轮复查：最新结果与图片](review-2/README.zh-CN.md)
- [第一轮 Claude 修改复查：历史快照](review-1/README.zh-CN.md)
- [首次全面检查：历史快照](initial/README.zh-CN.md)

旧 `audit/` 已移除。报告及其直接引用的图片／证据已迁入本目录并修正链接；其余原始中间文件完整保存于[原始证据压缩包](archive/font-audit-2026-09-29.zip)，包含274个文件，压缩后约4.4MB。删除原目录前已逐文件校验压缩包内内容，记录见[迁移清单](archive/migration-manifest.json)。

历史报告中的结论与源码行号对应各自的哈希快照，不能当作当前字体仍有同样问题。旧复现命令中的 `audit/` 是归档时的目录，解压证据包可以恢复；本次定点修改以 `overlay-alignment/` 为准，上一轮完整检查以 `review-2/` 为准。
