param([string]$C1 = "5B3FD1", [string]$C2 = "9B6BF2")
# 스킨배경(가로 3000, 글자 없음) + 타이틀(966x300, 바탕 투명, 글자만) — 둘을 겹치면 이음새가 없다
Add-Type -AssemblyName System.Drawing
$out = Join-Path $PSScriptRoot "blog_home\C_purple"
$a = [Drawing.ColorTranslator]::FromHtml("#$C1"); $b = [Drawing.ColorTranslator]::FromHtml("#$C2")
$font = "Malgun Gothic"
$center = New-Object Drawing.StringFormat; $center.Alignment = 'Center'; $center.LineAlignment = 'Center'
function Star($g, $cx, $cy, $s, $al) {
  $br = New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb($al, 255, 255, 255))
  $pts = @(
    (New-Object Drawing.PointF $cx, ($cy-$s)), (New-Object Drawing.PointF ($cx+$s*0.22), ($cy-$s*0.22)),
    (New-Object Drawing.PointF ($cx+$s), $cy), (New-Object Drawing.PointF ($cx+$s*0.22), ($cy+$s*0.22)),
    (New-Object Drawing.PointF $cx, ($cy+$s)), (New-Object Drawing.PointF ($cx-$s*0.22), ($cy+$s*0.22)),
    (New-Object Drawing.PointF ($cx-$s), $cy), (New-Object Drawing.PointF ($cx-$s*0.22), ($cy-$s*0.22)))
  $g.FillPolygon($br, $pts)
}

# 1) 스킨배경 3000 x 500 : 가운데가 가장 밝은 보라, 양옆으로 짙어짐 (반복돼도 이음새가 같은 색)
$W = 3000; $H = 500
$bmp = New-Object Drawing.Bitmap $W, $H; $g = [Drawing.Graphics]::FromImage($bmp); $g.SmoothingMode = 'AntiAlias'
$all = New-Object Drawing.Rectangle 0, 0, $W, $H
$lg = New-Object Drawing.Drawing2D.LinearGradientBrush $all, $a, $a, 0.0
$blend = New-Object Drawing.Drawing2D.ColorBlend 3
$blend.Colors = @($a, $b, $a); $blend.Positions = @([single]0, [single]0.5, [single]1)
$lg.InterpolationColors = $blend
$g.FillRectangle($lg, -1, 0, $W + 2, $H)
foreach ($c in @(@(1080, 120, 300, 35), @(1950, 380, 340, 30), @(300, 300, 260, 22), @(2700, 120, 260, 22))) {
  $g.FillEllipse((New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb($c[3], 255, 255, 255))), $c[0]-$c[2]/2, $c[1]-$c[2]/2, $c[2], $c[2])
}
$rnd = New-Object Random 11
for ($i = 0; $i -lt 90; $i++) {
  $sx = $rnd.Next(10, $W-10); $sy = $rnd.Next(10, $H-10)
  if ($sx -gt 1000 -and $sx -lt 2000 -and $sy -gt 120 -and $sy -lt 420) { continue }   # 대문 글자 자리 비우기
  Star $g $sx $sy ($rnd.Next(3, 8)) ($rnd.Next(80, 200))
}
$bmp.Save((Join-Path $out "skin_bg.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()

# 2) 타이틀 966 x 300 : 바탕 투명, 글자와 반짝이만
$bmp = New-Object Drawing.Bitmap 966, 300; $g = [Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = 'AntiAlias'; $g.TextRenderingHint = 'AntiAlias'; $g.Clear([Drawing.Color]::Transparent)
$p = New-Object Drawing.Drawing2D.GraphicsPath
$p.AddArc(383, 46, 36, 36, 90, 180); $p.AddArc(547, 46, 36, 36, 270, 180); $p.CloseFigure()
$g.FillPath((New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb(70, 255, 255, 255))), $p)
$g.DrawString("★ STAR NEWS ★", (New-Object Drawing.Font $font, 13, ([Drawing.FontStyle]::Bold)), [Drawing.Brushes]::White, (New-Object Drawing.RectangleF 383, 46, 200, 36), $center)
$tf = New-Object Drawing.Font $font, 50, ([Drawing.FontStyle]::Bold)
$g.DrawString("MK 연예계 뉴스", $tf, (New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb(90, 40, 10, 100))), (New-Object Drawing.RectangleF 3, 88, 966, 100), $center)
$g.DrawString("MK 연예계 뉴스", $tf, [Drawing.Brushes]::White, (New-Object Drawing.RectangleF 0, 84, 966, 100), $center)
$g.DrawString("오늘 가장 핫한 스타 소식, 한눈에 정리해 드려요", (New-Object Drawing.Font $font, 17, ([Drawing.FontStyle]::Bold)), (New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb(235, 255, 255, 255))), (New-Object Drawing.RectangleF 0, 182, 966, 40), $center)
$g.DrawString("#스타근황   #결혼·열애   #방송   #이슈", (New-Object Drawing.Font $font, 13), (New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb(210, 255, 255, 255))), (New-Object Drawing.RectangleF 0, 232, 966, 36), $center)
Star $g 250 92 18 255; Star $g 716 88 14 240
$bmp.Save((Join-Path $out "title_clear.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()

# 2-1) 보라 바탕이 들어간 타이틀 (배경 가운데를 잘라 깔고 글자를 얹음 — 스킨배경 없이도 보이고, 있으면 이어짐)
$bmp = New-Object Drawing.Bitmap 966, 300; $g = [Drawing.Graphics]::FromImage($bmp)
$bg = [Drawing.Image]::FromFile((Join-Path $out "skin_bg.png"))
$g.DrawImage($bg, (New-Object Drawing.Rectangle 0, 0, 966, 300), (New-Object Drawing.Rectangle 1017, 120, 966, 300), [Drawing.GraphicsUnit]::Pixel); $bg.Dispose()
$t = [Drawing.Image]::FromFile((Join-Path $out "title_clear.png")); $g.DrawImage($t, 0, 0, 966, 300); $t.Dispose()
$bmp.Save((Join-Path $out "title_full.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()

# 3) 미리보기: 화면 폭 1920 에 배경을 깔고 가운데 타이틀
$bmp = New-Object Drawing.Bitmap 1920, 500; $g = [Drawing.Graphics]::FromImage($bmp)
$bg = [Drawing.Image]::FromFile((Join-Path $out "skin_bg.png")); $g.DrawImage($bg, -540, 0, 3000, 500); $bg.Dispose()
$t = [Drawing.Image]::FromFile((Join-Path $out "title_clear.png")); $g.DrawImage($t, 477, 120, 966, 300); $t.Dispose()
$bmp.Save((Join-Path $out "preview_wide.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()
"ok"
