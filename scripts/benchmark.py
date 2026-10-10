import csv
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.rag import rebuild, retrieve
base=Path(__file__).resolve().parents[1]
rebuild()
rows=list(csv.DictReader((base/"tests/ten_questions.csv").open(encoding="utf-8")))
hits=0
for row in rows:
    got=retrieve(row["question"])
    expected=row["expected_source"]
    ok=any(d["source"]==expected for d in got) if expected else not got
    hits+=ok
    print(("PASS" if ok else "FAIL"),row["question"],"->", [x["source"] for x in got])
print(f"Retrieval/abstention success: {hits}/{len(rows)} ({hits/len(rows):.0%})")
print("This is NOT answer correctness or a generative model benchmark.")
