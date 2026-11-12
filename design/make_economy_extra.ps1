# 살림 경제 노트 — (1) 밝은 로고형 프로필 600x600  (2) 모바일 커버 1080x1080 (청록 무대, 내용은 가운데)
Add-Type -AssemblyName System.Drawing
$out = Join-Path $PSScriptRoot "blog_home\stage"
$font = "Malgun Gothic"
$C = { param($h) [Drawing.ColorTranslator]::FromHtml($h) }
$A = { param($a, $c) [Drawing.Color]::FromArgb($a, $c) }
$center = New-Object Drawing.StringFormat; $center.Alignment = 'Center'; $center.LineAlignment = 'Center'
$teal = & $C "#0F8A86"; $deep = & $C "#04363A"; $mint = & $C "#A6F7E6"; $gold = & $C "#FFD66B"

function Canvas($w, $h) {
  $b = New-Object Drawing.Bitmap $w, $h; $g = [Drawing.Graphics]::FromImage($b)
  $g.SmoothingMode = 'AntiAlias'; $g.TextRenderingHint = 'AntiAlias'; $g.InterpolationMode = 'HighQualityBicubic'
  return $b, $g
}
function RR($x, $y, $w, $h, $r) {
  $p = New-Object Drawing.Drawing2D.GraphicsPath
  $p.AddArc($x, $y, $r*2, $r*2, 180, 90); $p.AddArc($x+$w-$r*2, $y, $r*2, $r*2, 270, 90)
  $p.AddArc($x+$w-$r*2, $y+$h-$r*2, $r*2, $r*2, 0, 90); $p.AddArc($x, $y+$h-$r*2, $r*2, $r*2, 90, 90)
  $p.CloseFigure(); return $p
}
function Star($g, $cx, $cy, $s, $col) {
  $pts = @(
    (New-Object Drawing.PointF $cx, ($cy-$s)), (New-Object Drawing.PointF ($cx+$s*0.2), ($cy-$s*0.2)),
    (New-Object Drawing.PointF ($cx+$s), $cy), (New-Object Drawing.PointF ($cx+$s*0.2), ($cy+$s*0.2)),
    (New-Object Drawing.PointF $cx, ($cy+$s)), (New-Object Drawing.PointF ($cx-$s*0.2), ($cy+$s*0.2)),
    (New-Object Drawing.PointF ($cx-$s), $cy), (New-Object Drawing.PointF ($cx-$s*0.2), ($cy-$s*0.2)))
  $g.FillPolygon((New-Object Drawing.SolidBrush $col), $pts)
}
function TextPath($g, $text, $size, $rect, $brush, $fat) {
  $p = New-Object Drawing.Drawing2D.GraphicsPath
  $p.AddString($text, (New-Object Drawing.FontFamily $font), 1, $size, $rect, $center)
  if ($fat -gt 0) { $pen = New-Object Drawing.Pen $brush, $fat; $pen.LineJoin = 'Round'; $g.DrawPath($pen, $p) }
  $g.FillPath($brush, $p)
}
# 그래프 + 화살표 + ₩ 동전 아이콘 (가운데 cx, cy 기준, 크기 배율 k)
function MoneyIcon($g, $cx, $cy, $k, $barTop, $barBot) {
  $bars = @(@(-78, 20, 30, 42), @(-38, -4, 30, 66), @(2, -34, 30, 96))
  foreach ($b in $bars) {
    $x = $cx + $b[0]*$k; $y = $cy + $b[1]*$k; $w = $b[2]*$k; $h = $b[3]*$k
    $bp = RR $x $y $w $h (6*$k)
    $g.FillPath((New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.RectangleF $x, ($y-1), $w, ($h+2)), $barTop, $barBot, 90.0), $bp)
  }
  $ap = New-Object Drawing.Pen $gold, (7*$k); $ap.LineJoin = 'Round'; $ap.StartCap = 'Round'
  $ap.CustomEndCap = New-Object Drawing.Drawing2D.AdjustableArrowCap 3, 3
  $g.DrawLines($ap, @((New-Object Drawing.PointF ($cx-86*$k), ($cy+4*$k)), (New-Object Drawing.PointF ($cx-42*$k), ($cy-24*$k)),
                      (New-Object Drawing.PointF ($cx-14*$k), ($cy-12*$k)), (New-Object Drawing.PointF ($cx+44*$k), ($cy-60*$k))))
  $r = 30*$k; $ox = $cx + 62*$k; $oy = $cy + 28*$k
  $cp = New-Object Drawing.Drawing2D.GraphicsPath; $cp.AddEllipse($ox-$r, $oy-$r, $r*2, $r*2)
  $cb = New-Object Drawing.Drawing2D.PathGradientBrush $cp; $cb.CenterPoint = (New-Object Drawing.PointF ($ox-$r*0.3), ($oy-$r*0.3))
  $cb.CenterColor = (& $C "#FFF3C4"); $cb.SurroundColors = @((& $C "#E0A82E")); $g.FillPath($cb, $cp)
  $g.DrawEllipse((New-Object Drawing.Pen (& $C "#B8841C"), (2.5*$k)), $ox-$r*0.8, $oy-$r*0.8, $r*1.6, $r*1.6)
  $g.DrawString("₩", (New-Object Drawing.Font $font, (21*$k), ([Drawing.FontStyle]::Bold)), (New-Object Drawing.SolidBrush (& $C "#8A5F0E")), (New-Object Drawing.RectangleF ($ox-$r), ($oy-$r), ($r*2), ($r*2+2)), $center)
}

# ── (1) 밝은 로고형 프로필 ──
$S = 600
$bmp, $g = Canvas $S $S
$bg = New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.Rectangle 0, 0, $S, $S), (& $C "#F2FFFB"), (& $C "#CDF6EC"), 60.0
$g.FillRectangle($bg, 0, 0, $S, $S)
foreach ($ci in @(@(80, 90, 160, 50), @(540, 520, 220, 45), @(520, 70, 90, 40))) {
  $g.FillEllipse((New-Object Drawing.SolidBrush (& $A $ci[3] ([Drawing.Color]::White))), $ci[0]-$ci[2]/2, $ci[1]-$ci[2]/2, $ci[2], $ci[2])
}
# 둥근 네모 엠블럼 (그림자 + 청록 그라데이션)
$g.FillPath((New-Object Drawing.SolidBrush (& $A 40 $deep)), (RR 186 96 236 236 56))
$em = RR 182 88 236 236 56
$g.FillPath((New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.Rectangle 182, 88, 236, 236), (& $C "#17A79E"), $deep, 60.0), $em)
$g.DrawPath((New-Object Drawing.Pen (& $A 90 ([Drawing.Color]::White)), 2), (RR 190 96 220 220 50))
MoneyIcon $g 300 214 1.15 ([Drawing.Color]::White) $mint
Star $g 220 128 9 $gold; Star $g 392 300 6 $gold
TextPath $g "살림 경제 노트" 54 (New-Object Drawing.RectangleF 0, 350, $S, 80) (New-Object Drawing.SolidBrush $deep) 2
$g.FillRectangle((New-Object Drawing.SolidBrush $teal), 270, 438, 60, 4)
$g.DrawString("생활 꿀팁 · 재테크 · 절약", (New-Object Drawing.Font $font, 17, ([Drawing.FontStyle]::Bold)), (New-Object Drawing.SolidBrush $teal), (New-Object Drawing.RectangleF 0, 452, $S, 40), $center)
$bmp.Save((Join-Path $out "profile_600_economy_light.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()

# ── (2) 모바일 커버 1080 x 1080 : PC 대문을 세로로 다시 배치 (가운데 600px 안에 핵심) ──
$S = 1080
$bmp, $g = Canvas $S $S
# 바탕: PC 대문과 같은 청록 무대 (글자 없이 새로 그림) — 가운데 밝고 가장자리 짙게, 빛망울, 양쪽 조명
$g.Clear($deep)
$ep = New-Object Drawing.Drawing2D.GraphicsPath; $ep.AddEllipse(-300, -500, 1680, 1700)
$eb = New-Object Drawing.Drawing2D.PathGradientBrush $ep; $eb.CenterColor = $teal; $eb.SurroundColors = @($deep)
$g.FillRectangle($eb, 0, 0, $S, $S)
$rnd = New-Object Random 31
for ($i = 0; $i -lt 40; $i++) {
  $r = $rnd.Next(40, 160); $x = $rnd.Next(0, $S); $y = $rnd.Next(0, $S)
  $bp = New-Object Drawing.Drawing2D.GraphicsPath; $bp.AddEllipse($x-$r, $y-$r, $r*2, $r*2)
  $bb = New-Object Drawing.Drawing2D.PathGradientBrush $bp
  $bb.CenterColor = (& $A ($rnd.Next(25, 55)) (& $C @("#2FD3B7", "#58C7FF", "#FFD66B", "#7AF0C9")[$rnd.Next(0, 4)])); $bb.SurroundColors = @([Drawing.Color]::FromArgb(0, 0, 0, 0))
  $g.FillPath($bb, $bp)
}
foreach ($sp in @(@(60, 190, 160, 620), @(890, 1020, 460, 920))) {
  $pp = New-Object Drawing.Drawing2D.GraphicsPath
  $pp.AddPolygon(@((New-Object Drawing.PointF $sp[0], 0), (New-Object Drawing.PointF $sp[1], 0), (New-Object Drawing.PointF $sp[3], $S), (New-Object Drawing.PointF $sp[2], $S)))
  $g.FillPath((New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.Rectangle 0, 0, 10, ($S+1)), (& $A 60 ([Drawing.Color]::White)), (& $A 0 ([Drawing.Color]::White)), 90.0), $pp)
}
foreach ($sp in @(@(170, 250, 14), @(900, 220, 12), @(880, 820, 10), @(190, 840, 9), @(540, 210, 7))) { Star $g $sp[0] $sp[1] $sp[2] $gold }
MoneyIcon $g 540 330 1.25 ([Drawing.Color]::White) $mint
$tb = New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.Rectangle 0, 430, $S, 130), ([Drawing.Color]::White), $mint, 90.0
foreach ($w in @(26, 16)) { $p = New-Object Drawing.Drawing2D.GraphicsPath; $p.AddString("살림 경제 노트", (New-Object Drawing.FontFamily $font), 1, 96, (New-Object Drawing.RectangleF 0, 430, $S, 130), $center); $g.DrawPath((New-Object Drawing.Pen (& $A 30 (& $C "#2FD3B7")), $w), $p) }
TextPath $g "살림 경제 노트" 96 (New-Object Drawing.RectangleF 0, 430, $S, 130) $tb 3
$g.DrawString("오늘 꼭 알아야 할 생활·돈 정보를 한눈에", (New-Object Drawing.Font $font, 26, ([Drawing.FontStyle]::Bold)), (New-Object Drawing.SolidBrush (& $C "#D5FBF3")), (New-Object Drawing.RectangleF 0, 560, $S, 50), $center)
# 메뉴 2x2
$chips = @("생활 꿀팁", "재테크·금리", "절약·할인")
# 메뉴 한 줄 (가운데 정렬)
for ($i = 0; $i -lt $chips.Count; $i++) {
  $x = 540 + ($i - ($chips.Count - 1) / 2) * 290; $y = 680
  $cp = RR ($x - 130) $y 260 76 38
  $g.FillPath((New-Object Drawing.SolidBrush (& $A 120 (& $C "#053E42"))), $cp)
  $g.DrawPath((New-Object Drawing.Pen (& $A 170 $mint), 2), $cp)
  $g.DrawString($chips[$i], (New-Object Drawing.Font $font, 24, ([Drawing.FontStyle]::Bold)), [Drawing.Brushes]::White, (New-Object Drawing.RectangleF ($x - 130), $y, 260, 78), $center)
}
$bmp.Save((Join-Path $out "mobile_1080_economy.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()
"ok"
