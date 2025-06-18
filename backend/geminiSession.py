from fastapi import FastAPI
import socketio
import uvicorn
from google import genai
import base64
import asyncio
from dotenv import load_dotenv
import os
import sounddevice as sd
import numpy as np


sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*", max_http_buffer_size=100* 1024 * 1024)
app = FastAPI()
socket_app = socketio.ASGIApp(sio, app)

load_dotenv()

# GenAI API 初期化
client = genai.Client(api_key=os.getenv("API_KEY"), http_options={'api_version': 'v1alpha'})
model_id = "gemini-2.0-flash-live-001"
config = {"response_modalities": ["TEXT"]}

def play_pcm(pcm_data, samplerate=16000):
    try:
        # PCMデータをnumpy配列に変換（int16型でリトルエンディアンを想定）
        audio_array = np.frombuffer(pcm_data, dtype=np.int16)

        sd.play(pcm_data, samplerate=samplerate)

        # 再生完了まで待機
        sd.wait()
    except Exception as e:
        print(f"音声再生エラー: {e}")

# 「どのクライアント（＝Socket.IOのsid）が、どのGeminiセッションを持っているか」を管理
session_map = {}
# 「どのクライアントが、Geminiからの応答を受け取る非同期タスク（asyncio.Task）」を持っているか」を管理
receive_tasks = {}
task_map = {}

async def handle_session(sid):
    try:
        async with client.aio.live.connect(model=model_id, config=config) as session:
            session_map[sid] = session
            receive_tasks[sid] = asyncio.create_task(receive_from_gemini(session, sid))

            # セッションが続く限り待機させる（例：終了をイベントなどで検知するまで）
            await receive_tasks[sid]

    except asyncio.CancelledError:
        print(f"[handle_session] セッション {sid} はキャンセルされました")

    finally:
        session_map.pop(sid, None)
        receive_tasks.pop(sid, None)
        print(f"[handle_session] セッション {sid} が終了しました")

async def receive_from_gemini(session, sid):
    while True:
        async for response in session.receive():
            if data := response.data:
                # await sio.emit("gemini_audio", data, to=sid)
                await play_pcm(data)
                continue
            if text := response.text:
                print(text, end="")

@sio.event
async def connect(sid, environ):
    print(f"✅ クライアント {sid} が接続しました")
          
@sio.event
async def start_session(sid, data):
     task_map[sid] = asyncio.create_task(handle_session(sid))
     await sio.emit("session_started", {}, to=sid)

@sio.event
async def send_audio_chunk(sid, data):
    session = session_map.get(sid)
    if not session:
        return

    chunk = base64.b64decode(data["data"])
    await session.send(input={"mime_type": "audio/pcm", "data": chunk})
    print(f"[send_audio_chunk] {sid} 音声チャンク送信完了")
        
@sio.event
async def send_image_frame(sid, data):
    session = session_map.get(sid)
    if not session:
        return

    image = data["data"]
    await session.send(input={"mime_type": "image/jpeg", "data": image})
    print(f"[send_image_frame] {sid} 画像フレーム送信完了")

# @sio.event
# async def end_session(sid):
#     print(f"[end_session] {sid}")
#     session = session_map.pop(sid, None)
#     if session:
#         await session.close()
#     task = receive_tasks.pop(sid, None)
#     if task:
#         task.cancel()
#     await sio.emit("session_ended", {}, to=sid)

@sio.event
async def disconnect(sid):
    print(f"❌ クライアント {sid} が切断しました")
    session = session_map.pop(sid, None)
    if session:
        await session.close()
    task = task_map.pop(sid, None)
    if task:
        task.cancel()


# サーバー起動
if __name__ == "__main__":
    uvicorn.run(socket_app, host="0.0.0.0", port=8080)
    
    # uvicorn geminiSession:socket_app --host 0.0.0.0 --port 8080 --reload