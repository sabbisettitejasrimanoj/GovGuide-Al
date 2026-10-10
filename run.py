from app import create_app
from app.rag import rebuild

app=create_app()
if __name__=="__main__":
    print(f"Indexed {rebuild()} knowledge chunks")
    app.run(host="127.0.0.1",port=5000,debug=False)
