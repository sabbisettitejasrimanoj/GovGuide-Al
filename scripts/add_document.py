import argparse
import re
import shutil
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.rag import KNOWLEDGE,rebuild

parser=argparse.ArgumentParser(description="Import a locally downloaded official PDF or Markdown file")
parser.add_argument("file",type=Path)
parser.add_argument("--source-url",required=True,help="Actual official source URL")
parser.add_argument("--title",required=True)
args=parser.parse_args()
if not args.file.is_file() or args.file.suffix.lower() not in {".pdf",".md",".txt"}:
    parser.error("Provide an existing PDF, MD or TXT file")
if not args.source_url.startswith("https://"):
    parser.error("Use an HTTPS official source URL")
if args.file.stat().st_size > 8*1024*1024:
    parser.error("Maximum 8 MB")
if args.file.suffix.lower()==".pdf":
    import fitz
    with fitz.open(args.file) as pdf:
        text="\n".join(page.get_text() for page in pdf)
else:
    text=args.file.read_text(encoding="utf-8")
if len(text.strip())<100:
    parser.error("Not enough extractable text (scanned PDF may require OCR)")
safe=re.sub(r"[^a-z0-9-]+","-",args.title.lower()).strip("-")[:60] or "document"
dest=KNOWLEDGE/"imported"/(safe+".md")
dest.parent.mkdir(exist_ok=True)
# Imported docs remain draft until a human reviews them.
dest.write_text("---\ntype: Source\ntitle: "+repr(args.title)+
                "\nstatus: draft\nsource_url: "+repr(args.source_url)+
                "\n---\n# "+args.title+"\n\n"+text,encoding="utf-8")
print("Imported:",dest,"| chunks:",rebuild())
