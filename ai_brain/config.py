from __future__ import annotations
import json, os
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Settings:
    llm_provider: str = "openai_compatible"
    llm_model: str = "gpt-5.5"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    temperature: float = 0.2
    max_output_tokens: int = 1200
    embedding_provider: str = "sentence_transformers"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    db_path: str = "data/brain.sqlite3"
    top_k: int = 8
    rerank_top_k: int = 5
    semantic_weight: float = 0.7
    lexical_weight: float = 0.3
    min_score: float = 0.12
    max_context_chars: int = 18000
    memory_turns: int = 12
    max_long_term_items: int = 100
    copy_similarity_threshold: float = 0.86
    max_input_chars: int = 12000
    max_output_chars: int = 20000

def load_settings(root: str | Path = ".") -> Settings:
    root = Path(root)
    cfg = {}
    p = root / "config" / "default.json"
    if p.exists():
        cfg = json.loads(p.read_text(encoding="utf-8"))
    llm, emb, ret, gen, mem, saf = (cfg.get(k, {}) for k in ("llm","embeddings","retrieval","generation","memory","safety"))
    def env(k, default): return os.getenv(k, default)
    return Settings(
        llm_provider=env("LLM_PROVIDER", llm.get("provider", "openai_compatible")),
        llm_model=env("LLM_MODEL", llm.get("model", "gpt-5.5")),
        llm_base_url=env("LLM_BASE_URL", llm.get("base_url", "https://api.openai.com/v1")),
        llm_api_key=env("LLM_API_KEY", os.getenv("OPENAI_API_KEY", "")),
        temperature=float(env("LLM_TEMPERATURE", llm.get("temperature", 0.2))),
        max_output_tokens=int(env("LLM_MAX_OUTPUT_TOKENS", llm.get("max_output_tokens", 1200))),
        embedding_provider=env("EMBEDDING_PROVIDER", emb.get("provider", "sentence_transformers")),
        embedding_model=env("EMBEDDING_MODEL", emb.get("model", "sentence-transformers/all-MiniLM-L6-v2")),
        db_path=env("DB_PATH", "data/brain.sqlite3"),
        top_k=int(env("TOP_K", ret.get("top_k", 8))),
        rerank_top_k=int(env("RERANK_TOP_K", ret.get("rerank_top_k", 5))),
        semantic_weight=float(ret.get("semantic_weight", .7)),
        lexical_weight=float(ret.get("lexical_weight", .3)),
        min_score=float(ret.get("min_score", .12)),
        max_context_chars=int(env("MAX_CONTEXT_CHARS", gen.get("max_context_chars", 18000))),
        memory_turns=int(env("MEMORY_TURNS", mem.get("turns", 12))),
        max_long_term_items=int(mem.get("max_long_term_items", 100)),
        copy_similarity_threshold=float(gen.get("copy_similarity_threshold", .86)),
        max_input_chars=int(saf.get("max_input_chars", 12000)),
        max_output_chars=int(saf.get("max_output_chars", 20000)),
    )
