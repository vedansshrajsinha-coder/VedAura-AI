# AI Training connection

The complete training-data project is maintained separately at the local ai-training/ folder supplied with this project.

Recommended local layout:

Desktop/
  AI_BRAIN/
  ai-training/
  VedAura-AI/

The training project contains JSONL train/validation/test data, preprocessing, validation, and SFT configuration.

Do not copy raw training JSONL into the runtime prompt. Train/fine-tune an LLM first, serve the resulting model, then point VedAura's AI Brain provider at that model using LLM_BASE_URL and LLM_MODEL.

This separation prevents the training corpus from being confused with the AI Brain's runtime knowledge base.
