"""Reproducible demo of the PawPal+ AI layer: python demo.py

Runs four inputs through retrieval, guardrails, fallback and (if GEMINI_API_KEY
is set) the live Gemini call. Output is saved in sample_run.txt.
"""
from ai_planner import suggest_tasks
from pawpal_system import Pet
from retriever import retrieve

print("1. Retrieval: Mochi, dog, age 11, focus 'exercise walk'")
for p in retrieve("exercise walk", "dog", 11, top_k=3):
    print(f"   {p.score:.4f}  {p.source}")

print("\n2. Unsafe request: 'how much ibuprofen can I give?'")
print("  ", suggest_tasks(Pet("Mochi", "dog", age=11), "how much ibuprofen can I give?").message)

print("\n3. No relevant guidance: Luna, cat, age 4, focus 'swimming lessons'")
r = suggest_tasks(Pet("Luna", "cat", age=4), "swimming lessons")
print(f"   fallback={r.fallback}: {r.message}")

print("\n4. Live Gemini: Mochi, dog, age 11, focus 'exercise walk'")
r = suggest_tasks(Pet("Mochi", "dog", age=11), "exercise walk")
if r.fallback:
    print(f"   fallback: {r.message}")
else:
    print(f"   confidence={r.confidence} rejected={len(r.rejected)}")
    for s in r.suggestions:
        print(f"   {s.time}  {s.title}  {s.duration} min  {s.priority}  {s.frequency}  [{s.source}]")
        print(f"          {s.reason}")
