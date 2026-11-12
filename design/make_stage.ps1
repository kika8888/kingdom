# 기존 연예 블로그(soduwk1209) 대문과 같은 '무대' 스타일: 짙은 보라 + 조명 + 빛망울 + 분홍 빛나는 제목 + 금색 별
# 색 조합: 바탕 가장자리·가운데, 제목 위·아래·번짐, 포인트(메뉴 사이 별·테두리), 메뉴 띠, 빛망울 4색, 옅은 글자
param([string]$Title = "MK 연예계 뉴스", [string]$Name = "",
      [string]$Edge = "#1A0830", [string]$Mid = "#4A1A6E", [string]$T1 = "#FFF1F8", [string]$T2 = "#FF8FC8",
      [string]$Glow = "#FF5FB0", [string]$Acc = "#FF7FC0", [string]$Band = "#2A1440", [string]$Soft = "#E9D6FF",
      [string]$Bokeh = "#FF6FB5,#9B5CFF,#FFB86B,#C77DFF",
      # 문구: 대문 윗줄·부제(가운데 금색 부분)·메뉴(쉼표로), 위젯 제목 두 줄, 프로필 큰 글자·작은 글자·영문, 프로필 그림(mic|money)
      [string]$Kicker = "ENTERTAINMENT NEWS", [string]$SubA = "오늘 가장 뜨거운 ", [string]$SubHi = "스타 소식", [string]$SubB = "을 한눈에",
      [string]$Menus = "스타 근황,결혼 · 열애,방송,이슈", [string]$WTitle1 = "MK 연예계", [string]$WTitle2 = "뉴스", [string]$WKick = "ENTERTAINMENT",
      [string]$PMain = "MK", [int]$PMainSize = 96, [string]$PSub = "연예계 뉴스", [string]$PKick = "ENTERTAINMENT", [string]$Icon = "mic")
Add-Type -AssemblyName System.Drawing
$out = Join-Path $PSScriptRoot "blog_home\stage"
New-Item -ItemType Directory -Force $out | Out-Null
$sfx = $(if ($Name) { "_$Name" } else { "" })
$font = "Malgun Gothic"
$C = { param($h) [Drawing.ColorTranslator]::FromHtml($h) }
$A = { param($a, $c) [Drawing.Color]::FromArgb($a, $c) }
$pinkTop = & $C $T1; $pinkBot = & $C $T2; $gold = & $C "#FFD66B"
$center = New-Object Drawing.StringFormat; $center.Alignment = 'Center'; $center.LineAlignment = 'Center'

function Canvas($w, $h) {
  $b = New-Object Drawing.Bitmap $w, $h; $g = [Drawing.Graphics]::FromImage($b)
  $g.SmoothingMode = 'AntiAlias'; $g.TextRenderingHint = 'AntiAlias'; $g.InterpolationMode = 'HighQualityBicubic'
  return $b, $g
}
function Stage($g, $w, $h, $seed) {
  # 바탕: 위쪽 가운데가 밝은 보라 → 가장자리 짙은 보라
  $g.Clear((& $C $Edge))
  $p = New-Object Drawing.Drawing2D.GraphicsPath; $p.AddEllipse(-$w*0.3, -$h*0.9, $w*1.6, $h*1.9)
  $pg = New-Object Drawing.Drawing2D.PathGradientBrush $p
  $pg.CenterColor = (& $C $Mid); $pg.SurroundColors = @((& $C $Edge))
  $g.FillRectangle($pg, 0, 0, $w, $h)
  # 빛망울
  $rnd = New-Object Random $seed
  $cols = $Bokeh.Split(",")
  for ($i = 0; $i -lt [int]($w / 22); $i++) {
    $r = $rnd.Next([int]($h*0.06), [int]($h*0.2)); $x = $rnd.Next(0, $w); $y = $rnd.Next(0, $h)
    $bp = New-Object Drawing.Drawing2D.GraphicsPath; $bp.AddEllipse($x-$r, $y-$r, $r*2, $r*2)
    $bb = New-Object Drawing.Drawing2D.PathGradientBrush $bp
    $bb.CenterColor = (& $A ($rnd.Next(25, 60)) (& $C $cols[$rnd.Next(0, 4)])); $bb.SurroundColors = @([Drawing.Color]::FromArgb(0, 0, 0, 0))
    $g.FillPath($bb, $bp)
  }
}
function Spot($g, $x1, $x2, $bx1, $bx2, $h) {
  $p = New-Object Drawing.Drawing2D.GraphicsPath
  $p.AddPolygon(@((New-Object Drawing.PointF $x1, 0), (New-Object Drawing.PointF $x2, 0), (New-Object Drawing.PointF $bx2, $h), (New-Object Drawing.PointF $bx1, $h)))
  $lb = New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.Rectangle 0, 0, 10, ($h+1)), (& $A 70 ([Drawing.Color]::White)), (& $A 0 ([Drawing.Color]::White)), 90.0
  $g.FillPath($lb, $p)
}
function Star($g, $cx, $cy, $s, $col) {
  $pts = @(
    (New-Object Drawing.PointF $cx, ($cy-$s)), (New-Object Drawing.PointF ($cx+$s*0.2), ($cy-$s*0.2)),
    (New-Object Drawing.PointF ($cx+$s), $cy), (New-Object Drawing.PointF ($cx+$s*0.2), ($cy+$s*0.2)),
    (New-Object Drawing.PointF $cx, ($cy+$s)), (New-Object Drawing.PointF ($cx-$s*0.2), ($cy+$s*0.2)),
    (New-Object Drawing.PointF ($cx-$s), $cy), (New-Object Drawing.PointF ($cx-$s*0.2), ($cy-$s*0.2)))
  $glow = New-Object Drawing.Drawing2D.GraphicsPath; $glow.AddEllipse($cx-$s*1.6, $cy-$s*1.6, $s*3.2, $s*3.2)
  $gb = New-Object Drawing.Drawing2D.PathGradientBrush $glow; $gb.CenterColor = (& $A 90 $col); $gb.SurroundColors = @([Drawing.Color]::FromArgb(0, 0, 0, 0))
  $g.FillPath($gb, $glow); $g.FillPolygon((New-Object Drawing.SolidBrush $col), $pts)
}
# 굵게 빛나는 글자: 글자 모양(path)에 두꺼운 테두리로 굵게 + 바깥 번짐 + 위→아래 흰분홍 그라데이션
function GlowText($g, $text, $size, $rect, $top, $bot, $glowCol, $fat) {
  $p = New-Object Drawing.Drawing2D.GraphicsPath
  $p.AddString($text, (New-Object Drawing.FontFamily $font), [int][Drawing.FontStyle]::Bold, $size, $rect, $center)
  foreach ($w in @(26, 18, 11)) {
    $pen = New-Object Drawing.Pen ((& $A 22 $glowCol)), $w; $pen.LineJoin = 'Round'; $g.DrawPath($pen, $p)
  }
  $bnd = $p.GetBounds()
  $lb = New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.RectangleF $bnd.X, ($bnd.Y-1), $bnd.Width, ($bnd.Height+2)), $top, $bot, 90.0
  if ($fat -gt 0) { $pen = New-Object Drawing.Pen $lb, $fat; $pen.LineJoin = 'Round'; $g.DrawPath($pen, $p) }
  $g.FillPath($lb, $p)
}
function Spaced($g, $text, $size, $cy, $w, $col, $gap) {
  $f = New-Object Drawing.Font $font, $size, ([Drawing.FontStyle]::Bold)
  $ws = @($text.ToCharArray() | ForEach-Object { $g.MeasureString([string]$_, $f).Width * 0.72 })
  $total = ($ws | Measure-Object -Sum).Sum + $gap * ($ws.Count - 1)
  $x = ($w - $total) / 2
  for ($i = 0; $i -lt $ws.Count; $i++) {
    $g.DrawString([string]$text[$i], $f, (New-Object Drawing.SolidBrush $col), (New-Object Drawing.RectangleF $x, ($cy-$size), ($ws[$i]+$size), ($size*2)), (New-Object Drawing.StringFormat))
    $x += $ws[$i] + $gap
  }
}

# ── 1) 대문 1920 x 600 (스킨배경 상단 영역에 그대로) ──
$W = 1920; $H = 600
$bmp, $g = Canvas $W $H
Stage $g $W $H 5
Spot $g 200 330 260 960 $H; Spot $g 1590 1720 960 1660 $H
foreach ($s in @(@(376,152,14), @(1553,126,13), @(1651,342,10), @(309,348,9), @(527,74,7), @(1767,194,7), @(205,220,5), @(1426,263,6))) { Star $g $s[0] $s[1] $s[2] $gold }
Spaced $g $Kicker 17 128 $W (& $C $Soft) 14
GlowText $g $Title 118 (New-Object Drawing.RectangleF 0, 150, $W, 150) $pinkTop $pinkBot (& $C $Glow) 4
# 부제: '스타 소식' 만 금색
$sf = New-Object Drawing.Font $font, 22, ([Drawing.FontStyle]::Bold)
$parts = @(@($SubA, (& $C $Soft)), @($SubHi, $gold), @($SubB, (& $C $Soft)))
$fmt = [Drawing.StringFormat]::GenericTypographic.Clone(); $fmt.FormatFlags = $fmt.FormatFlags -bor [Drawing.StringFormatFlags]::MeasureTrailingSpaces
$tw = ($parts | ForEach-Object { $g.MeasureString($_[0], $sf, 2000, $fmt).Width } | Measure-Object -Sum).Sum
$x = ($W - $tw) / 2
foreach ($pt in $parts) { $g.DrawString($pt[0], $sf, (New-Object Drawing.SolidBrush $pt[1]), $x, 322, $fmt); $x += $g.MeasureString($pt[0], $sf, 2000, $fmt).Width }
# 가운데 가는 빛줄
$lb = New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.Rectangle 700, 0, 520, 2), (& $A 0 $pinkBot), (& $A 0 $pinkBot), 0.0
$cb = New-Object Drawing.Drawing2D.ColorBlend 3; $cb.Colors = @((& $A 0 $pinkBot), (& $A 200 $pinkBot), (& $A 0 $pinkBot)); $cb.Positions = @([single]0, [single]0.5, [single]1); $lb.InterpolationColors = $cb
$g.FillRectangle($lb, 700, 465, 520, 2)
# 아래 메뉴 띠
$g.FillRectangle((New-Object Drawing.SolidBrush (& $A 150 (& $C $Band))), 0, 492, $W, 108)
$g.FillRectangle((New-Object Drawing.SolidBrush (& $A 110 (& $C $Soft))), 0, 492, $W, 1)
$menuList = $Menus.Split(",")
$mf = 34; $xs = @(); $mw = @()
$tmp = New-Object Drawing.Drawing2D.GraphicsPath
foreach ($m in $menuList) { $pp = New-Object Drawing.Drawing2D.GraphicsPath; $pp.AddString($m, (New-Object Drawing.FontFamily $font), 1, $mf, (New-Object Drawing.PointF 0, 0), [Drawing.StringFormat]::GenericTypographic); $mw += $pp.GetBounds().Width }
$gap = 110; $total = ($mw | Measure-Object -Sum).Sum + $gap * ($menuList.Count - 1); $x = ($W - $total) / 2
for ($i = 0; $i -lt $menuList.Count; $i++) {
  $pp = New-Object Drawing.Drawing2D.GraphicsPath
  $pp.AddString($menuList[$i], (New-Object Drawing.FontFamily $font), 1, $mf, (New-Object Drawing.PointF $x, 527), [Drawing.StringFormat]::GenericTypographic)
  $pen = New-Object Drawing.Pen ([Drawing.Color]::White), 2; $pen.LineJoin = 'Round'; $g.DrawPath($pen, $pp); $g.FillPath([Drawing.Brushes]::White, $pp)
  if ($i -lt $menuList.Count - 1) { Star $g ($x + $mw[$i] + $gap/2) 548 9 (& $C $Acc) }
  $x += $mw[$i] + $gap
}
$bmp.Save((Join-Path $out "stage_1920x600$sfx.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()

# ── 2) 세로 메뉴 위젯 170 x 400 ──
$bmp, $g = Canvas 170 400
Stage $g 170 400 9
Spot $g 20 45 0 110 400; Spot $g 125 150 60 170 400
Star $g 22 30 6 $gold; Star $g 150 64 5 $gold; Star $g 140 20 3 $gold
Spaced $g $WKick 6 30 170 (& $C $Soft) 3
GlowText $g $WTitle1 21 (New-Object Drawing.RectangleF 0, 38, 170, 30) $pinkTop $pinkBot (& $C $Glow) 1
GlowText $g $WTitle2 21 (New-Object Drawing.RectangleF 0, 64, 170, 30) $pinkTop $pinkBot (& $C $Glow) 1
$y = 110; $map = @()
foreach ($m in ($Menus.Split(",") | ForEach-Object { $_ -replace ' · ', '·' })) {
  $rp = New-Object Drawing.Drawing2D.GraphicsPath
  $rp.AddArc(14, $y, 26, 26, 90, 180); $rp.AddArc(130, $y, 26, 26, 270, 180); $rp.CloseFigure()
  $rp2 = New-Object Drawing.Drawing2D.GraphicsPath; $rp2.AddArc(14, $y, 52, 52, 180, 90); $rp2.AddArc(104, $y, 52, 52, 270, 90); $rp2.AddArc(104, $y+12, 52, 52, 0, 90); $rp2.AddArc(14, $y+12, 52, 52, 90, 90); $rp2.CloseFigure()
  $g.FillPath((New-Object Drawing.SolidBrush (& $A 90 (& $C $Band))), $rp2)
  $g.DrawPath((New-Object Drawing.Pen (& $A 170 $pinkBot), 1.5), $rp2)
  $g.DrawString($m, (New-Object Drawing.Font $font, 14, ([Drawing.FontStyle]::Bold)), [Drawing.Brushes]::White, (New-Object Drawing.RectangleF 14, $y, 142, 64), $center)
  $map += "14,$y,156,$($y+64)"
  $y += 72
}
$bmp.Save((Join-Path $out "menu_170x400$sfx.png"), [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()

# ── 3) 프로필 600 x 600 (PC는 네모, 모바일은 동그라미로 잘리므로 내용은 원 안에) ──
$S = 600
$bmp, $g = Canvas $S $S
Stage $g $S $S 21
Spot $g 150 220 40 330 $S; Spot $g 380 450 270 560 $S
# 원 테두리 빛
foreach ($w in @(14, 8, 3)) { $g.DrawEllipse((New-Object Drawing.Pen (& $A ($(if ($w -eq 3) { 200 } else { 40 })) (& $C $T2)), $w), 36, 36, 528, 528) }
if ($Icon -eq "money") {
  # 오르는 막대그래프 3개 + 위로 꺾이는 금색 화살표 + ₩ 동전
  $bars = @(@(212, 205, 44, 60), @(268, 170, 44, 95), @(324, 128, 44, 137))
  foreach ($bv in $bars) {
    $bp = New-Object Drawing.Drawing2D.GraphicsPath; $bp.AddArc($bv[0], $bv[1], 16, 16, 180, 90); $bp.AddArc($bv[0]+$bv[2]-16, $bv[1], 16, 16, 270, 90)
    $bp.AddLine($bv[0]+$bv[2], $bv[1]+$bv[3], $bv[0], $bv[1]+$bv[3]); $bp.CloseFigure()
    $g.FillPath((New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.RectangleF $bv[0], ($bv[1]-1), $bv[2], ($bv[3]+2)), $pinkTop, $pinkBot, 90.0), $bp)
  }
  $ap = New-Object Drawing.Pen $gold, 9; $ap.LineJoin = 'Round'; $ap.StartCap = 'Round'
  $ap.CustomEndCap = New-Object Drawing.Drawing2D.AdjustableArrowCap 3, 3
  $g.DrawLines($ap, @((New-Object Drawing.PointF 200, 190), (New-Object Drawing.PointF 262, 150), (New-Object Drawing.PointF 300, 168), (New-Object Drawing.PointF 382, 100)))
  $cp = New-Object Drawing.Drawing2D.GraphicsPath; $cp.AddEllipse(372, 176, 74, 74)
  $cb2 = New-Object Drawing.Drawing2D.PathGradientBrush $cp; $cb2.CenterPoint = (New-Object Drawing.PointF 395, 198)
  $cb2.CenterColor = (& $C "#FFF3C4"); $cb2.SurroundColors = @((& $C "#E0A82E"))
  $g.FillPath($cb2, $cp); $g.DrawEllipse((New-Object Drawing.Pen (& $C "#B8841C"), 3), 380, 184, 58, 58)
  $g.DrawString("₩", (New-Object Drawing.Font $font, 26, ([Drawing.FontStyle]::Bold)), (New-Object Drawing.SolidBrush (& $C "#8A5F0E")), (New-Object Drawing.RectangleF 372, 176, 74, 76), $center)
} else {
# 마이크: 손잡이(기울인 막대) + 머리(은색 공 + 그물)
$st = $g.Save()
$g.TranslateTransform(315, 168); $g.RotateTransform(40)
$hb = New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.Rectangle -22, 0, 44, 10), (& $C "#5A6478"), (& $C "#1C2230"), 0.0
$hp = New-Object Drawing.Drawing2D.GraphicsPath; $hp.AddArc(-22, 40, 44, 20, 180, 180); $hp.AddLine(22, 50, 14, 175); $hp.AddArc(-14, 165, 28, 20, 0, 180); $hp.AddLine(-14, 175, -22, 50); $hp.CloseFigure()
$g.FillPath($hb, $hp); $g.DrawPath((New-Object Drawing.Pen (& $A 120 ([Drawing.Color]::White)), 1.5), $hp)
$g.FillRectangle((New-Object Drawing.SolidBrush (& $C "#D7E6FF")), -24, 52, 48, 8)
$ball = New-Object Drawing.Drawing2D.GraphicsPath; $ball.AddEllipse(-52, -52, 104, 104)
$bb = New-Object Drawing.Drawing2D.PathGradientBrush $ball; $bb.CenterPoint = (New-Object Drawing.PointF -18, -22)
$bb.CenterColor = [Drawing.Color]::White; $bb.SurroundColors = @((& $C "#6F7F99"))
$g.FillPath($bb, $ball)
$g.SetClip($ball)
$gp = New-Object Drawing.Pen (& $A 90 (& $C "#2B3550")), 1.6
for ($i = -52; $i -le 52; $i += 10) { $g.DrawLine($gp, $i, -52, $i, 52); $g.DrawLine($gp, -52, $i, 52, $i) }
$g.ResetClip()
$g.DrawEllipse((New-Object Drawing.Pen (& $A 160 ([Drawing.Color]::White)), 2), -52, -52, 104, 104)
$g.Restore($st)
}
Star $g 168 150 12 $gold; Star $g 438 128 9 $gold; Star $g 455 250 6 $gold; Star $g 150 268 5 $gold
GlowText $g $PMain $PMainSize (New-Object Drawing.RectangleF 0, 322, $S, 110) $pinkTop $pinkBot (& $C $Glow) 3
GlowText $g $PSub 40 (New-Object Drawing.RectangleF 0, 420, $S, 56) $pinkTop $pinkBot (& $C $Glow) 1
Spaced $g $PKick 12 498 $S (& $C $Soft) 7
$bmp.Save((Join-Path $out "profile_600$sfx.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()
$map -join " | "
