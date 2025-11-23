# run.py  (place this in the main folder, next to app/)
import uvicorn

if __name__ == "__main__":
    uvicorn.run("skillsmatch.app.main:app", host="127.0.0.1", port=8000, reload=True)