import uuid
from flask import Blueprint, jsonify, render_template, request
from .rag import answer, rebuild
from .store import history, save

bp=Blueprint("api",__name__)

@bp.get("/")
def home():
    return render_template("index.html")

@bp.get("/api/health")
def health():
    return jsonify({"status":"ok"})

@bp.post("/api/chat")
def chat():
    data=request.get_json(silent=True) or {}
    question=data.get("message","")
    if not isinstance(question,str) or not question.strip() or len(question)>1500:
        return jsonify({"error":"Enter a question between 1 and 1500 characters."}),400
    session=data.get("session_id")
    try:
        session=str(uuid.UUID(str(session))) if session else str(uuid.uuid4())
    except ValueError:
        return jsonify({"error":"Invalid session ID."}),400
    result=answer(question.strip())
    save(session,"user",question.strip())
    save(session,"assistant",result["answer"])
    return jsonify(dict(result,session_id=session))

@bp.get("/api/history/<session_id>")
def get_history(session_id):
    try:
        session_id=str(uuid.UUID(session_id))
    except ValueError:
        return jsonify({"error":"Invalid session ID."}),400
    return jsonify({"messages":history(session_id)})

@bp.post("/api/reindex")
def reindex():
    # Disable this route for public deployment or protect it with authentication.
    if not request.remote_addr in {"127.0.0.1","::1"}:
        return jsonify({"error":"Local use only"}),403
    return jsonify({"chunks":rebuild()})
