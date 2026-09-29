import CoreText
import CoreGraphics
import Foundation
for path in CommandLine.arguments.dropFirst() {
 let provider = CGDataProvider(url:URL(fileURLWithPath:path) as CFURL)!
 let font = CTFontCreateWithGraphicsFont(CGFont(provider)!, 1950, nil, nil)
 print("FONT \(path) monoSpace=\(CTFontGetSymbolicTraits(font).contains(.traitMonoSpace))")
 for text in ["xx", "q\u{0301}q", "x\u{0336}x", "x\u{0335}x", "--\u{0335}", "-\u{0335}", "x\u{0335}\u{0336}x", "x\u{0336}\u{0335}x", "q\u{0301}\u{0336}q", "\u{1D53C}\u{0336}", "\u{25CC}\u{0336}", "x\u{0323}x", "x\u{0325}x", "a\u{200b}b", "a\u{feff}b"] {
  let attr = NSAttributedString(string:text, attributes:[NSAttributedString.Key(kCTFontAttributeName as String):font])
  let line = CTLineCreateWithAttributedString(attr)
  let runs = CTLineGetGlyphRuns(line) as! [CTRun]
  var records:[String] = []
  for run in runs {
   let n=CTRunGetGlyphCount(run)
   var glyphs=[CGGlyph](repeating:0,count:n)
   var advances=[CGSize](repeating:.zero,count:n)
   var positions=[CGPoint](repeating:.zero,count:n)
   CTRunGetGlyphs(run,CFRange(location:0,length:n),&glyphs)
   CTRunGetAdvances(run,CFRange(location:0,length:n),&advances)
   CTRunGetPositions(run,CFRange(location:0,length:n),&positions)
   for i in 0..<n {records.append("gid\(glyphs[i]) x=\(positions[i].x) y=\(positions[i].y) aw=\(advances[i].width)")}
  }
  print("\(text.unicodeScalars.map {String(format:"U+%04X",$0.value)}.joined(separator:" ")) total=\(CTLineGetTypographicBounds(line,nil,nil,nil)): \(records.joined(separator:" | "))")
 }
}
