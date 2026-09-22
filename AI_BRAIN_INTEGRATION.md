# VedAura + AI Brain + AI Training

VedAura's normal /chat route now goes through the modular AI Brain.

## Runtime flow

VedAura UI -> /chat -> app.engine -> brain_gateway -> AI Brain -> context -> retrieval -> generation -> verification -> VedAura UI

The existing conversation database remains the source of truth for chat history. The integration reconstructs the current conversation and passes recent turns into the Brain so follow-up questions can use context.

Uploaded TXT/MD/PDF/XLSX/HTML/DOCX/EPUB files are treated as temporary evidence for the current request.

## AI_BRAIN folder

The gateway supports an external sibling folder:

Desktop/
  AI_BRAIN/
  VedAura-AI/

This is the layout already used in local development. If the folders are elsewhere, set AI_BRAIN_PATH in .env.

## AI-training folder

Keep the training project separate from runtime knowledge:

Desktop/
  AI_BRAIN/
  ai-training/
  VedAura-AI/

The training JSONL teaches an LLM behavior through SFT/LoRA; it is not itself a runtime model and should not be pasted into prompts.

After fine-tuning, serve the resulting model through an OpenAI-compatible endpoint or compatible local server and set:

LLM_PROVIDER=openai_compatible
LLM_BASE_URL=http://localhost:8000/v1
LLM_MODEL=<your-fine-tuned-model>

For a hosted provider, use its compatible base URL and model identifier.

## Knowledge books

Put legally usable documents in the AI_BRAIN books/ directory and run the AI Brain ingestion command before expecting them to be available as persistent knowledge.
