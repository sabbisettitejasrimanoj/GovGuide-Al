from app import create_app
from app.rag import rebuild

def test_health():
    c=create_app().test_client()
    assert c.get("/api/health").json["status"]=="ok"

def test_empty_question():
    c=create_app().test_client()
    assert c.post("/api/chat",json={"message":""}).status_code==400

def test_rag_response():
    rebuild()
    c=create_app().test_client()
    r=c.post("/api/chat",json={"message":"How can I check scholarship eligibility?"})
    assert r.status_code==200
    assert "sources" in r.json
    assert "session_id" in r.json

def test_invalid_session():
    c=create_app().test_client()
    assert c.post("/api/chat",json={"message":"hello","session_id":"bad"}).status_code==400
