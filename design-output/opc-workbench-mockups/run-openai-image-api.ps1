$ErrorActionPreference = "Stop"

$workDir = $PSScriptRoot
$generator = Join-Path $workDir "scripts\generate_openai_images.py"

if (-not $env:OPENAI_API_KEY) {
  throw "OPENAI_API_KEY is not set. The image generation API requires it."
}

if (-not (Test-Path $generator)) {
  throw "Generator not found: $generator"
}

$endpoint = if ($env:OPC_IMAGE_ENDPOINT) { $env:OPC_IMAGE_ENDPOINT } else { "https://ai.input.im/v1/images/generations" }
$model = if ($env:OPC_IMAGE_MODEL) { $env:OPC_IMAGE_MODEL } else { "gpt-image-2" }
$size = if ($env:OPC_IMAGE_SIZE) { $env:OPC_IMAGE_SIZE } else { "2048x1152" }
$quality = if ($env:OPC_IMAGE_QUALITY) { $env:OPC_IMAGE_QUALITY } else { "high" }
$maxAttempts = if ($env:OPC_IMAGE_MAX_ATTEMPTS) { $env:OPC_IMAGE_MAX_ATTEMPTS } else { "3" }
$promptMode = if ($env:OPC_IMAGE_PROMPT_MODE) { $env:OPC_IMAGE_PROMPT_MODE } else { "compact" }

$argsList = @(
  $generator,
  "--work-dir", $workDir,
  "--endpoint", $endpoint,
  "--model", $model,
  "--size", $size,
  "--quality", $quality,
  "--max-attempts", $maxAttempts,
  "--prompt-mode", $promptMode
)

if ($env:OPC_IMAGE_FORCE -eq "1") {
  $argsList += "--force"
}

if ($env:OPC_IMAGE_ONLY) {
  $env:OPC_IMAGE_ONLY.Split(",") |
    ForEach-Object { $_.Trim() } |
    Where-Object { $_ } |
    ForEach-Object {
      $argsList += "--only"
      $argsList += $_
    }
}

python @argsList
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}
