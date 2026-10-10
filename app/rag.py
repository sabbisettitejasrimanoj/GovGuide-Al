import os
import re
from pathlib import Path
import requests
import yaml
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Optional
from scipy.sparse import spmatrix
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"


DOCS: list[dict] = []
VECTORIZER: Optional[TfidfVectorizer] = None
MATRIX: Optional[spmatrix] = None

def parse_note(path):
    raw = path.read_text(encoding="utf-8", errors="replace")
    meta = {}
    if raw.startswith("---\n"):
        parts = raw.split("---", 2)
        if len(parts) == 3:
            meta = yaml.safe_load(parts[1]) or {}
            raw = parts[2]
    return raw.strip(), meta

def chunks(raw):
    # Keep Markdown sections together for interpretable citations.
    segments = re.split(r"(?=^## )", raw, flags=re.M)
    title = segments[0].strip().splitlines()[0] if segments[0].strip() else ""
    for s in segments:
        s = s.strip()
        if s and len(s) > 35:
            # Prevent oversized document chunks.
            for start in range(0, len(s), 1400):
                yield (title + "\n" + s[start:start+1400]).strip()

def rebuild():
    global DOCS, VECTORIZER, MATRIX
    docs = []
    for path in sorted(KNOWLEDGE.rglob("*.md")):
        if path.name in {"index.md", "log.md"}:
            continue
        raw, meta = parse_note(path)
        for i, section in enumerate(chunks(raw)):
            docs.append({"text":section, "source":str(path.relative_to(KNOWLEDGE)).replace("\\","/"),
                         "section":i, "title":meta.get("title",path.stem),
                         "status":meta.get("status","draft"),
                         "url":meta.get("source_url",""),
                         "verified":str(meta.get("verified",""))})
    DOCS = docs
    if docs:
        VECTORIZER = TfidfVectorizer(ngram_range=(1,2), sublinear_tf=True, strip_accents="unicode")
        MATRIX = VECTORIZER.fit_transform([d["text"] for d in docs])
    else:
        VECTORIZER = MATRIX = None
    return len(docs)

import re

def requires_current_facts(question):
    q = question.lower()

    current_terms = [
        "current", "latest", "this month",
        "today", "now", "deadline",
        "last date", "how much money",
        "exact amount", "payment amount"
    ]

    return any(term in q for term in current_terms)

def retrieve(question, top_k=3):
    if MATRIX is None:
        rebuild()

    if not DOCS:
        return []

    if requires_current_facts(question):
        return []

    if VECTORIZER is None or MATRIX is None:
        rebuild()

    if VECTORIZER is None or MATRIX is None:
        return []

    query = VECTORIZER.transform([question])
    scores = cosine_similarity(query, MATRIX)[0]

    q = question.lower()

    topic_keywords = {
        "scholarship": "schemes/scholarships.md",
        "scholarships": "schemes/scholarships.md",
        "eligibility": "guides/eligibility.md",
        "verify": "safety/source-verification.md",
        "verification": "safety/source-verification.md",
        "official evidence": "safety/source-verification.md",
        "otp": "safety/privacy.md",
    }

    for keyword, source in topic_keywords.items():
        if re.search(r"\b" + re.escape(keyword) + r"\b", q):
            for i, doc in enumerate(DOCS):
                if doc["source"] == source:
                    scores[i] += 0.35

    threshold = float(
        os.getenv("MIN_SIMILARITY", "0.10")
    )

    ranked = scores.argsort()[::-1]

    results = []
    seen_sources = set()

    for i in ranked:
        if scores[i] < threshold:
            continue

        doc = DOCS[i]

        if doc["source"] in seen_sources:
            continue

        results.append(
            dict(doc, score=round(float(scores[i]), 3))
        )

        seen_sources.add(doc["source"])

        if len(results) >= top_k:
            break

    return results

def extractive_answer(hits):
    # Strictly quote the retrieved source; no fabricated government benefits.
    best = hits[0]
    lines = [x.strip() for x in best["text"].splitlines()
             if x.strip() and not x.startswith("#")]
    return ("Based on the available project knowledge:\n\n" +
            "\n".join(lines[:9]) +
            "\n\nThis is draft guidance, not an official eligibility decision. "
            "Check the cited official portal for current scheme details.")

def ollama_answer(question, hits):
    import requests

    context = "\n\n".join(
        f"Source: {h['source']}\n{h['text'][:500]}"
        for h in hits[:2]
    )

    system = (
        "You are GovGuide AI, an Indian government scheme assistant. "
        "Answer using only the provided context. "
        "If information is missing, say you don't know. "
        "Never invent eligibility rules, amounts, or deadlines. "
        "Never ask for OTPs or personal identity numbers. "
        "Give a short, clear answer."
    )

    payload = {
        "model": os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b"),
        "stream": False,
        "keep_alive": "5m",
        "messages": [
            {
                "role": "system",
                "content": system
            },
            {
                "role": "user",
                "content": (
                    f"Context:\n{context}\n\n"
                    f"Question: {question}"
                )
            }
        ],
        "options": {
            "temperature": 0,
            "num_predict": 120,
            "num_ctx": 2048
        }
    }

    url = (
        os.getenv(
            "OLLAMA_URL",
            "http://127.0.0.1:11434"
        ).rstrip("/")
        + "/api/chat"
    )

    response = requests.post(
        url,
        json=payload,
        timeout=(10, 60)
    )

    response.raise_for_status()

    data = response.json()

    return data["message"]["content"].strip()
def answer(question):
    hits = retrieve(question)

    if not hits:
        return {
            "answer": (
                "I don't know from the available documents. "
                "Please check an official government portal "
                "or add verified scheme documents."
            ),
            "sources": [],
            "mode": "no_match"
        }

    # Always create sources before calling Ollama.
    sources = [
        {
            "file": h["source"],
            "title": h["title"],
            "status": h["status"],
            "url": h["url"],
            "score": h["score"]
        }
        for h in hits
    ]

    mode = os.getenv("RAG_MODE", "extractive").lower()

    if mode == "ollama":
        try:
            response = ollama_answer(question, hits)
            mode = "ollama"

        except (requests.RequestException, KeyError, ValueError) as exc:
            print(
                f"[OLLAMA ERROR] {type(exc).__name__}: {exc}",
                flush=True
            )

            response = (
                extractive_answer(hits)
                + "\n\nAI generation is temporarily unavailable. "
                "Showing retrieved knowledge instead."
            )

            mode = "extractive_fallback"

    else:
        response = extractive_answer(hits)
        mode = "extractive"

    return {
        "answer": response,
        "sources": sources,
        "mode": mode
    }