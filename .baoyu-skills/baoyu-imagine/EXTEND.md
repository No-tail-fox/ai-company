---
version: 1
default_provider: openai
default_quality: 2k
default_aspect_ratio: "16:9"
default_image_size: null
default_image_api_dialect: openai-native
default_model:
  google: null
  openai: "gpt-image-2"
  azure: null
  openrouter: null
  dashscope: null
  zai: null
  minimax: null
  replicate: null
  jimeng: null
  seedream: null
batch:
  max_workers: 3
  provider_limits:
    openai:
      concurrency: 3
      start_interval_ms: 1100
---
