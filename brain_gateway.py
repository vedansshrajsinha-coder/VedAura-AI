from __future__ import annotations

import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

_LOCK = threading.RLock()
_BRAIN = None

def _brain_root() -> Path:
    configured = os.getenv("AI_BRAIN_PATH", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path(__file__).resolve().parent.parent / "AI_BRAIN").resolve()

def _load_brain():
    root = _brain_root()
    if not root.exists():
        raise RuntimeError(f"AI_BRAIN_PATH does not exist: {root}")
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    from ai_brain.app import AIBrain
    return AIBrain(root)

def get_brain():
    global _BRAIN
    with _LOCK:
        if _BRAIN is None:
            _BRAIN = _load_brain()
        return _BRAIN

def _seed_legacy_brain_history(brain, history):
    if not history or not hasattr(brain, "memory"):
        return
    try:
        from memory.system import Turn
    except ImportError:
        return
    turns = []
    for item in history[-12:]:
        role = item.get("role") if isinstance(item, dict) else None
        content = (item.get("content") or item.get("text")) if isinstance(item, dict) else None
        if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
            turns.append(Turn(role, content.strip(), datetime.now(timezone.utc).isoformat()))
    brain.memory.turns = turns

def ask(message, history=None, extra_evidence=None):
    with _LOCK:
        brain = get_brain()
        try:
            return brain.ask(message, history=history, extra_evidence=extra_evidence)
        except TypeError:
            _seed_legacy_brain_history(brain, history or [])
            query = message
            if extra_evidence:
                attachments = []
                for item in extra_evidence:
                    title = item.get("title", "file")
                    text = item.get("text", "")
                    attachments.append(f"Uploaded evidence ({title}):\n{text}")
                query += "\n\n" + "\n\n".join(attachments)
            return brain.ask(query)
