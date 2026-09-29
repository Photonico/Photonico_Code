import CoreText
import CoreGraphics
import Foundation
import ImageIO
let paths=Array(CommandLine.arguments.dropFirst().prefix(2))
let output=CommandLine.arguments[3]
let fonts=paths.map{CTFontCreateWithGraphicsFont(CGFont(CGDataProvider(url:URL(fileURLWithPath:$0) as CFURL)!)!,84,nil,nil)}
let width=980,height=840
let context=CGContext(data:nil,width:width,height:height,bitsPerComponent:8,bytesPerRow:0,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)!
context.setFillColor(CGColor(gray:1,alpha:1));context.fill(CGRect(x:0,y:0,width:width,height:height))
let cell=1200.0/1950.0*84.0
let cols=[380.0,690.0]
let label=CTFontCreateWithName("Menlo" as CFString,15,nil)
let note=CTFontCreateWithName("Menlo" as CFString,12,nil)
@discardableResult func draw(_ text:String,_ font:CTFont,_ xx:Double,_ yy:Double)->Double{
 let attr=NSAttributedString(string:text,attributes:[NSAttributedString.Key(kCTFontAttributeName as String):font,NSAttributedString.Key(kCTForegroundColorAttributeName as String):CGColor(gray:0.07,alpha:1)])
 let line=CTLineCreateWithAttributedString(attr);context.textMatrix = .identity;context.textPosition=CGPoint(x:xx,y:yy);CTLineDraw(line,context)
 return CTLineGetTypographicBounds(line,nil,nil,nil)
}
draw("Native macOS CoreText | grid = 1200 font units",label,25,807)
draw("Before alignment",label,cols[0],773);draw("Geometric alignment",label,cols[1],773)
let samples:[(String,String)]=[("xx (control)","xx"),("x U+0336 x","x\u{0336}x"),("-- U+0335","--\u{0335}"),("x U+0335 U+0336 x","x\u{0335}\u{0336}x"),("x U+0336 U+0335 x","x\u{0336}\u{0335}x"),("U+1D53C U+0336","\u{1D53C}\u{0336}"),("U+25CC U+0336","\u{25CC}\u{0336}"),("q U+0301 U+0336 q","q\u{0301}\u{0336}q")]
for (i,(name,text)) in samples.enumerated(){
 let yy=680.0-Double(i)*84.0
 draw(name,label,25,yy+10)
 for (j,font) in fonts.enumerated(){
  for k in 0...2 {
   context.setStrokeColor(CGColor(red:0.68,green:0.81,blue:0.93,alpha:1));context.setLineWidth(1)
   context.move(to:CGPoint(x:cols[j]+Double(k)*cell,y:yy-17));context.addLine(to:CGPoint(x:cols[j]+Double(k)*cell,y:yy+61));context.strokePath()
  }
  let aw=draw(text,font,cols[j],yy)*1950.0/84.0
  draw(String(format:"%.0f units",aw),note,cols[j]+145,yy+12)
 }
}
draw("84 px render; widths shown in 1950 UPM font units. Blue guides mark cell boundaries.",note,25,25)
let image=context.makeImage()!;let dest=CGImageDestinationCreateWithURL(URL(fileURLWithPath:output) as CFURL,"public.png" as CFString,1,nil)!
CGImageDestinationAddImage(dest,image,nil);if !CGImageDestinationFinalize(dest){fatalError("PNG write failed")}
