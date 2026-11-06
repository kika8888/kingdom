param([string]$Name = "", [string]$C1 = "FF5EA8", [string]$C2 = "844CE6")
Add-Type -AssemblyName System.Drawing
$out = Join-Path $PSScriptRoot ("blog_home" + $(if ($Name) { "\$Name" } else { "" }))
New-Item -ItemType Directory -Force $out | Out-Null
$pink = [Drawing.ColorTranslator]::FromHtml("#$C1")
$purple = [Drawing.ColorTranslator]::FromHtml("#$C2")
$deep = [Drawing.Color]::FromArgb(255, 74, 32, 140)
$font = "Malgun Gothic"

function New-Canvas($w, $h) {
  $bmp = New-Object Drawing.Bitmap $w, $h
  $g = [Drawing.Graphics]::FromImage($bmp)
  $g.SmoothingMode = 'AntiAlias'; $g.TextRenderingHint = 'AntiAlias'; $g.InterpolationMode = 'HighQualityBicubic'
  return $bmp, $g
}
function Round-Rect($x, $y, $w, $h, $r) {
  $p = New-Object Drawing.Drawing2D.GraphicsPath
  $p.AddArc($x, $y, $r*2, $r*2, 180, 90); $p.AddArc($x+$w-$r*2, $y, $r*2, $r*2, 270, 90)
  $p.AddArc($x+$w-$r*2, $y+$h-$r*2, $r*2, $r*2, 0, 90); $p.AddArc($x, $y+$h-$r*2, $r*2, $r*2, 90, 90)
  $p.CloseFigure(); return $p
}
function Star($g, $cx, $cy, $s, $a) {
  $b = New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb($a, 255, 255, 255))
  $pts = @(
    (New-Object Drawing.PointF $cx, ($cy-$s)), (New-Object Drawing.PointF ($cx+$s*0.22), ($cy-$s*0.22)),
    (New-Object Drawing.PointF ($cx+$s), $cy), (New-Object Drawing.PointF ($cx+$s*0.22), ($cy+$s*0.22)),
    (New-Object Drawing.PointF $cx, ($cy+$s)), (New-Object Drawing.PointF ($cx-$s*0.22), ($cy+$s*0.22)),
    (New-Object Drawing.PointF ($cx-$s), $cy), (New-Object Drawing.PointF ($cx-$s*0.22), ($cy-$s*0.22)))
  $g.FillPolygon($b, $pts)
}
$center = New-Object Drawing.StringFormat; $center.Alignment = 'Center'; $center.LineAlignment = 'Center'

# ── 대문(타이틀) 966 x 300 ──
$W = 966; $H = 300
$bmp, $g = New-Canvas $W $H
$rect = New-Object Drawing.Rectangle 0, 0, $W, $H
$g.FillRectangle((New-Object Drawing.Drawing2D.LinearGradientBrush $rect, $pink, $purple, 20.0), $rect)
# 부드러운 빛 원
foreach ($c in @(@(120, 40, 260, 40), @(820, 230, 300, 35), @(560, -80, 220, 25))) {
  $g.FillEllipse((New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb($c[3], 255, 255, 255))), $c[0]-$c[2]/2, $c[1]-$c[2]/2, $c[2], $c[2])
}
$rnd = New-Object Random 7
$n = 0
while ($n -lt 26) {   # 글자 있는 가운데(가로 200~766)는 피해서
  $sx = $rnd.Next(20, $W-20); $sy = $rnd.Next(15, $H-15)
  if ($sx -gt 200 -and $sx -lt 766 -and $sy -gt 40 -and $sy -lt 270) { continue }
  Star $g $sx $sy ($rnd.Next(3, 9)) ($rnd.Next(90, 220)); $n++
}
Star $g 250 92 18 255; Star $g 716 88 14 240
# 작은 꼬리표
$tag = Round-Rect 383 46 200 36 18
$g.FillPath((New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb(70, 255, 255, 255))), $tag)
$g.DrawString("★ STAR NEWS ★", (New-Object Drawing.Font $font, 13, ([Drawing.FontStyle]::Bold)), [Drawing.Brushes]::White, (New-Object Drawing.RectangleF 383, 46, 200, 36), $center)
# 제목 (그림자 + 흰 글씨)
$tf = New-Object Drawing.Font $font, 50, ([Drawing.FontStyle]::Bold)
$g.DrawString("MK 연예계 정보", $tf, (New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb(90, 60, 10, 110))), (New-Object Drawing.RectangleF 3, 88, $W, 100), $center)
$g.DrawString("MK 연예계 정보", $tf, [Drawing.Brushes]::White, (New-Object Drawing.RectangleF 0, 84, $W, 100), $center)
$g.DrawString("오늘 가장 핫한 스타 소식, 한눈에 정리해 드려요", (New-Object Drawing.Font $font, 17, ([Drawing.FontStyle]::Bold)), (New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb(235, 255, 255, 255))), (New-Object Drawing.RectangleF 0, 182, $W, 40), $center)
# 아래 키워드 띠
$g.DrawString("#스타근황   #결혼·열애   #방송   #이슈", (New-Object Drawing.Font $font, 13), (New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb(210, 255, 255, 255))), (New-Object Drawing.RectangleF 0, 232, $W, 36), $center)
$bmp.Save((Join-Path $out "title.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()

# ── 메뉴 버튼 160 x 52 (네이버 위젯 폭 170 이하) ──
$menus = @(@("star", "⭐ 스타 근황"), @("love", "💍 결혼·열애"), @("tv", "📺 방송"), @("issue", "🔥 이슈"))
foreach ($m in $menus) {
  $bmp, $g = New-Canvas 160 52
  $g.Clear([Drawing.Color]::Transparent)
  $p = Round-Rect 2 2 155 47 23
  $r = New-Object Drawing.Rectangle 0, 0, 160, 52
  $g.FillPath((New-Object Drawing.Drawing2D.LinearGradientBrush $r, $pink, $purple, 0.0), $p)
  $g.DrawPath((New-Object Drawing.Pen ([Drawing.Color]::FromArgb(200, 255, 255, 255)), 2), $p)
  $label = $m[1] -replace '^\S+\s', ''   # 이모지는 윈도 글꼴에서 깨지므로 글자만
  $g.DrawString($label, (New-Object Drawing.Font $font, 15, ([Drawing.FontStyle]::Bold)), [Drawing.Brushes]::White, (New-Object Drawing.RectangleF 0, 1, 160, 50), $center)
  $bmp.Save((Join-Path $out "menu_$($m[0]).png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()
}

# ── 미리보기: 대문 아래 버튼 4개 ──
$bmp, $g = New-Canvas 966 380
$g.Clear([Drawing.Color]::FromArgb(255, 250, 247, 252))
$t = [Drawing.Image]::FromFile((Join-Path $out "title.png")); $g.DrawImage($t, 0, 0, 966, 300); $t.Dispose()
$x = (966 - (4*160 + 3*24)) / 2
foreach ($m in $menus) { $i = [Drawing.Image]::FromFile((Join-Path $out "menu_$($m[0]).png")); $g.DrawImage($i, $x, 314, 160, 52); $i.Dispose(); $x += 184 }
$bmp.Save((Join-Path $out "preview.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()
Get-ChildItem $out | Select-Object Name, Length
