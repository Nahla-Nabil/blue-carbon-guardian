# Final step, done in PowerPoint itself (COM):
#  1) replace every picture named vid_<key> with the matching video from build\media (same position and size, poster frame kept);
#     cover / cells / product videos play automatically with the slide, loop and are muted; the backup demo plays on click with sound;
#  2) save docs\Blue_Carbon_Guardian_final.pptx and docs\Blue_Carbon_Guardian_final.pdf;
#  3) export one PNG per slide to build\render for checking.
# Run after python animate.py:  powershell -ExecutionPolicy Bypass -File deck_pptx\render.ps1
$here = $PSScriptRoot; $root = Split-Path -Parent $here
$src  = Join-Path $here "build\animated.pptx"
$pptx = Join-Path $root "docs\Blue_Carbon_Guardian_final.pptx"
$pdf  = Join-Path $root "docs\Blue_Carbon_Guardian_final.pdf"
$png  = Join-Path $here "build\render"; New-Item -ItemType Directory -Force $png | Out-Null
Get-ChildItem $png -Filter *.png | Remove-Item -Force
$media = Join-Path $here "build\media"
$auto = @{ cover = "cover_scan"; cells = "alert_story"; product = "website" }   # autoplay + loop + muted
# Safety: never touch a PowerPoint the user has open (COM would attach to it, and Quit would close their window).
if (Get-Process POWERPNT -ErrorAction SilentlyContinue) { Write-Error "PowerPoint is open. Close it (save your work first), then run this again."; exit 1 }
$app = New-Object -ComObject PowerPoint.Application
try {
  $deck = $app.Presentations.Open($src, $false, $false, $false)
  foreach ($s in $deck.Slides) {
    $targets = @($s.Shapes | Where-Object { $_.Name -like "vid_*" })
    foreach ($ph in $targets) {
      $key = $ph.Name.Substring(4)
      $file = if ($auto.ContainsKey($key)) { $auto[$key] } else { "demo" }
      $v = $s.Shapes.AddMediaObject2((Join-Path $media "$file.mp4"), 0, -1, $ph.Left, $ph.Top, $ph.Width, $ph.Height)
      $v.Name = "video_$key"
      $v.MediaFormat.SetDisplayPictureFromFile((Join-Path $media "$file.png"))
      while ($v.ZOrderPosition -gt $ph.ZOrderPosition + 1) { $v.ZOrder(3) }   # msoSendBackward: keep the placeholder's layer
      $ph.Delete()
      if ($auto.ContainsKey($key)) {
        $v.MediaFormat.Muted = $true
        $e = $s.TimeLine.MainSequence.AddEffect($v, 83, 0, 2, 1)   # msoAnimEffectMediaPlay, with previous, first in sequence
        $e.Timing.TriggerDelayTime = 0.3
        $v.AnimationSettings.PlaySettings.LoopUntilStopped = -1
        $v.AnimationSettings.PlaySettings.HideWhileNotPlaying = 0
      }
      "slide {0:D2}: {1}.mp4 -> {2}" -f $s.SlideIndex, $file, $v.Name
    }
  }
  $deck.SaveAs($pptx)
  foreach ($s in $deck.Slides) { $s.Export((Join-Path $png ("slide{0:D2}.png" -f $s.SlideIndex)), "PNG", 1920, 1080) }
  $deck.SaveAs($pdf, 32)  # ppSaveAsPDF
  "slides: $($deck.Slides.Count)"
  foreach ($s in $deck.Slides) { "{0:D2}  transition={1}  effects={2}" -f $s.SlideIndex, $s.SlideShowTransition.EntryEffect, $s.TimeLine.MainSequence.Count }
  $deck.Close()
} finally { $app.Quit() }
