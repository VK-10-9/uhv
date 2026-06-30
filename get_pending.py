import generate_explanations
import json
html, qs = generate_explanations.parse_html_questions()
cache = generate_explanations.load_cache()
pending = [q for q in qs if q['q'] not in cache]
print(f"Pending count: {len(pending)}")
for idx, q in enumerate(pending):
    print(f"--- Q{idx+1} ---")
    print(f"Q: {q['q']}")
    print(f"Opts: {q['opts']}")
    print(f"A: {q['a']}")
