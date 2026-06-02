"""Quick live check for Wikipedia integration."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.wikipedia_tool import extract_wikipedia_queries, get_wikipedia_context

QUERIES = [
    "Diabetes",
    "What are symptoms of dengue?",
    "I have fever and cough for 3 days",
    "Tell me about asthma treatment",
    "I feel sick",
    "randomxyz123notapage",
]

print("=== Wikipedia live check ===\n")
ok = 0
for q in QUERIES:
    titles = extract_wikipedia_queries(q)
    ctx = get_wikipedia_context(q)
    found = bool(ctx)
    if found:
        ok += 1
    print(f"Q: {q!r}")
    print(f"  titles: {titles[:5]}")
    print(f"  found: {found} ({len(ctx)} chars)")
    if ctx:
        line = ctx.split("\n")[0]
        print(f"  first line: {line[:100]}")
    print()

print(f"Summary: {ok}/{len(QUERIES)} queries returned Wikipedia context")
