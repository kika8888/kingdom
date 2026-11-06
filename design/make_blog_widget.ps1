# 네이버 블로그 위젯 직접등록용 세로 메뉴 170 x 400
Add-Type -AssemblyName System.Drawing
$out = Join-Path $PSScriptRoot "blog_home\C_purple"
$a = [Drawing.ColorTranslator]::FromHtml("#5B3FD1"); $b = [Drawing.ColorTranslator]::FromHtml("#9B6BF2")
$font = "Malgun Gothic"
$center = New-Object Drawing.StringFormat; $center.Alignment = 'Center'; $center.LineAlignment = 'Center'
function RR($x, $y, $w, $h, $r) {
  $p = New-Object Drawing.Drawing2D.GraphicsPath
  $p.AddArc($x, $y, $r*2, $r*2, 180, 90); $p.AddArc($x+$w-$r*2, $y, $r*2, $r*2, 270, 90)
  $p.AddArc($x+$w-$r*2, $y+$h-$r*2, $r*2, $r*2, 0, 90); $p.AddArc($x, $y+$h-$r*2, $r*2, $r*2, 90, 90)
  $p.CloseFigure(); return $p
}
$W = 170; $H = 400
$bmp = New-Object Drawing.Bitmap $W, $H; $g = [Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = 'AntiAlias'; $g.TextRenderingHint = 'AntiAlias'; $g.Clear([Drawing.Color]::White)
$box = RR 0 0 ($W-1) ($H-1) 14
$g.FillPath((New-Object Drawing.Drawing2D.LinearGradientBrush (New-Object Drawing.Rectangle 0, 0, $W, $H), $a, $b, 60.0), $box)
$g.FillEllipse((New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb(30, 255, 255, 255))), 90, -40, 130, 130)
$g.DrawString("★ MENU ★", (New-Object Drawing.Font $font, 9, ([Drawing.FontStyle]::Bold)), (New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb(220, 255, 255, 255))), (New-Object Drawing.RectangleF 0, 14, $W, 20), $center)
$g.DrawString("MK 연예계 뉴스", (New-Object Drawing.Font $font, 15, ([Drawing.FontStyle]::Bold)), [Drawing.Brushes]::White, (New-Object Drawing.RectangleF 0, 36, $W, 30), $center)
$g.FillRectangle((New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb(120, 255, 255, 255))), 55, 74, 60, 2)
$menus = @("스타 근황", "결혼·열애", "방송", "이슈")
$y = 96
$map = @()
foreach ($m in $menus) {
  $p = RR 12 $y 146 56 28
  $g.FillPath((New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb(255, 255, 255, 255))), $p)
  $g.DrawString($m, (New-Object Drawing.Font $font, 14, ([Drawing.FontStyle]::Bold)), (New-Object Drawing.SolidBrush ([Drawing.ColorTranslator]::FromHtml("#5B3FD1"))), (New-Object Drawing.RectangleF 12, $y, 146, 56), $center)
  $map += "12,$y,158,$($y+56)"
  $y += 72
}
$bmp.Save((Join-Path $out "menu_170x400.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()
$map -join " | "
