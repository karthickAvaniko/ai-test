import json
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import uvicorn

app = FastAPI()

@app.post("/v1/chat")
async def mock_chat(request: Request):
    data = await request.json()
    message = data.get("message", "Hello")
    stream = data.get("stream", False)
    
    if not stream:
        return {
            "response": "This is a mock response from the fake RunPod server.",
            "tokens_used": 15
        }
        
    async def generate():
        response_text = f"Hello! This is a simulated streaming response from the Avaniko Mock Server. You said: '{message}'. The UI looks great! ✨"
        words = response_text.split(" ")
        for i, word in enumerate(words):
            chunk = {
                "token": word + (" " if i < len(words) - 1 else "")
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.05) # simulate network delay
        yield "data: [DONE]\n\n"
        
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=2222)
