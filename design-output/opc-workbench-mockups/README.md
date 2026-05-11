# OPC Undesigned Page Mockups

This folder contains generation assets for the OPC community pages that do not yet have dedicated frontend designs.

## Scope

This set intentionally excludes pages that already have dedicated frontend designs: AI assistant, AI marketing, AI image, AI video, AI audio, AI coding, and AI writing.

Current generated set:
- `01-home-basic-essentials.png`
- `02-home-growth-center.png`
- `03-order-center.png`
- `04-resource-matchmaking.png`
- `05-project-cocreation.png`
- `06-workbench-overview.png`
- `07-template-toolkit.png`
- `08-ecommerce-operations.png`
- `09-legal-service-desk.png`
- `10-office-productivity.png`

## Files

- `prompt-common.md` - strict shared visual-style prompt based on the provided OPC reference screenshot.
- `prompts/*.md` - page-specific prompts for the 10 target mockups.
- `prompts.json` - structured index consumed by the custom generation script.
- `batch.json` - baoyu-imagine-compatible batch index for the same prompt set.
- `references/style-reference.png` - user-provided OPC style screenshot kept as a visual reference.
- `run-generation.ps1` - repeatable generation command.

## Generate

Set `OPENAI_API_KEY`, then run:

```powershell
.\design-output\opc-workbench-mockups\run-generation.ps1
```

This path reads `prompts.json`, skips PNG files that already exist unless forced, and generates the prompts one by one through the OpenAI-compatible image endpoint:

```powershell
.\design-output\opc-workbench-mockups\run-openai-image-api.ps1
```

Defaults used by the script:
- Endpoint: `https://ai.input.im/v1/images/generations`
- Model: `gpt-image-2`
- Size: `2048x1152`
- Quality: `high`
- Prompt mode: `compact`

Optional overrides:
- `OPC_IMAGE_ENDPOINT`
- `OPC_IMAGE_MODEL`
- `OPC_IMAGE_SIZE`
- `OPC_IMAGE_QUALITY`
- `OPC_IMAGE_PROMPT_MODE=compact` or `full`
- `OPC_IMAGE_FORCE=1`
- `OPC_IMAGE_ONLY=03-order-center,07-template-toolkit`
