from fastapi import FastAPI
import socketio
import uvicorn
from google import genai
import base64
import asyncio
from dotenv import load_dotenv
import os


sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*", max_http_buffer_size=100* 1024 * 1024)
app = FastAPI()
socket_app = socketio.ASGIApp(sio, app)

load_dotenv()

# GenAI API 初期化
client = genai.Client(api_key=os.getenv("API_KEY"), http_options={'api_version': 'v1alpha'})
model_id = "gemini-2.0-flash-live-001"
config = {"response_modalities": ["TEXT"]}

session_map = {}
receive_tasks = {}

@sio.event
async def connect(sid, environ):
    print(f"✅ クライアント {sid} が接続しました")
          
@sio.event
async def start_session(sid, data):
    print(f"[start_session] {sid}")
    # 必要に応じてconfigをdataから渡す
    session = await client.aio.live.connect(model=model_id, config=config)
    session_map[sid] = session

    # Gemini応答をリアルタイムでクライアントに流す
    async def receive_from_gemini():
        try:
            async for response in session.receive():
                if response.text:
                    await sio.emit("gemini_text", response.text, to=sid)
        except Exception as e:
            print(f"[Gemini受信エラー] {e}")

    # タスクとして受信を開始
    task = asyncio.create_task(receive_from_gemini())
    receive_tasks[sid] = task

    await sio.emit("session_started", {}, to=sid)

@sio.event
async def send_chunk(sid, data):
    session = session_map.get(sid)
    if not session:
        await sio.emit("error", {"message": "No live session"}, to=sid)
        return
    try:
        mime_type = data.get("mime_type")
        chunk_data = base64.b64decode(data["data"])
        await session.send(input={"mime_type": mime_type, "data": chunk_data})
    except Exception as e:
        print(f"[チャンク送信エラー] {e}")
        await sio.emit("error", {"message": str(e)}, to=sid)

@sio.event
async def end_session(sid):
    print(f"[end_session] {sid}")
    session = session_map.pop(sid, None)
    if session:
        await session.close()
    task = receive_tasks.pop(sid, None)
    if task:
        task.cancel()
    await sio.emit("session_ended", {}, to=sid)

@sio.event
async def disconnect(sid):
    print(f"❌ クライアント {sid} が切断しました")
    # セッションも強制終了
    await end_session(sid)

# サーバー起動
if __name__ == "__main__":
    uvicorn.run(socket_app, host="0.0.0.0", port=8080)
    
    # uvicorn geminiSession:socket_app --host 0.0.0.0 --port 8080 --reload