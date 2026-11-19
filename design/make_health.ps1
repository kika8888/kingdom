# 매일 건강 노트 — 네이비 + 하늘색: 대문 1920x600 / 프로필 600x600 / 모바일 커버 1080x1080
# 하트 + 심박선(ECG) + 은빛 하늘색 글자 + 이중 액자
# 주의: PowerShell 변수는 대소문자를 가리지 않는다 → 반복문 변수 이름이 위 이름과 겹치지 않게
param([string]$Title = "매일 건강 노트", [string]$Line1 = "매일 건강", [string]$Line2 = "노트",
      [string]$Kicker = "DAILY HEALTH NOTE", [string]$PWord = "N O T E", [string]$PKick = "DAILY HEALTH",
      [string]$Menus = "건강 상식,질환 정보,운동 · 식단,영양 · 약 정보")
Add-Type -AssemblyName System.Drawing
$out = Join-Path $PSScriptRoot "blog_home\health"
New-Item -ItemType Directory -Force $out | Out-Null
$font = "Malgun Gothic"
function Col($h) { [Drawing.ColorTranslator]::FromHtml($h) }
function Alp($a, $c) { [Drawing.Color]::FromArgb($a, $c) }
$navyEdge = Col "#03102A"; $navyMid = Col "#13468A"; $navyBand = Col "#061736"
$sLight = Col "#FFFFFF"; $sMid = Col "#BEE6FF"; $sDark = Col "#3C8ED6"; $sLow = Col "#E4F5FF"; $sEdge = Col "#0A2A57"
$sky = Col "#7FD3FF"; $soft = Col "#D9EAF7"; $hi = Col "#9EE7FF"
$center = New-Object Drawing.StringFormat; $center.Alignment = 'Center'; $center.LineAlignment = 'Center'
$clear = [Drawing.Color]::FromArgb(0, 0, 0, 0)

function Canvas($w, $h) {
  $b = New-Object Drawing.Bitmap $w, $h; $g = [Drawing.Graphics]::FromImage($b)
  $g.SmoothingMode = 'AntiAlias'; $g.TextRenderingHint = 'AntiAlias'; $g.InterpolationMode = 'HighQualityBicubic'
  return $b, $g
}
# 은빛 하늘색 금속 붓
function SkyBrush($rect, $angle) {
  $lb = New-Object Drawing.Drawing2D.LinearGradientBrush $rect, $sLight, $sLow, $angle
  $cb = New-Object Drawing.Drawing2D.ColorBlend 6
  $cb.Colors = @($sLight, $sMid, $sDark, $sMid, $sLight, $sLow)
  $cb.Positions = @([single]0, [single]0.4, [single]0.52, [single]0.68, [single]0.88, [single]1)
  $lb.InterpolationColors = $cb; return $lb
}
function Background($g, $w, $h, $seed) {
  $g.Clear($navyEdge)
  $p = New-Object Drawing.Drawing2D.GraphicsPath; $p.AddEllipse(-$w*0.2, -$h*0.6, $w*1.4, $h*1.8)
  $pg = New-Object Drawing.Drawing2D.PathGradientBrush $p; $pg.CenterColor = $navyMid; $pg.SurroundColors = @($navyEdge)
  $g.FillRectangle($pg, 0, 0, $w, $h)
  $rnd = New-Object Random $seed
  $cols = @("#7FD3FF", "#3C8ED6", "#FFFFFF", "#5FE0E8", "#2B6CC4")
  $n = [int]([math]::Max($w, $h) / 22)
  for ($i = 0; $i -lt $n; $i++) {
    $r = $rnd.Next([int]($h*0.03), [int]($h*0.15)); $bx = $rnd.Next(0, $w); $by = $rnd.Next(0, $h)
    $bp = New-Object Drawing.Drawing2D.GraphicsPath; $bp.AddEllipse($bx-$r, $by-$r, $r*2, $r*2)
    $bb = New-Object Drawing.Drawing2D.PathGradientBrush $bp
    $bb.CenterColor = (Alp ($rnd.Next(18, 45)) (Col $cols[$rnd.Next(0, 5)])); $bb.SurroundColors = @($clear)
    $g.FillPath($bb, $bp)
  }
  # 아래쪽 부드러운 물결 두 줄
  foreach ($wv in @(@(0.80, 28, 90, 2.2), @(0.86, 22, 60, 1.4))) {
    $pts = @(); for ($wx = 0; $wx -le $w; $wx += 8) { $pts += New-Object Drawing.PointF $wx, ($h * $wv[0] + [math]::Sin($wx / $w * 6.28 * 1.5) * $wv[1]) }
    $g.DrawCurve((New-Object Drawing.Pen (Alp $wv[2] $sky), $wv[3]), $pts)
  }
}
# 심박선: 왼쪽 x1 → 오른쪽 x2, 높이 y, 가운데쯤에서 뛰는 모양
function Ecg($g, $x1, $x2, $y, $amp, $width, $alpha) {
  $mid = ($x1 + $x2) / 2
  $pts = @((New-Object Drawing.PointF $x1, $y), (New-Object Drawing.PointF ($mid - 120), $y), (New-Object Drawing.PointF ($mid - 90), ($y - $amp*0.25)),
    (New-Object Drawing.PointF ($mid - 70), $y), (New-Object Drawing.PointF ($mid - 40), $y), (New-Object Drawing.PointF ($mid - 22), ($y + $amp*0.35)),
    (New-Object Drawing.PointF $mid, ($y - $amp)), (New-Object Drawing.PointF ($mid + 22), ($y + $amp*0.55)), (New-Object Drawing.PointF ($mid + 40), $y),
    (New-Object Drawing.PointF ($mid + 80), $y), (New-Object Drawing.PointF ($mid + 105), ($y - $amp*0.3)), (New-Object Drawing.PointF ($mid + 130), $y), (New-Object Drawing.PointF $x2, $y))
  foreach ($gw in @(($width * 5), ($width * 2.5))) { $pn = New-Object Drawing.Pen (Alp ([int]($alpha * 0.15)) $hi), $gw; $pn.LineJoin = 'Round'; $g.DrawLines($pn, $pts) }
  $line = New-Object Drawing.Pen (New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.PointF $x1, $y), (New-Object Drawing.PointF $x2, $y), (Alp 0 $hi), (Alp 0 $hi)), $width
  $cb = New-Object Drawing.Drawing2D.ColorBlend 3; $cb.Colors = @((Alp 0 $hi), (Alp $alpha $hi), (Alp 0 $hi)); $cb.Positions = @([single]0, [single]0.5, [single]1)
  $line.Brush.InterpolationColors = $cb; $line.LineJoin = 'Round'; $g.DrawLines($line, $pts)
}
function Heart($g, $cx, $cy, $s, $withEcg) {
  $p = New-Object Drawing.Drawing2D.GraphicsPath
  $p.AddBezier(($cx), ($cy + $s*0.62), ($cx - $s*1.05), ($cy + $s*0.02), ($cx - $s*0.72), ($cy - $s*0.78), ($cx), ($cy - $s*0.32))
  $p.AddBezier(($cx), ($cy - $s*0.32), ($cx + $s*0.72), ($cy - $s*0.78), ($cx + $s*1.05), ($cy + $s*0.02), ($cx), ($cy + $s*0.62))
  $p.CloseFigure()
  $glow = New-Object Drawing.Drawing2D.GraphicsPath; $glow.AddEllipse($cx - $s*1.3, $cy - $s*1.2, $s*2.6, $s*2.4)
  $gb = New-Object Drawing.Drawing2D.PathGradientBrush $glow; $gb.CenterColor = (Alp 70 $sky); $gb.SurroundColors = @($clear); $g.FillPath($gb, $glow)
  $bnd = $p.GetBounds()
  $g.FillPath((SkyBrush (New-Object Drawing.RectangleF $bnd.X, ($bnd.Y - 1), $bnd.Width, ($bnd.Height + 2)) 90.0), $p)
  $g.DrawPath((New-Object Drawing.Pen (Alp 220 $sLight), 2), $p)
  if ($withEcg) {
    $y = $cy - $s * 0.05
    $pts = @((New-Object Drawing.PointF ($cx - $s*0.62), $y), (New-Object Drawing.PointF ($cx - $s*0.22), $y), (New-Object Drawing.PointF ($cx - $s*0.1), ($y + $s*0.18)),
      (New-Object Drawing.PointF ($cx + $s*0.04), ($y - $s*0.36)), (New-Object Drawing.PointF ($cx + $s*0.18), ($y + $s*0.22)), (New-Object Drawing.PointF ($cx + $s*0.28), $y), (New-Object Drawing.PointF ($cx + $s*0.62), $y))
    $pn = New-Object Drawing.Pen $navyEdge, ($s * 0.07); $pn.LineJoin = 'Round'; $pn.StartCap = 'Round'; $pn.EndCap = 'Round'; $g.DrawLines($pn, $pts)
  }
}
function Plus($g, $cx, $cy, $s, $a) {
  $br = New-Object Drawing.SolidBrush (Alp $a $sLight)
  $g.FillRectangle($br, ($cx - $s*0.18), ($cy - $s*0.5), ($s*0.36), $s); $g.FillRectangle($br, ($cx - $s*0.5), ($cy - $s*0.18), $s, ($s*0.36))
}
function Diamond($g, $cx, $cy, $s) {
  $pts = @((New-Object Drawing.PointF $cx, ($cy-$s)), (New-Object Drawing.PointF ($cx+$s), $cy), (New-Object Drawing.PointF $cx, ($cy+$s)), (New-Object Drawing.PointF ($cx-$s), $cy))
  $g.FillPolygon((SkyBrush (New-Object Drawing.RectangleF ($cx-$s), ($cy-$s), ($s*2), ($s*2)) 90.0), $pts)
}
function DecoFrame($g, $x, $y, $w, $h, $gapW) {
  $pen1 = New-Object Drawing.Pen (SkyBrush (New-Object Drawing.RectangleF $x, $y, $w, $h) 0.0), 2.4
  $pen2 = New-Object Drawing.Pen (Alp 150 $sMid), 1
  $cx = $x + $w / 2
  foreach ($inset in @(@(0, $pen1), @(10, $pen2))) {
    $d = $inset[0]; $pn = $inset[1]; $x1 = $x + $d; $y1 = $y + $d; $x2 = $x + $w - $d; $y2 = $y + $h - $d; $rr = 26
    # 모서리 둥근 액자 (윗선 가운데 비움)
    $g.DrawLine($pn, ($x1 + $rr), $y1, ($cx - $gapW/2), $y1); $g.DrawLine($pn, ($cx + $gapW/2), $y1, ($x2 - $rr), $y1)
    $g.DrawArc($pn, ($x2 - $rr*2), $y1, ($rr*2), ($rr*2), 270, 90); $g.DrawLine($pn, $x2, ($y1 + $rr), $x2, ($y2 - $rr))
    $g.DrawArc($pn, ($x2 - $rr*2), ($y2 - $rr*2), ($rr*2), ($rr*2), 0, 90); $g.DrawLine($pn, ($x2 - $rr), $y2, ($x1 + $rr), $y2)
    $g.DrawArc($pn, $x1, ($y2 - $rr*2), ($rr*2), ($rr*2), 90, 90); $g.DrawLine($pn, $x1, ($y2 - $rr), $x1, ($y1 + $rr))
    $g.DrawArc($pn, $x1, $y1, ($rr*2), ($rr*2), 180, 90)
  }
  Diamond $g $cx ($y + $h) 9
}
function SkyText($g, $text, $size, $rect, $fat) {
  $p = New-Object Drawing.Drawing2D.GraphicsPath
  $p.AddString($text, (New-Object Drawing.FontFamily $font), [int][Drawing.FontStyle]::Bold, $size, $rect, $center)
  foreach ($gw in @(32, 20, 11)) { $pn = New-Object Drawing.Pen (Alp 18 $sky), $gw; $pn.LineJoin = 'Round'; $g.DrawPath($pn, $p) }
  $sh = $p.Clone(); $mx = New-Object Drawing.Drawing2D.Matrix; $mx.Translate(0, [single]($size * 0.06)); $sh.Transform($mx)
  $g.FillPath((New-Object Drawing.SolidBrush (Alp 170 (Col "#010815"))), $sh)
  $bnd = $p.GetBounds()
  $sb = SkyBrush (New-Object Drawing.RectangleF $bnd.X, ($bnd.Y - 1), $bnd.Width, ($bnd.Height + 2)) 90.0
  $edge = New-Object Drawing.Pen $sEdge, ($fat + 3); $edge.LineJoin = 'Round'; $g.DrawPath($edge, $p)
  if ($fat -gt 0) { $pn = New-Object Drawing.Pen $sb, $fat; $pn.LineJoin = 'Round'; $g.DrawPath($pn, $p) }
  $g.FillPath($sb, $p)
  $g.DrawPath((New-Object Drawing.Pen (Alp 120 ([Drawing.Color]::White)), 1), $p)
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
  $parts = @(@("오늘부터 챙기는 ", $soft), @("건강 정보", $hi), @("를 쉽고 정확하게", $soft))
  $fmt = [Drawing.StringFormat]::GenericTypographic.Clone(); $fmt.FormatFlags = $fmt.FormatFlags -bor [Drawing.StringFormatFlags]::MeasureTrailingSpaces
  $tw = ($parts | ForEach-Object { $g.MeasureString($_[0], $sf, 3000, $fmt).Width } | Measure-Object -Sum).Sum
  $sx = ($w - $tw) / 2
  foreach ($pt in $parts) { $g.DrawString($pt[0], $sf, (New-Object Drawing.SolidBrush $pt[1]), $sx, ($cy - $size * 0.7), $fmt); $sx += $g.MeasureString($pt[0], $sf, 3000, $fmt).Width }
}

# ── 1) 대문 1920 x 600 ──
$bmp, $g = Canvas 1920 600
Background $g 1920 600 7
Ecg $g 0 1920 420 50 3 150
foreach ($pl in @(@(300, 140, 22, 70), @(1620, 170, 18, 60), @(1500, 420, 14, 50), @(420, 420, 12, 45), @(1760, 330, 10, 40), @(170, 300, 10, 40))) { Plus $g $pl[0] $pl[1] $pl[2] $pl[3] }
$kw = SpacedWidth $g $Kicker 15 11
DecoFrame $g 470 72 980 380 ($kw + 110)
Spaced $g $Kicker 15 82 1920 $hi 11
Heart $g 960 40 30 $true
SkyText $g $Title 108 (New-Object Drawing.RectangleF 0, 118, 1920, 180) 4
Subtitle $g 336 1920 23
$g.FillRectangle((New-Object Drawing.SolidBrush (Alp 225 $navyBand)), 0, 496, 1920, 104)
$g.FillRectangle((SkyBrush (New-Object Drawing.RectangleF 0, 494, 1920, 3) 0.0), 0, 494, 1920, 3)
$menuList = $Menus.Split(","); $mw = @()
foreach ($mn in $menuList) { $pp = New-Object Drawing.Drawing2D.GraphicsPath; $pp.AddString($mn, (New-Object Drawing.FontFamily $font), 1, 32, (New-Object Drawing.PointF 0, 0), [Drawing.StringFormat]::GenericTypographic); $mw += $pp.GetBounds().Width }
$gap = 120; $mx = (1920 - (($mw | Measure-Object -Sum).Sum + $gap * ($menuList.Count - 1))) / 2
for ($i = 0; $i -lt $menuList.Count; $i++) {
  $pp = New-Object Drawing.Drawing2D.GraphicsPath
  $pp.AddString($menuList[$i], (New-Object Drawing.FontFamily $font), 1, 32, (New-Object Drawing.PointF $mx, 532), [Drawing.StringFormat]::GenericTypographic)
  $bnd = $pp.GetBounds()
  $g.DrawPath((New-Object Drawing.Pen $sEdge, 3), $pp)
  $g.FillPath((SkyBrush (New-Object Drawing.RectangleF $bnd.X, ($bnd.Y - 1), $bnd.Width, ($bnd.Height + 2)) 90.0), $pp)
  if ($i -lt $menuList.Count - 1) { Plus $g ($mx + $mw[$i] + $gap / 2) 552 14 200 }
  $mx += $mw[$i] + $gap
}
$bmp.Save((Join-Path $out "health_banner_1920x600.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()

# ── 2) 프로필 600 x 600 ──
$bmp, $g = Canvas 600 600
Background $g 600 600 21
$g.FillEllipse((New-Object Drawing.SolidBrush (Alp 110 $navyEdge)), 70, 70, 460, 460)
$g.DrawEllipse((New-Object Drawing.Pen (Alp 40 $sky), 18), 40, 40, 520, 520)
$g.DrawEllipse((New-Object Drawing.Pen (SkyBrush (New-Object Drawing.RectangleF 40, 40, 520, 520) 45.0), 6), 40, 40, 520, 520)
$g.DrawEllipse((New-Object Drawing.Pen (Alp 160 $sMid), 1.2), 58, 58, 484, 484)
foreach ($dp in @(@(300, 40), @(560, 300), @(300, 560), @(40, 300))) { Diamond $g $dp[0] $dp[1] 10 }
Ecg $g 70 530 196 70 2.4 140
Heart $g 300 190 92 $true
foreach ($pl in @(@(160, 150, 16, 120), @(440, 140, 12, 110), @(450, 250, 9, 90))) { Plus $g $pl[0] $pl[1] $pl[2] $pl[3] }
SkyText $g $Line1 64 (New-Object Drawing.RectangleF 0, 314, 600, 96) 3
Spaced $g $PWord 18 444 600 $hi 4
$g.FillRectangle((SkyBrush (New-Object Drawing.RectangleF 230, 476, 140, 2) 0.0), 230, 476, 140, 2); Diamond $g 300 477 4
Spaced $g $PKick 10 500 600 $soft 4
$bmp.Save((Join-Path $out "health_profile_600.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()

# ── 3) 모바일 커버 1080 x 1080 ──
$bmp, $g = Canvas 1080 1080
Background $g 1080 1080 33
$kw = SpacedWidth $g $Kicker 14 8
DecoFrame $g 110 110 860 860 ($kw + 70)
Spaced $g $Kicker 14 120 1080 $hi 8
Ecg $g 110 970 300 110 3 150
Heart $g 540 292 130 $true
foreach ($pl in @(@(230, 250, 22, 90), @(860, 280, 18, 80), @(850, 880, 14, 60), @(230, 880, 12, 55))) { Plus $g $pl[0] $pl[1] $pl[2] $pl[3] }
SkyText $g $Line1 116 (New-Object Drawing.RectangleF 0, 440, 1080, 150) 4
SkyText $g $Line2 96 (New-Object Drawing.RectangleF 0, 578, 1080, 124) 3
Subtitle $g 742 1080 25
$chips = @($Menus.Split(",") | ForEach-Object { $_ -replace ' · ', '·' })
for ($i = 0; $i -lt $chips.Count; $i++) {
  $colN = $i % 2; $rowN = [math]::Floor($i / 2)
  $cx = 540 + ($colN - 0.5) * 290; $cy = 806 + $rowN * 80
  $rp = New-Object Drawing.Drawing2D.GraphicsPath; $rp.AddArc(($cx - 125), $cy, 62, 62, 90, 180); $rp.AddArc(($cx + 63), $cy, 62, 62, 270, 180); $rp.CloseFigure()
  $g.FillPath((New-Object Drawing.SolidBrush (Alp 200 $navyBand)), $rp)
  $g.DrawPath((New-Object Drawing.Pen (SkyBrush (New-Object Drawing.RectangleF ($cx - 125), $cy, 250, 62) 90.0), 2), $rp)
  $g.DrawString($chips[$i], (New-Object Drawing.Font $font, 21, ([Drawing.FontStyle]::Bold)), (New-Object Drawing.SolidBrush $sLow), (New-Object Drawing.RectangleF ($cx - 125), $cy, 250, 64), $center)
}
$bmp.Save((Join-Path $out "health_mobile_1080.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()
"ok"
