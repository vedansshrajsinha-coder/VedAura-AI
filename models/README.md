# Model connection

VedAura uses the AI Brain provider layer.

The ai-training JSONL files are training inputs, not a model. After SFT/LoRA produces a model, serve it through an OpenAI-compatible endpoint (or a compatible local server), then configure LLM_PROVIDER, LLM_BASE_URL, and LLM_MODEL.

This keeps the UI, memory, retrieval, and knowledge system independent from the model implementation.
