# 무대 대문·메뉴 위젯 색만 바꾼 버전 (색상환 회전) + 비교 이미지
Add-Type -AssemblyName System.Drawing
$dir = Join-Path $PSScriptRoot "blog_home\stage"
function HueMatrix([double]$deg) {
  $r = $deg * [Math]::PI / 180; $c = [Math]::Cos($r); $s = [Math]::Sin($r)
  $m = New-Object Drawing.Imaging.ColorMatrix
  $m.Matrix00 = .213 + $c*.787 - $s*.213; $m.Matrix10 = .715 - $c*.715 - $s*.715; $m.Matrix20 = .072 - $c*.072 + $s*.928
  $m.Matrix01 = .213 - $c*.213 + $s*.143; $m.Matrix11 = .715 + $c*.285 + $s*.140; $m.Matrix21 = .072 - $c*.072 - $s*.283
  $m.Matrix02 = .213 - $c*.213 - $s*.787; $m.Matrix12 = .715 - $c*.715 + $s*.715; $m.Matrix22 = .072 + $c*.928 + $s*.072
  $m.Matrix33 = 1; $m.Matrix44 = 1
  return $m
}
$variants = @(@("1_blue", 60), @("2_red", -60), @("3_green", 140))
foreach ($v in $variants) {
  foreach ($f in "stage_1920x600", "menu_170x400") {
    $src = [Drawing.Image]::FromFile((Join-Path $dir "$f.png"))
    $bmp = New-Object Drawing.Bitmap $src.Width, $src.Height; $g = [Drawing.Graphics]::FromImage($bmp)
    $ia = New-Object Drawing.Imaging.ImageAttributes; $ia.SetColorMatrix((HueMatrix $v[1]))
    $g.DrawImage($src, (New-Object Drawing.Rectangle 0, 0, $src.Width, $src.Height), 0, 0, $src.Width, $src.Height, [Drawing.GraphicsUnit]::Pixel, $ia)
    $bmp.Save((Join-Path $dir "$($f)_$($v[0]).png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose(); $src.Dispose()
  }
}
# 비교: 원본(보라) + 3가지, 대문 축소 + 위젯
$bmp = New-Object Drawing.Bitmap 1180, 1260; $g = [Drawing.Graphics]::FromImage($bmp); $g.Clear([Drawing.Color]::White)
$g.TextRenderingHint = 'AntiAlias'; $g.InterpolationMode = 'HighQualityBicubic'
$y = 0
foreach ($n in @(@("", "0번 보라 (기존 연예 블로그와 같은 색)"), @("_1_blue", "1번 파랑"), @("_2_red", "2번 레드·와인"), @("_3_green", "3번 청록"))) {
  $g.DrawString($n[1], (New-Object Drawing.Font "Malgun Gothic", 15, ([Drawing.FontStyle]::Bold)), [Drawing.Brushes]::Black, 6, $y + 4)
  $a = [Drawing.Image]::FromFile((Join-Path $dir "stage_1920x600$($n[0]).png")); $g.DrawImage($a, 0, $y + 34, 960, 300); $a.Dispose()
  $b = [Drawing.Image]::FromFile((Join-Path $dir "menu_170x400$($n[0]).png")); $g.DrawImage($b, 990, $y + 34, 113, 266); $b.Dispose()
  $y += 315
}
$bmp.Save((Join-Path $dir "compare.png"), [Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()
"ok"
