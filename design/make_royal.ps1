# 연예 이슈 프리미엄 (라운지 업그레이드) — 로열 네이비 벨벳 + 샴페인 골드 금박
# 대문 1920x600 / 프로필 600x600 / 모바일 커버 1080x1080
# 주의: PowerShell 변수는 대소문자를 가리지 않는다 → 반복문 변수 이름이 위 이름과 겹치지 않게
param([string]$Title = "연예 이슈 프리미엄", [string]$Line1 = "연예 이슈", [string]$Line2 = "프리미엄",
      [string]$Kicker = "PREMIUM ENTERTAINMENT NEWS", [string]$PWord = "P R E M I U M", [string]$PKick = "ENTERTAINMENT NEWS",
      [string]$Menus = "스타 근황,열애 · 결혼,방송 · 예능,화제 이슈")
Add-Type -AssemblyName System.Drawing
$out = Join-Path $PSScriptRoot "blog_home\royal"
New-Item -ItemType Directory -Force $out | Out-Null
$font = "Malgun Gothic"
function Col($h) { [Drawing.ColorTranslator]::FromHtml($h) }
function Alp($a, $c) { [Drawing.Color]::FromArgb($a, $c) }
$navyEdge = Col "#040919"; $navyMid = Col "#17306A"; $navyBand = Col "#060F2B"; $navyDeep = Col "#0A1738"
$gLight = Col "#FFF8E6"; $gMid = Col "#E9CB8B"; $gDark = Col "#8E6B2E"; $gLow = Col "#F5E2B0"; $gEdge = Col "#3A2A0E"
$soft = Col "#E6E1D6"; $champ = Col "#F4DDA6"
$center = New-Object Drawing.StringFormat; $center.Alignment = 'Center'; $center.LineAlignment = 'Center'
$clear = [Drawing.Color]::FromArgb(0, 0, 0, 0)

function Canvas($w, $h) {
  $b = New-Object Drawing.Bitmap $w, $h; $g = [Drawing.Graphics]::FromImage($b)
  $g.SmoothingMode = 'AntiAlias'; $g.TextRenderingHint = 'AntiAlias'; $g.InterpolationMode = 'HighQualityBicubic'
  return $b, $g
}
# 금박 붓: 밝음 → 금 → 진한 띠 → 금 → 밝음 (실제 금속판처럼)
function GoldBrush($rect, $angle) {
  $lb = New-Object Drawing.Drawing2D.LinearGradientBrush $rect, $gLight, $gLow, $angle
  $cb = New-Object Drawing.Drawing2D.ColorBlend 6
  $cb.Colors = @($gLight, $gMid, $gDark, $gMid, $gLight, $gLow)
  $cb.Positions = @([single]0, [single]0.38, [single]0.5, [single]0.66, [single]0.86, [single]1)
  $lb.InterpolationColors = $cb; return $lb
}
function Background($g, $w, $h, $seed) {
  $g.Clear($navyEdge)
  $p = New-Object Drawing.Drawing2D.GraphicsPath; $p.AddEllipse(-$w*0.2, -$h*0.6, $w*1.4, $h*1.8)
  $pg = New-Object Drawing.Drawing2D.PathGradientBrush $p; $pg.CenterColor = $navyMid; $pg.SurroundColors = @($navyEdge)
  $g.FillRectangle($pg, 0, 0, $w, $h)
  # 벨벳 결: 아주 옅은 세로 주름
  $rnd = New-Object Random $seed
  for ($vx = 0; $vx -lt $w; $vx += 6) { $g.FillRectangle((New-Object Drawing.SolidBrush (Alp ($rnd.Next(0, 9)) ([Drawing.Color]::White))), $vx, 0, 3, $h) }
  # 빛망울 (금·푸른빛)
  $cols = @("#E9CB8B", "#4C7BD9", "#FFF1C9", "#2B4FA8", "#C9A35A")
  $n = [int]([math]::Max($w, $h) / 22)
  for ($i = 0; $i -lt $n; $i++) {
    $r = $rnd.Next([int]($h*0.03), [int]($h*0.14)); $bx = $rnd.Next(0, $w); $by = $rnd.Next(0, $h)
    $bp = New-Object Drawing.Drawing2D.GraphicsPath; $bp.AddEllipse($bx-$r, $by-$r, $r*2, $r*2)
    $bb = New-Object Drawing.Drawing2D.PathGradientBrush $bp
    $bb.CenterColor = (Alp ($rnd.Next(20, 50)) (Col $cols[$rnd.Next(0, 5)])); $bb.SurroundColors = @($clear)
    $g.FillPath($bb, $bp)
  }
}
# 위 가운데에서 퍼지는 아르데코 햇살
function Sunburst($g, $cx, $cy, $len, $count, $spread) {
  for ($i = 0; $i -lt $count; $i++) {
    $ang = (180 + (180 - $spread) / 2 + $spread * $i / ($count - 1)) * [math]::PI / 180
    $ex = $cx + [math]::Cos($ang) * $len; $ey = $cy - [math]::Sin($ang) * $len
    $pen = New-Object Drawing.Pen (New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.PointF $cx, $cy), (New-Object Drawing.PointF $ex, $ey), (Alp 70 $gMid), (Alp 0 $gMid)), $(if ($i % 2) { 1.2 } else { 2.4 })
    $g.DrawLine($pen, $cx, $cy, $ex, $ey)
  }
}
# 양쪽 벨벳 커튼 (주름 + 금색 테두리 + 묶음 끈)
function Curtain($g, $x, $w, $h, $left) {
  $folds = 5; $fw = $w / $folds
  for ($i = 0; $i -lt $folds; $i++) {
    $fx = $x + $i * $fw
    $lb = New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.RectangleF $fx, 0, ($fw + 1), $h), $navyDeep, $navyDeep, 0.0
    $cb = New-Object Drawing.Drawing2D.ColorBlend 3; $cb.Colors = @((Col "#050C22"), (Col "#1C3878"), (Col "#050C22")); $cb.Positions = @([single]0, [single]0.5, [single]1)
    $lb.InterpolationColors = $cb; $g.FillRectangle($lb, $fx, 0, ($fw + 1), $h)
  }
  $edgeX = $(if ($left) { $x + $w } else { $x })
  $g.FillRectangle((GoldBrush (New-Object Drawing.RectangleF ($edgeX - 3), 0, 6, $h) 0.0), ($edgeX - 3), 0, 6, $h)
  # 위 금색 커튼봉 장식 띠
  $g.FillRectangle((GoldBrush (New-Object Drawing.RectangleF $x, 0, $w, 14) 90.0), $x, 0, $w, 14)
  # 묶음 끈 (술)
  $ty = $h * 0.62; $tx = $edgeX + $(if ($left) { -18 } else { 18 })
  $g.FillEllipse((GoldBrush (New-Object Drawing.RectangleF ($tx - 13), ($ty - 13), 26, 26) 90.0), ($tx - 13), ($ty - 13), 26, 26)
  $tp = New-Object Drawing.Drawing2D.GraphicsPath
  $tp.AddPolygon(@((New-Object Drawing.PointF ($tx - 9), ($ty + 8)), (New-Object Drawing.PointF ($tx + 9), ($ty + 8)), (New-Object Drawing.PointF ($tx + 15), ($ty + 58)), (New-Object Drawing.PointF ($tx - 15), ($ty + 58))))
  $g.FillPath((GoldBrush (New-Object Drawing.RectangleF ($tx - 15), ($ty + 8), 30, 50) 0.0), $tp)
  # 커튼 안쪽 그림자
  if ($left) { $sx = $x + $w; $c1 = Alp 140 $navyEdge; $c2 = Alp 0 $navyEdge } else { $sx = $x - 60; $c1 = Alp 0 $navyEdge; $c2 = Alp 140 $navyEdge }
  $shade = New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.RectangleF $sx, 0, 60, $h), $c1, $c2, 0.0
  $g.FillRectangle($shade, $sx, 0, 60, $h)
}
function Flash($g, $cx, $cy, $s) {
  $glow = New-Object Drawing.Drawing2D.GraphicsPath; $glow.AddEllipse($cx-$s*2.4, $cy-$s*2.4, $s*4.8, $s*4.8)
  $gb = New-Object Drawing.Drawing2D.PathGradientBrush $glow; $gb.CenterColor = (Alp 130 $gLight); $gb.SurroundColors = @($clear); $g.FillPath($gb, $glow)
  $pts = @(
    (New-Object Drawing.PointF $cx, ($cy-$s*1.6)), (New-Object Drawing.PointF ($cx+$s*0.14), ($cy-$s*0.14)),
    (New-Object Drawing.PointF ($cx+$s*1.6), $cy), (New-Object Drawing.PointF ($cx+$s*0.14), ($cy+$s*0.14)),
    (New-Object Drawing.PointF $cx, ($cy+$s*1.6)), (New-Object Drawing.PointF ($cx-$s*0.14), ($cy+$s*0.14)),
    (New-Object Drawing.PointF ($cx-$s*1.6), $cy), (New-Object Drawing.PointF ($cx-$s*0.14), ($cy-$s*0.14)))
  $g.FillPolygon((New-Object Drawing.SolidBrush $gLight), $pts)
}
function Diamond($g, $cx, $cy, $s) {
  $pts = @((New-Object Drawing.PointF $cx, ($cy-$s)), (New-Object Drawing.PointF ($cx+$s), $cy), (New-Object Drawing.PointF $cx, ($cy+$s)), (New-Object Drawing.PointF ($cx-$s), $cy))
  $g.FillPolygon((GoldBrush (New-Object Drawing.RectangleF ($cx-$s), ($cy-$s), ($s*2), ($s*2)) 90.0), $pts)
}
function Crown($g, $cx, $cy, $s) {
  $p = New-Object Drawing.Drawing2D.GraphicsPath
  $p.AddPolygon(@((New-Object Drawing.PointF ($cx - $s), ($cy + $s*0.55)), (New-Object Drawing.PointF ($cx - $s), ($cy - $s*0.35)),
    (New-Object Drawing.PointF ($cx - $s*0.5), ($cy + $s*0.05)), (New-Object Drawing.PointF $cx, ($cy - $s*0.6)),
    (New-Object Drawing.PointF ($cx + $s*0.5), ($cy + $s*0.05)), (New-Object Drawing.PointF ($cx + $s), ($cy - $s*0.35)), (New-Object Drawing.PointF ($cx + $s), ($cy + $s*0.55))))
  $g.FillPath((GoldBrush (New-Object Drawing.RectangleF ($cx - $s), ($cy - $s*0.6), ($s*2), ($s*1.15)) 90.0), $p)
  $g.DrawPath((New-Object Drawing.Pen $gEdge, 1), $p)
  foreach ($px in @(-1, 0, 1)) { $ox = $cx + $px * $s * $(if ($px -eq 0) { 0 } else { 1 }); $oy = $(if ($px -eq 0) { $cy - $s*0.6 } else { $cy - $s*0.35 }); $g.FillEllipse((New-Object Drawing.SolidBrush $gLight), ($ox - $s*0.13), ($oy - $s*0.13), ($s*0.26), ($s*0.26)) }
}
# 이중 액자 + 모서리 부채 장식 + 윗선 가운데 비우기
function DecoFrame($g, $x, $y, $w, $h, $gapW) {
  $pen1 = New-Object Drawing.Pen (GoldBrush (New-Object Drawing.RectangleF $x, $y, $w, $h) 0.0), 2.6
  $pen2 = New-Object Drawing.Pen (Alp 160 $gMid), 1
  $cx = $x + $w / 2
  foreach ($inset in @(@(0, $pen1), @(10, $pen2))) {
    $d = $inset[0]; $pn = $inset[1]; $x1 = $x + $d; $y1 = $y + $d; $x2 = $x + $w - $d; $y2 = $y + $h - $d; $cut = 22
    $g.DrawLine($pn, ($x1 + $cut), $y1, ($cx - $gapW/2), $y1); $g.DrawLine($pn, ($cx + $gapW/2), $y1, ($x2 - $cut), $y1)
    $g.DrawLine($pn, ($x2 - $cut), $y1, $x2, ($y1 + $cut)); $g.DrawLine($pn, $x2, ($y1 + $cut), $x2, ($y2 - $cut))
    $g.DrawLine($pn, $x2, ($y2 - $cut), ($x2 - $cut), $y2); $g.DrawLine($pn, ($x2 - $cut), $y2, ($x1 + $cut), $y2)
    $g.DrawLine($pn, ($x1 + $cut), $y2, $x1, ($y2 - $cut)); $g.DrawLine($pn, $x1, ($y2 - $cut), $x1, ($y1 + $cut))
    $g.DrawLine($pn, $x1, ($y1 + $cut), ($x1 + $cut), $y1)
  }
  # 모서리 부채(햇살 3줄)
  foreach ($cn in @(@($x, $y, 1, 1), @(($x + $w), $y, -1, 1), @($x, ($y + $h), 1, -1), @(($x + $w), ($y + $h), -1, -1))) {
    foreach ($ln in @(30, 46, 30)) {}
    $px = $cn[0] + $cn[2] * 26; $py = $cn[1] + $cn[3] * 26
    $fp = New-Object Drawing.Pen (Alp 200 $gMid), 1.2
    $g.DrawLine($fp, $px, $py, ($px + $cn[2] * 26), $py); $g.DrawLine($fp, $px, $py, $px, ($py + $cn[3] * 26)); $g.DrawLine($fp, $px, $py, ($px + $cn[2] * 18), ($py + $cn[3] * 18))
    Diamond $g $cn[0] $cn[1] 8
  }
  Diamond $g $cx ($y + $h) 10
}
# 금박 제목: 번짐 + 그림자 + 진한 테두리 + 금박면 + 위쪽 얇은 빛
function GoldText($g, $text, $size, $rect, $fat) {
  $p = New-Object Drawing.Drawing2D.GraphicsPath
  $p.AddString($text, (New-Object Drawing.FontFamily $font), [int][Drawing.FontStyle]::Bold, $size, $rect, $center)
  foreach ($gw in @(34, 22, 12)) { $pn = New-Object Drawing.Pen (Alp 16 $gMid), $gw; $pn.LineJoin = 'Round'; $g.DrawPath($pn, $p) }
  $sh = $p.Clone(); $mx = New-Object Drawing.Drawing2D.Matrix; $mx.Translate(0, [single]($size * 0.06)); $sh.Transform($mx)
  $g.FillPath((New-Object Drawing.SolidBrush (Alp 170 (Col "#01030A"))), $sh)
  $bnd = $p.GetBounds()
  $gb = GoldBrush (New-Object Drawing.RectangleF $bnd.X, ($bnd.Y - 1), $bnd.Width, ($bnd.Height + 2)) 90.0
  $edge = New-Object Drawing.Pen $gEdge, ($fat + 3); $edge.LineJoin = 'Round'; $g.DrawPath($edge, $p)
  if ($fat -gt 0) { $pn = New-Object Drawing.Pen $gb, $fat; $pn.LineJoin = 'Round'; $g.DrawPath($pn, $p) }
  $g.FillPath($gb, $p)
  $g.DrawPath((New-Object Drawing.Pen (Alp 110 ([Drawing.Color]::White)), 1), $p)
}
function SpacedWidth($g, $text, $size, $gap) {
  $f = New-Object Drawing.Font $font, $size, ([Drawing.FontStyle]::Bold)
  $ws = @($text.ToCharArray() | ForEach-Object { $g.MeasureString([string]$_, $f).Width * 0.72 })
  return ($ws | Measure-Object -Sum).Sum + $gap * ($ws.Count - 1)
}
function Spaced($g, $text, $size, $cy, $w, $col, $gap) {
  $f = New-Object Drawing.Font $font, $size, ([Drawing.FontStyle]::Bold)
  $ws = @($text.ToCharArray() | ForEach-Object { $g.MeasureString([string]$_, $f).Width * 0.72 })
  $sx = ($w - (SpacedWidth $g $text $size $gap)) / 2
  for ($i = 0; $i -lt $ws.Count; $i++) {
    $g.DrawString([string]$text[$i], $f, (New-Object Drawing.SolidBrush $col), (New-Object Drawing.RectangleF $sx, ($cy - $size), ($ws[$i] + $size), ($size * 2)), (New-Object Drawing.StringFormat))
    $sx += $ws[$i] + $gap
  }
}
function Subtitle($g, $cy, $w, $size) {
  $sf = New-Object Drawing.Font $font, $size, ([Drawing.FontStyle]::Bold)
  $parts = @(@("오늘 가장 핫한 ", $soft), @("연예 이슈", $champ), @("를 한발 먼저", $soft))
  $fmt = [Drawing.StringFormat]::GenericTypographic.Clone(); $fmt.FormatFlags = $fmt.FormatFlags -bor [Drawing.StringFormatFlags]::MeasureTrailingSpaces
  $tw = ($parts | ForEach-Object { $g.MeasureString($_[0], $sf, 3000, $fmt).Width } | Measure-Object -Sum).Sum
  $sx = ($w - $tw) / 2
  foreach ($pt in $parts) { $g.DrawString($pt[0], $sf, (New-Object Drawing.SolidBrush $pt[1]), $sx, ($cy - $size * 0.7), $fmt); $sx += $g.MeasureString($pt[0], $sf, 3000, $fmt).Width }
}
function GoldLine($g, $cx, $cy, $half) {
  $lb = New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.RectangleF ($cx - $half), 0, ($half * 2), 2), (Alp 0 $gMid), (Alp 0 $gMid), 0.0
  $cb = New-Object Drawing.Drawing2D.ColorBlend 3; $cb.Colors = @((Alp 0 $gMid), (Alp 240 $gMid), (Alp 0 $gMid)); $cb.Positions = @([single]0, [single]0.5, [single]1)
  $lb.InterpolationColors = $cb; $g.FillRectangle($lb, ($cx - $half), $cy, ($half * 2), 2); Diamond $g $cx ($cy + 1) 5
}
# 금 마이크
function Mic($g, $cx, $cy, $k) {
  $st = $g.Save()
  $g.TranslateTransform($cx, $cy); $g.ScaleTransform($k, $k); $g.RotateTransform(38)
  $hp = New-Object Drawing.Drawing2D.GraphicsPath
  $hp.AddArc(-22, 40, 44, 20, 180, 180); $hp.AddLine(22, 50, 13, 180); $hp.AddArc(-13, 170, 26, 18, 0, 180); $hp.AddLine(-13, 180, -22, 50); $hp.CloseFigure()
  $g.FillPath((New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.Rectangle -22, 0, 44, 10), (Col "#1E2C52"), (Col "#03060F"), 0.0), $hp)
  $g.DrawPath((New-Object Drawing.Pen (Alp 220 $gMid), 1.6), $hp)
  $g.FillRectangle((GoldBrush (New-Object Drawing.RectangleF -26, 48, 52, 14) 0.0), -26, 48, 52, 14)
  $ball = New-Object Drawing.Drawing2D.GraphicsPath; $ball.AddEllipse(-54, -56, 108, 108)
  $bb = New-Object Drawing.Drawing2D.PathGradientBrush $ball; $bb.CenterPoint = (New-Object Drawing.PointF -20, -26)
  $bb.CenterColor = $gLight; $bb.SurroundColors = @($gDark); $g.FillPath($bb, $ball)
  $g.SetClip($ball)
  $gp = New-Object Drawing.Pen (Alp 80 $gEdge), 1.5
  for ($i = -56; $i -le 56; $i += 10) { $g.DrawLine($gp, $i, -60, $i + 20, 60); $g.DrawLine($gp, -60, $i, 60, $i - 20) }
  $g.ResetClip()
  $g.DrawEllipse((New-Object Drawing.Pen (Alp 220 $gLight), 2), -54, -56, 108, 108)
  $g.Restore($st)
}
# 월계수: 원호를 따라 잎 (왼쪽·오른쪽)
# 각도 a 는 원의 맨 아래(0도)에서 양옆으로 올라가는 각도. 잎은 원을 따라(접선 방향) 살짝 바깥으로 눕힌다
function Laurel($g, $cx, $cy, $r, $leaves, $a0, $a1) {
  foreach ($side in @(-1, 1)) {
    for ($i = 0; $i -lt $leaves; $i++) {
      $deg = $a0 + $i * (($a1 - $a0) / ($leaves - 1))
      $rad = $deg * [math]::PI / 180
      $lx = $cx + $side * $r * [math]::Sin($rad); $ly = $cy + $r * [math]::Cos($rad)
      $tan = [math]::Atan2(-[math]::Sin($rad), $side * [math]::Cos($rad)) * 180 / [math]::PI
      $st = $g.Save()
      $g.TranslateTransform($lx, $ly); $g.RotateTransform($tan - 90 + $side * 25)
      $lp = New-Object Drawing.Drawing2D.GraphicsPath; $lp.AddEllipse(-6, -15, 12, 30)
      $g.FillPath((GoldBrush (New-Object Drawing.RectangleF -6, -15, 12, 30) 0.0), $lp)
      $g.DrawLine((New-Object Drawing.Pen (Alp 120 $gEdge), 1), 0, -13, 0, 13)
      $g.Restore($st)
    }
  }
}

# ── 1) 대문 1920 x 600 ──
$bmp, $g = Canvas 1920 600
Background $g 1920 600 7
Sunburst $g 960 600 760 34 150
Curtain $g 0 300 600 $true; Curtain $g 1620 300 600 $false
foreach ($fl in @(@(355, 130, 8), @(1565, 150, 8), @(1560, 420, 6), @(360, 420, 6), @(760, 34, 4), @(1180, 40, 4))) { Flash $g $fl[0] $fl[1] $fl[2] }
$kw = SpacedWidth $g $Kicker 15 11
DecoFrame $g 400 72 1120 380 ($kw + 80)
Spaced $g $Kicker 15 82 1920 $champ 11
Crown $g 960 44 20
GoldText $g $Title 100 (New-Object Drawing.RectangleF 0, 118, 1920, 180) 4
Subtitle $g 334 1920 23
GoldLine $g 960 390 210
# 아래 메뉴 띠
$g.FillRectangle((New-Object Drawing.SolidBrush (Alp 225 $navyBand)), 0, 496, 1920, 104)
$g.FillRectangle((GoldBrush (New-Object Drawing.RectangleF 0, 494, 1920, 3) 0.0), 0, 494, 1920, 3)
$g.FillRectangle((New-Object Drawing.SolidBrush (Alp 120 $gMid)), 0, 501, 1920, 1)
$menuList = $Menus.Split(","); $mw = @()
foreach ($mn in $menuList) { $pp = New-Object Drawing.Drawing2D.GraphicsPath; $pp.AddString($mn, (New-Object Drawing.FontFamily $font), 1, 32, (New-Object Drawing.PointF 0, 0), [Drawing.StringFormat]::GenericTypographic); $mw += $pp.GetBounds().Width }
$gap = 120; $mx = (1920 - (($mw | Measure-Object -Sum).Sum + $gap * ($menuList.Count - 1))) / 2
for ($i = 0; $i -lt $menuList.Count; $i++) {
  $pp = New-Object Drawing.Drawing2D.GraphicsPath
  $pp.AddString($menuList[$i], (New-Object Drawing.FontFamily $font), 1, 32, (New-Object Drawing.PointF $mx, 532), [Drawing.StringFormat]::GenericTypographic)
  $bnd = $pp.GetBounds()
  $g.DrawPath((New-Object Drawing.Pen $gEdge, 3), $pp)
  $g.FillPath((GoldBrush (New-Object Drawing.RectangleF $bnd.X, ($bnd.Y - 1), $bnd.Width, ($bnd.Height + 2)) 90.0), $pp)
  if ($i -lt $menuList.Count - 1) { Diamond $g ($mx + $mw[$i] + $gap / 2) 552 6 }
  $mx += $mw[$i] + $gap
}
$bmp.Save((Join-Path $out "royal_banner_1920x600.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()

# ── 2) 프로필 600 x 600 ──
$bmp, $g = Canvas 600 600
Background $g 600 600 21
Sunburst $g 300 300 300 28 360
$g.FillEllipse((New-Object Drawing.SolidBrush (Alp 120 $navyEdge)), 70, 70, 460, 460)
$g.DrawEllipse((New-Object Drawing.Pen (Alp 40 $gMid), 18), 40, 40, 520, 520)
$g.DrawEllipse((New-Object Drawing.Pen (GoldBrush (New-Object Drawing.RectangleF 40, 40, 520, 520) 45.0), 6), 40, 40, 520, 520)
$g.DrawEllipse((New-Object Drawing.Pen (Alp 170 $gMid), 1.2), 58, 58, 484, 484)
foreach ($dp in @(@(300, 40), @(560, 300), @(300, 560), @(40, 300))) { Diamond $g $dp[0] $dp[1] 10 }
Laurel $g 300 300 222 9 50 130
Crown $g 300 104 22
Mic $g 312 180 0.82
foreach ($fl in @(@(186, 172, 7), @(420, 140, 6), @(440, 262, 4))) { Flash $g $fl[0] $fl[1] $fl[2] }
GoldText $g $Line1 64 (New-Object Drawing.RectangleF 0, 316, 600, 96) 3
Spaced $g $PWord 18 444 600 $champ 4
GoldLine $g 300 476 70
Spaced $g $PKick 10 500 600 $soft 4
$bmp.Save((Join-Path $out "royal_profile_600.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()

# ── 3) 모바일 커버 1080 x 1080 ──
$bmp, $g = Canvas 1080 1080
Background $g 1080 1080 33
Sunburst $g 540 1080 1000 40 150
Curtain $g 0 110 1080 $true; Curtain $g 970 110 1080 $false
$kw = SpacedWidth $g $Kicker 13 7
DecoFrame $g 140 120 800 860 ($kw + 70)
Spaced $g $Kicker 13 129 1080 $champ 7
Crown $g 540 196 26
foreach ($fl in @(@(230, 260, 9), @(850, 290, 8), @(840, 900, 6), @(240, 900, 6))) { Flash $g $fl[0] $fl[1] $fl[2] }
Mic $g 552 300 1.0
GoldText $g $Line1 112 (New-Object Drawing.RectangleF 0, 450, 1080, 150) 4
GoldText $g $Line2 92 (New-Object Drawing.RectangleF 0, 584, 1080, 124) 3
Subtitle $g 738 1080 25
GoldLine $g 540 786 160
$chips = @($Menus.Split(",") | ForEach-Object { $_ -replace ' · ', '·' })
for ($i = 0; $i -lt $chips.Count; $i++) {
  $colN = $i % 2; $rowN = [math]::Floor($i / 2)
  $cx = 540 + ($colN - 0.5) * 290; $cy = 812 + $rowN * 80
  $rp = New-Object Drawing.Drawing2D.GraphicsPath; $rp.AddArc(($cx - 125), $cy, 62, 62, 90, 180); $rp.AddArc(($cx + 63), $cy, 62, 62, 270, 180); $rp.CloseFigure()
  $g.FillPath((New-Object Drawing.SolidBrush (Alp 200 $navyBand)), $rp)
  $g.DrawPath((New-Object Drawing.Pen (GoldBrush (New-Object Drawing.RectangleF ($cx - 125), $cy, 250, 62) 90.0), 2), $rp)
  $g.DrawString($chips[$i], (New-Object Drawing.Font $font, 21, ([Drawing.FontStyle]::Bold)), (New-Object Drawing.SolidBrush $gLow), (New-Object Drawing.RectangleF ($cx - 125), $cy, 250, 64), $center)
}
$bmp.Save((Join-Path $out "royal_mobile_1080.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()
"ok"
