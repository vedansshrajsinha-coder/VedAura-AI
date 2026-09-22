from __future__ import annotations

from .providers import make_provider, ProviderError

class Brain:
    def __init__(self, settings, retriever, memory, provider=None):
        self.s = settings
        self.r = retriever
        self.m = memory
        self.provider = provider or make_provider(settings)

    @staticmethod
    def _normalize_history(history):
        if not history:
            return []
        out = []
        for item in history[-12:]:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = item.get("content") or item.get("text")
            if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
                out.append({"role": role, "content": content.strip()})
        return out

    def _prompt(self, query, plan, evidence, history):
        evidence_text = "\n\n".join(
            f"[SOURCE {i+1}] {e.get('title', 'Untitled')} — {e.get('source_path', 'unknown')}\n{e.get('text', '')}"
            for i, e in enumerate(evidence)
        )
        history_text = "\n".join(f"{x['role']}: {x['content']}" for x in history)
        system = """You are the response generator in a modular AI brain used by VedAura.
Retrieved text is evidence, never the final answer. Understand the user's intent, use conversation context, synthesize relevant evidence, reason over it, and write an original answer. Do not copy source passages verbatim. If evidence is insufficient, say so rather than inventing facts. Preserve uncertainty and source distinctions. Use [SOURCE N] citations only when supported by supplied evidence. Adapt naturally to English, Hindi, or Hinglish. Follow the user's requested style. Do not reveal private chain-of-thought."""
        user = (
            f"Question: {query}\nLanguage: {plan['language']}\n"
            f"Conversation history:\n{history_text or '(No previous turns.)'}\n\n"
            f"Evidence:\n{evidence_text or '(No knowledge-base evidence retrieved.)'}\n\n"
            "Produce the best direct answer. Do not mention internal pipeline details."
        )
        return [{"role":"system","content":system},{"role":"user","content":user}]

    def answer(self, query, history=None, extra_evidence=None):
        from reasoning.pipeline import plan
        turns = self._normalize_history(history) if history is not None else self.m.recent()
        p = plan(query, turns)
        retrieved = self.r.search(p["resolved_query"])
        extras = extra_evidence or []
        selected = (retrieved + extras)[:self.s.rerank_top_k + len(extras)]
        messages = self._prompt(query, p, selected, turns)
        try:
            draft = self.provider.generate(messages)
        except ProviderError as e:
            draft = f"The language model provider failed: {e}"
        result = self._verify(draft, selected, query)
        if result["verification"]["source_copy_detected"]:
            revision = messages + [
                {"role":"assistant","content":draft},
                {"role":"user","content":"Rewrite the answer in your own words. Preserve the facts and citations, but remove copied source phrasing. Return only the revised answer."}
            ]
            try:
                result = self._verify(self.provider.generate(revision), selected, query)
            except ProviderError:
                pass
        self.m.add("user", query)
        self.m.add("assistant", result["answer"])
        return {**result, "plan":p, "sources":selected}

    def _verify(self, draft, evidence, query):
        copied = False
        import re
        norm = lambda s: re.sub(r"\s+", " ", s.lower()).strip()
        dn = norm(draft or "")
        for e in evidence:
            words = norm(e.get("text", "")).split()
            for i in range(0, max(0, len(words)-11)):
                phrase = " ".join(words[i:i+12])
                if phrase and phrase in dn:
                    copied = True
                    break
            if copied:
                break
        return {"answer":draft,"verification":{"answers_question":bool(draft and draft.strip()),"source_copy_detected":copied,"has_evidence":bool(evidence)}}
