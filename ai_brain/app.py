from pathlib import Path
from .config import load_settings
from .db import BrainDB
from embeddings.provider import make_embedder
from retrieval.engine import Retriever
from memory.system import Memory
from generation.brain import Brain
from safety.gates import SafetyGate

class AIBrain:
    """Application-facing facade for the modular AI brain."""
    def __init__(self, root="."):
        self.root = Path(root)
        self.s = load_settings(root)
        self.db = BrainDB(self.root / self.s.db_path)
        self.embedder = make_embedder(self.s)
        self.retriever = Retriever(self.db, self.embedder, self.s)
        self.memory = Memory(self.db, self.s.memory_turns)
        self.brain = Brain(self.s, self.retriever, self.memory)
        self.safety = SafetyGate(self.s.max_input_chars, self.s.max_output_chars)

    def ask(self, q, history=None, extra_evidence=None):
        self.safety.check_input(q)
        result = self.brain.answer(q, history=history, extra_evidence=extra_evidence)
        self.safety.check_output(result["answer"])
        return result

    def close(self):
        self.db.close()
