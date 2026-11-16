# 연예 이슈 라운지 — 와인 + 로즈골드 고급형: 대문 1920x600 / 프로필 600x600 / 모바일 커버 1080x1080
# 주의: PowerShell 변수는 대소문자를 가리지 않는다 → 반복문 변수 이름을 위의 이름과 겹치지 않게
param([string]$Title = "연예 이슈 라운지", [string]$Line1 = "연예 이슈", [string]$Line2 = "라운지",
      [string]$Kicker = "ENTERTAINMENT ISSUE LOUNGE", [string]$Menus = "스타 근황,열애 · 결혼,방송 · 예능,화제 이슈")
Add-Type -AssemblyName System.Drawing
$out = Join-Path $PSScriptRoot "blog_home\lounge"
New-Item -ItemType Directory -Force $out | Out-Null
$font = "Malgun Gothic"
function Col($h) { [Drawing.ColorTranslator]::FromHtml($h) }
function Alp($a, $c) { [Drawing.Color]::FromArgb($a, $c) }
$wineEdge = Col "#1A050D"; $wineMid = Col "#5E1530"; $wineBand = Col "#2A0814"
$rgLight = Col "#FFF3EC"; $rgMid = Col "#F0BFA8"; $rgDark = Col "#A9644F"; $rgLow = Col "#F7D3C3"
$champ = Col "#F5DDB5"; $soft = Col "#F3D9D2"
$center = New-Object Drawing.StringFormat; $center.Alignment = 'Center'; $center.LineAlignment = 'Center'

function Canvas($w, $h) {
  $b = New-Object Drawing.Bitmap $w, $h; $g = [Drawing.Graphics]::FromImage($b)
  $g.SmoothingMode = 'AntiAlias'; $g.TextRenderingHint = 'AntiAlias'; $g.InterpolationMode = 'HighQualityBicubic'
  return $b, $g
}
# 로즈골드 금속 붓: 위 밝음 → 가운데 진하게 꺾임 → 아래 다시 밝음
function MetalBrush($rect, $angle) {
  $lb = New-Object Drawing.Drawing2D.LinearGradientBrush $rect, $rgLight, $rgLow, $angle
  $cb = New-Object Drawing.Drawing2D.ColorBlend 5
  $cb.Colors = @($rgLight, $rgMid, $rgDark, $rgMid, $rgLow); $cb.Positions = @([single]0, [single]0.42, [single]0.52, [single]0.7, [single]1)
  $lb.InterpolationColors = $cb; return $lb
}
function Background($g, $w, $h, $seed) {
  $g.Clear($wineEdge)
  $p = New-Object Drawing.Drawing2D.GraphicsPath; $p.AddEllipse(-$w*0.25, -$h*0.7, $w*1.5, $h*1.9)
  $pg = New-Object Drawing.Drawing2D.PathGradientBrush $p; $pg.CenterColor = $wineMid; $pg.SurroundColors = @($wineEdge)
  $g.FillRectangle($pg, 0, 0, $w, $h)
  # 비단결 사선 광택
  foreach ($k in @(@(0.18, 70), @(0.62, 45))) {
    $sx = $w * $k[0]
    $sp = New-Object Drawing.Drawing2D.GraphicsPath
    $sp.AddPolygon(@((New-Object Drawing.PointF $sx, 0), (New-Object Drawing.PointF ($sx + $w*0.12), 0), (New-Object Drawing.PointF ($sx + $w*0.12 - $h*0.6), $h), (New-Object Drawing.PointF ($sx - $h*0.6), $h)))
    $sb = New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.RectangleF ($sx - $h*0.6), 0, ($w*0.12 + $h*0.6), $h), (Alp 0 ([Drawing.Color]::White)), (Alp 0 ([Drawing.Color]::White)), 0.0
    $cb = New-Object Drawing.Drawing2D.ColorBlend 3; $cb.Colors = @((Alp 0 ([Drawing.Color]::White)), (Alp $k[1] (Col "#FFD9CF")), (Alp 0 ([Drawing.Color]::White))); $cb.Positions = @([single]0, [single]0.5, [single]1)
    $sb.InterpolationColors = $cb; $g.FillPath($sb, $sp)
  }
  # 빛망울
  $rnd = New-Object Random $seed
  $cols = @("#F2B6A0", "#C9506E", "#FFD9B8", "#8E2A4A", "#F5DDB5")
  $n = [int]([math]::Max($w, $h) / 20)
  for ($i = 0; $i -lt $n; $i++) {
    $r = $rnd.Next([int]($h*0.04), [int]($h*0.17)); $bx = $rnd.Next(0, $w); $by = $rnd.Next(0, $h)
    $bp = New-Object Drawing.Drawing2D.GraphicsPath; $bp.AddEllipse($bx-$r, $by-$r, $r*2, $r*2)
    $bb = New-Object Drawing.Drawing2D.PathGradientBrush $bp
    $bb.CenterColor = (Alp ($rnd.Next(22, 55)) (Col $cols[$rnd.Next(0, 5)])); $bb.SurroundColors = @([Drawing.Color]::FromArgb(0, 0, 0, 0))
    $g.FillPath($bb, $bp)
  }
  # 아래로 갈수록 살짝 어둡게 (글자가 또렷하게)
  $vb = New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.Rectangle 0, 0, $w, ($h+1)), (Alp 0 $wineEdge), (Alp 120 $wineEdge), 90.0
  $g.FillRectangle($vb, 0, 0, $w, $h)
}
function Sparkle($g, $cx, $cy, $s, $col) {
  $glow = New-Object Drawing.Drawing2D.GraphicsPath; $glow.AddEllipse($cx-$s*2, $cy-$s*2, $s*4, $s*4)
  $gb = New-Object Drawing.Drawing2D.PathGradientBrush $glow; $gb.CenterColor = (Alp 110 $col); $gb.SurroundColors = @([Drawing.Color]::FromArgb(0, 0, 0, 0))
  $g.FillPath($gb, $glow)
  $pts = @(
    (New-Object Drawing.PointF $cx, ($cy-$s)), (New-Object Drawing.PointF ($cx+$s*0.16), ($cy-$s*0.16)),
    (New-Object Drawing.PointF ($cx+$s), $cy), (New-Object Drawing.PointF ($cx+$s*0.16), ($cy+$s*0.16)),
    (New-Object Drawing.PointF $cx, ($cy+$s)), (New-Object Drawing.PointF ($cx-$s*0.16), ($cy+$s*0.16)),
    (New-Object Drawing.PointF ($cx-$s), $cy), (New-Object Drawing.PointF ($cx-$s*0.16), ($cy-$s*0.16)))
  $g.FillPolygon((New-Object Drawing.SolidBrush $col), $pts)
}
function Diamond($g, $cx, $cy, $s) {
  $pts = @((New-Object Drawing.PointF $cx, ($cy-$s)), (New-Object Drawing.PointF ($cx+$s), $cy), (New-Object Drawing.PointF $cx, ($cy+$s)), (New-Object Drawing.PointF ($cx-$s), $cy))
  $g.FillPolygon((MetalBrush (New-Object Drawing.RectangleF ($cx-$s), ($cy-$s), ($s*2), ($s*2)) 90.0), $pts)
}
# 아르데코 이중 액자 + 모서리 장식. 위 가운데 gapW 만큼 선을 비워 둔다(제목 위 글자 자리)
function DecoFrame($g, $x, $y, $w, $h, $gapW) {
  $pen1 = New-Object Drawing.Pen (MetalBrush (New-Object Drawing.RectangleF $x, $y, $w, $h) 0.0), 2.4
  $pen2 = New-Object Drawing.Pen (Alp 150 $rgMid), 1
  $cx = $x + $w / 2
  foreach ($inset in @(@(0, $pen1), @(9, $pen2))) {
    $d = $inset[0]; $pn = $inset[1]; $x1 = $x + $d; $y1 = $y + $d; $x2 = $x + $w - $d; $y2 = $y + $h - $d; $cut = 18
    # 모서리를 깎은 팔각 액자
    $g.DrawLine($pn, ($x1 + $cut), $y1, ($cx - $gapW/2), $y1); $g.DrawLine($pn, ($cx + $gapW/2), $y1, ($x2 - $cut), $y1)
    $g.DrawLine($pn, ($x2 - $cut), $y1, $x2, ($y1 + $cut)); $g.DrawLine($pn, $x2, ($y1 + $cut), $x2, ($y2 - $cut))
    $g.DrawLine($pn, $x2, ($y2 - $cut), ($x2 - $cut), $y2); $g.DrawLine($pn, ($x2 - $cut), $y2, ($x1 + $cut), $y2)
    $g.DrawLine($pn, ($x1 + $cut), $y2, $x1, ($y2 - $cut)); $g.DrawLine($pn, $x1, ($y2 - $cut), $x1, ($y1 + $cut))
    $g.DrawLine($pn, $x1, ($y1 + $cut), ($x1 + $cut), $y1)
  }
  foreach ($pt in @(@($x, $y), @(($x+$w), $y), @($x, ($y+$h)), @(($x+$w), ($y+$h)))) { Diamond $g $pt[0] $pt[1] 7 }
  Diamond $g $cx ($y + $h) 9
}
# 금속 제목: 바깥 번짐 + 어두운 테두리 + 로즈골드 금속면 + 위쪽 얇은 하이라이트
function MetalText($g, $text, $size, $rect, $fat) {
  $p = New-Object Drawing.Drawing2D.GraphicsPath
  $p.AddString($text, (New-Object Drawing.FontFamily $font), [int][Drawing.FontStyle]::Bold, $size, $rect, $center)
  foreach ($gw in @(30, 20, 12)) { $pn = New-Object Drawing.Pen (Alp 18 (Col "#FF9C86")), $gw; $pn.LineJoin = 'Round'; $g.DrawPath($pn, $p) }
  $sh = $p.Clone(); $mx = New-Object Drawing.Drawing2D.Matrix; $mx.Translate(0, [single]($size * 0.05)); $sh.Transform($mx)
  $g.FillPath((New-Object Drawing.SolidBrush (Alp 150 (Col "#12030A"))), $sh)
  $bnd = $p.GetBounds()
  $mb = MetalBrush (New-Object Drawing.RectangleF $bnd.X, ($bnd.Y - 1), $bnd.Width, ($bnd.Height + 2)) 90.0
  $edge = New-Object Drawing.Pen (Col "#5A1A22"), ($fat + 3); $edge.LineJoin = 'Round'; $g.DrawPath($edge, $p)
  if ($fat -gt 0) { $pn = New-Object Drawing.Pen $mb, $fat; $pn.LineJoin = 'Round'; $g.DrawPath($pn, $p) }
  $g.FillPath($mb, $p)
  $hl = New-Object Drawing.Pen (Alp 120 ([Drawing.Color]::White)), 1; $g.DrawPath($hl, $p)
}
function Spaced($g, $text, $size, $cy, $w, $col, $gap) {
  $f = New-Object Drawing.Font $font, $size, ([Drawing.FontStyle]::Bold)
  $ws = @($text.ToCharArray() | ForEach-Object { $g.MeasureString([string]$_, $f).Width * 0.72 })
  $total = ($ws | Measure-Object -Sum).Sum + $gap * ($ws.Count - 1)
  $sx = ($w - $total) / 2
  for ($i = 0; $i -lt $ws.Count; $i++) {
    $g.DrawString([string]$text[$i], $f, (New-Object Drawing.SolidBrush $col), (New-Object Drawing.RectangleF $sx, ($cy - $size), ($ws[$i] + $size), ($size * 2)), (New-Object Drawing.StringFormat))
    $sx += $ws[$i] + $gap
  }
  return $total
}
function SpacedWidth($g, $text, $size, $gap) {
  $f = New-Object Drawing.Font $font, $size, ([Drawing.FontStyle]::Bold)
  $ws = @($text.ToCharArray() | ForEach-Object { $g.MeasureString([string]$_, $f).Width * 0.72 })
  return ($ws | Measure-Object -Sum).Sum + $gap * ($ws.Count - 1)
}
function Subtitle($g, $cy, $w, $size) {
  $sf = New-Object Drawing.Font $font, $size, ([Drawing.FontStyle]::Bold)
  $parts = @(@("오늘 가장 핫한 ", $soft), @("연예 이슈", $champ), @("를 한발 먼저", $soft))
  $fmt = [Drawing.StringFormat]::GenericTypographic.Clone(); $fmt.FormatFlags = $fmt.FormatFlags -bor [Drawing.StringFormatFlags]::MeasureTrailingSpaces
  $tw = ($parts | ForEach-Object { $g.MeasureString($_[0], $sf, 3000, $fmt).Width } | Measure-Object -Sum).Sum
  $sx = ($w - $tw) / 2
  foreach ($pt in $parts) { $g.DrawString($pt[0], $sf, (New-Object Drawing.SolidBrush $pt[1]), $sx, ($cy - $size * 0.7), $fmt); $sx += $g.MeasureString($pt[0], $sf, 3000, $fmt).Width }
}
# 로즈골드 마이크 (가운데 cx, cy, 배율 k, 기울기 45도)
function Mic($g, $cx, $cy, $k) {
  $st = $g.Save()
  $g.TranslateTransform($cx, $cy); $g.ScaleTransform($k, $k); $g.RotateTransform(38)
  $hp = New-Object Drawing.Drawing2D.GraphicsPath
  $hp.AddArc(-22, 40, 44, 20, 180, 180); $hp.AddLine(22, 50, 13, 180); $hp.AddArc(-13, 170, 26, 18, 0, 180); $hp.AddLine(-13, 180, -22, 50); $hp.CloseFigure()
  $g.FillPath((New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.Rectangle -22, 0, 44, 10), (Col "#4A1626"), (Col "#12040A"), 0.0), $hp)
  $g.DrawPath((New-Object Drawing.Pen (Alp 200 $rgMid), 1.6), $hp)
  $g.FillRectangle((MetalBrush (New-Object Drawing.RectangleF -26, 48, 52, 14) 0.0), -26, 48, 52, 14)
  $ball = New-Object Drawing.Drawing2D.GraphicsPath; $ball.AddEllipse(-54, -56, 108, 108)
  $bb = New-Object Drawing.Drawing2D.PathGradientBrush $ball; $bb.CenterPoint = (New-Object Drawing.PointF -20, -26)
  $bb.CenterColor = $rgLight; $bb.SurroundColors = @($rgDark); $g.FillPath($bb, $ball)
  $g.SetClip($ball)
  $gp = New-Object Drawing.Pen (Alp 80 (Col "#4A1626")), 1.5
  for ($i = -56; $i -le 56; $i += 10) { $g.DrawLine($gp, $i, -60, $i + 20, 60); $g.DrawLine($gp, -60, $i, 60, $i - 20) }
  $g.ResetClip()
  $g.DrawEllipse((New-Object Drawing.Pen (Alp 200 $rgLight), 2), -54, -56, 108, 108)
  $g.Restore($st)
}

# ── 1) 대문 1920 x 600 ──
$bmp, $g = Canvas 1920 600
Background $g 1920 600 7
foreach ($sk in @(@(300,120,13), @(1640,150,12), @(1500,420,9), @(420,430,8), @(200,300,6), @(1760,320,6), @(760,40,5), @(1180,46,5))) { Sparkle $g $sk[0] $sk[1] $sk[2] $champ }
# 액자 윗선은 영문 글자 폭만큼 비우고, 글자는 그 선 높이 가운데에
$kw = SpacedWidth $g $Kicker 15 11
DecoFrame $g 470 64 980 384 ($kw + 70)
$null = Spaced $g $Kicker 15 74 1920 $champ 11
Diamond $g (960 - $kw / 2 - 20) 64 5; Diamond $g (960 + $kw / 2 + 20) 64 5
MetalText $g $Title 112 (New-Object Drawing.RectangleF 0, 110, 1920, 190) 4
Subtitle $g 336 1920 23
# 얇은 장식선
$lb = New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.Rectangle 760, 0, 400, 2), (Alp 0 $rgMid), (Alp 0 $rgMid), 0.0
$cb = New-Object Drawing.Drawing2D.ColorBlend 3; $cb.Colors = @((Alp 0 $rgMid), (Alp 230 $rgMid), (Alp 0 $rgMid)); $cb.Positions = @([single]0, [single]0.5, [single]1); $lb.InterpolationColors = $cb
$g.FillRectangle($lb, 760, 388, 400, 2); Diamond $g 960 389 5
# 아래 메뉴 띠
$g.FillRectangle((New-Object Drawing.SolidBrush (Alp 200 $wineBand)), 0, 496, 1920, 104)
$g.FillRectangle((MetalBrush (New-Object Drawing.RectangleF 0, 495, 1920, 2) 0.0), 0, 495, 1920, 2)
$menuList = $Menus.Split(","); $mw = @()
foreach ($mn in $menuList) { $pp = New-Object Drawing.Drawing2D.GraphicsPath; $pp.AddString($mn, (New-Object Drawing.FontFamily $font), 1, 32, (New-Object Drawing.PointF 0, 0), [Drawing.StringFormat]::GenericTypographic); $mw += $pp.GetBounds().Width }
$gap = 120; $mx = (1920 - (($mw | Measure-Object -Sum).Sum + $gap * ($menuList.Count - 1))) / 2
for ($i = 0; $i -lt $menuList.Count; $i++) {
  $pp = New-Object Drawing.Drawing2D.GraphicsPath
  $pp.AddString($menuList[$i], (New-Object Drawing.FontFamily $font), 1, 32, (New-Object Drawing.PointF $mx, 530), [Drawing.StringFormat]::GenericTypographic)
  $bnd = $pp.GetBounds()
  $g.FillPath((MetalBrush (New-Object Drawing.RectangleF $bnd.X, ($bnd.Y - 1), $bnd.Width, ($bnd.Height + 2)) 90.0), $pp)
  if ($i -lt $menuList.Count - 1) { Diamond $g ($mx + $mw[$i] + $gap / 2) 551 6 }
  $mx += $mw[$i] + $gap
}
$bmp.Save((Join-Path $out "lounge_banner_1920x600.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()

# ── 2) 프로필 600 x 600 (모바일 동그라미에도 들어가게 원 안에) ──
$bmp, $g = Canvas 600 600
Background $g 600 600 21
$ring = New-Object Drawing.Pen (MetalBrush (New-Object Drawing.RectangleF 40, 40, 520, 520) 45.0), 5
$g.DrawEllipse((New-Object Drawing.Pen (Alp 40 $rgMid), 16), 40, 40, 520, 520)
$g.DrawEllipse($ring, 40, 40, 520, 520); $g.DrawEllipse((New-Object Drawing.Pen (Alp 150 $rgMid), 1.2), 56, 56, 488, 488)
foreach ($dp in @(@(300, 40), @(560, 300), @(300, 560), @(40, 300))) { Diamond $g $dp[0] $dp[1] 9 }
Mic $g 312 158 0.92
foreach ($sk in @(@(172, 150, 11), @(436, 122, 9), @(450, 250, 6), @(160, 262, 5))) { Sparkle $g $sk[0] $sk[1] $sk[2] $champ }
MetalText $g $Line1 68 (New-Object Drawing.RectangleF 0, 318, 600, 100) 3
$null = Spaced $g "L O U N G E" 18 448 600 $champ 4
$g.FillRectangle((MetalBrush (New-Object Drawing.RectangleF 230, 482, 140, 2) 0.0), 230, 482, 140, 2); Diamond $g 300 483 4
$null = Spaced $g "ENTERTAINMENT ISSUE" 10 506 600 $soft 4
$bmp.Save((Join-Path $out "lounge_profile_600.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()

# ── 3) 모바일 커버 1080 x 1080 (핵심은 가운데) ──
$bmp, $g = Canvas 1080 1080
Background $g 1080 1080 33
$kw = SpacedWidth $g $Kicker 13 7
DecoFrame $g 90 90 900 900 ($kw + 60)
$null = Spaced $g $Kicker 13 99 1080 $champ 7
foreach ($sk in @(@(200, 230, 13), @(880, 260, 11), @(860, 860, 9), @(220, 880, 8))) { Sparkle $g $sk[0] $sk[1] $sk[2] $champ }
Mic $g 548 262 1.1
MetalText $g $Line1 118 (New-Object Drawing.RectangleF 0, 440, 1080, 160) 4
MetalText $g $Line2 96 (New-Object Drawing.RectangleF 0, 580, 1080, 130) 3
Subtitle $g 742 1080 26
$chips = @($Menus.Split(",") | ForEach-Object { $_ -replace ' · ', '·' })
for ($i = 0; $i -lt $chips.Count; $i++) {
  $col = $i % 2; $row = [math]::Floor($i / 2)
  $cx = 540 + ($col - 0.5) * 300; $cy = 810 + $row * 82
  $rp = New-Object Drawing.Drawing2D.GraphicsPath; $rp.AddArc(($cx - 130), $cy, 64, 64, 90, 180); $rp.AddArc(($cx + 66), $cy, 64, 64, 270, 180); $rp.CloseFigure()
  $g.FillPath((New-Object Drawing.SolidBrush (Alp 170 $wineBand)), $rp)
  $g.DrawPath((New-Object Drawing.Pen (MetalBrush (New-Object Drawing.RectangleF ($cx - 130), $cy, 260, 64) 90.0), 2), $rp)
  $g.DrawString($chips[$i], (New-Object Drawing.Font $font, 22, ([Drawing.FontStyle]::Bold)), (New-Object Drawing.SolidBrush $rgLight), (New-Object Drawing.RectangleF ($cx - 130), $cy, 260, 66), $center)
}
$bmp.Save((Join-Path $out "lounge_mobile_1080.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()
"ok"
