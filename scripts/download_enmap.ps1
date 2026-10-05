# Download the ordered EnMAP packages from the DLR FTPS delivery server into data\enmap.
# - The password is typed by you, hidden, at run time. It is never saved to a file and never passed on the command line
#   (it is sent to curl through standard input), so it does not appear in process lists or shell history.
# - Uses Windows' built-in curl.exe (explicit FTP over TLS, passive mode). Safe to re-run: unfinished downloads resume.
# Run from the project folder:   powershell -ExecutionPolicy Bypass -File .\scripts\download_enmap.ps1

$ErrorActionPreference = "Stop"
$server = "download.dsda.dlr.de"
$outDir = Join-Path (Split-Path -Parent $PSScriptRoot) "data\enmap"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$user = Read-Host "DLR EOWEB user name (looks like <yourname>-cat1distributor)"
if ([string]::IsNullOrWhiteSpace($user)) { throw "A DLR user name is required." }
$secure = Read-Host "DLR password (typing is hidden)" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
$plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)

# curl reads its options (including the credentials) from stdin with -K -
function Invoke-Curl([string[]]$curlArgs) {
    # escape backslash and double quote so passwords containing them survive curl's config-file quoting
    $u = $user.Replace('\', '\\').Replace('"', '\"'); $p = $plain.Replace('\', '\\').Replace('"', '\"')
    $cfg = "user = `"$u`:$p`""
    $cfg | & curl.exe -K - @curlArgs
}
$common = @("--ssl-reqd", "--ftp-pasv", "--ssl-no-revoke", "--connect-timeout", "30", "--silent", "--show-error")

Write-Host "`nListing files on $server ..."
$list = Invoke-Curl ($common + @("--list-only", "ftp://$server/"))
if ($LASTEXITCODE -ne 0) { $plain = $null; throw "Login or listing failed (curl exit code $LASTEXITCODE). Check the user name and password." }
$files = @($list | Where-Object { $_ -match "\.tar(\.gz)?$|\.zip$" })
if ($files.Count -eq 0) { $plain = $null; Write-Host "No packages found. Server listing was:"; $list; return }
Write-Host ("Found: " + ($files -join ", "))

foreach ($f in $files) {
    $dest = Join-Path $outDir $f
    Write-Host "`nDownloading $f -> $dest (resumes if interrupted)"
    Invoke-Curl ($common + @("--progress-bar", "--retry", "5", "--retry-delay", "5", "-C", "-", "-o", $dest, "ftp://$server/$f"))
    if ($LASTEXITCODE -ne 0) { $plain = $null; throw "Download of $f failed (curl exit code $LASTEXITCODE). Run the script again to resume." }
    Write-Host ("Done: {0:N0} bytes" -f (Get-Item $dest).Length)
}
$plain = $null
Write-Host "`nAll packages saved in $outDir. Tell Claude when it is finished."
