import CoreText
import CoreGraphics
import Foundation
import ImageIO
let paths=Array(CommandLine.arguments.dropFirst().prefix(2))
let output=CommandLine.arguments[3]
let fonts=paths.map{CTFontCreateWithGraphicsFont(CGFont(CGDataProvider(url:URL(fileURLWithPath:$0) as CFURL)!)!,1950,nil,nil)}
let context=CGContext(data:nil,width:1000,height:660,bitsPerComponent:8,bytesPerRow:0,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)!
context.setFillColor(CGColor(gray:1,alpha:1));context.fill(CGRect(x:0,y:0,width:1000,height:660))
let label=CTFontCreateWithName("Menlo" as CFString,15,nil)
let small=CTFontCreateWithName("Menlo" as CFString,12,nil)
let scale=0.060
func text(_ s:String,_ x:Double,_ y:Double,_ f:CTFont){
 let a=NSAttributedString(string:s,attributes:[NSAttributedString.Key(kCTFontAttributeName as String):f,NSAttributedString.Key(kCTForegroundColorAttributeName as String):CGColor(gray:0.1,alpha:1)])
 context.textMatrix = .identity;context.textPosition=CGPoint(x:x,y:y);CTLineDraw(CTLineCreateWithAttributedString(a),context)
}
text("Native CoreText: overlay placement relative to source geometry",25,630,label)
text("Before alignment",390,590,label);text("Geometric alignment",700,590,label)
let samples:[(String,String,Double,Double)]=[("x + U+0336","x\u{0336}",600,480),("-- + U+0335","--\u{0335}",1200,600),("U+1D53C + U+0336","\u{1D53C}\u{0336}",595,650),("U+25CC + U+0336","\u{25CC}\u{0336}",600,600)]
for (i,(name,sample,cx,cy)) in samples.enumerated(){
 let yy=470.0-Double(i)*110.0
 text(name,25,yy+32,label);text(String(format:"target centre (%.0f, %.0f)",cx,cy),25,yy+10,small)
 for (j,font) in fonts.enumerated(){
  let xx=[390.0,700.0][j]
  let attr=NSAttributedString(string:sample,attributes:[NSAttributedString.Key(kCTFontAttributeName as String):font])
  let line=CTLineCreateWithAttributedString(attr)
  for run in CTLineGetGlyphRuns(line) as! [CTRun]{
   let n=CTRunGetGlyphCount(run);var glyphs=[CGGlyph](repeating:0,count:n);var pos=[CGPoint](repeating:.zero,count:n)
   CTRunGetGlyphs(run,CFRange(location:0,length:n),&glyphs);CTRunGetPositions(run,CFRange(location:0,length:n),&pos)
   for k in 0..<n {
    guard let p=CTFontCreatePathForGlyph(font,glyphs[k],nil) else{continue}
    let isOverlay=glyphs[k]==1673 || glyphs[k]==1674
    if isOverlay {let b=p.boundingBoxOfPath;print("font\(j) \(name): native overlay centre=(\(b.midX+pos[k].x),\(b.midY+pos[k].y))")}
    context.saveGState();context.translateBy(x:xx,y:yy);context.scaleBy(x:scale,y:scale);context.translateBy(x:pos[k].x,y:pos[k].y)
    context.setFillColor(isOverlay ? CGColor(red:0.85,green:0.08,blue:0.10,alpha:0.82) : CGColor(gray:0.08,alpha:1));context.addPath(p);context.fillPath();context.restoreGState()
   }
  }
  context.setStrokeColor(CGColor(red:0.0,green:0.48,blue:0.42,alpha:0.85));context.setLineWidth(1);context.setLineDash(phase:0,lengths:[3,3])
  context.move(to:CGPoint(x:xx-8,y:yy+cy*scale));context.addLine(to:CGPoint(x:xx+(cx*2+160)*scale,y:yy+cy*scale));context.strokePath()
  context.move(to:CGPoint(x:xx+cx*scale,y:yy-8));context.addLine(to:CGPoint(x:xx+cx*scale,y:yy+(cy*2+110)*scale));context.strokePath();context.setLineDash(phase:0,lengths:[])
 }
}
text("Red = overlay glyph; green crosshair = source outline bounding-box centre.",25,70,small)
text("Glyph paths and positions use native CoreText. Export rounding can differ by ~1 unit.",25,48,small)
let image=context.makeImage()!;let dest=CGImageDestinationCreateWithURL(URL(fileURLWithPath:output) as CFURL,"public.png" as CFString,1,nil)!
CGImageDestinationAddImage(dest,image,nil);if !CGImageDestinationFinalize(dest){fatalError("PNG write failed")}
