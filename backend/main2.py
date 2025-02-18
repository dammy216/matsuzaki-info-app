import json
import os
import asyncio
import base64
from fastapi import FastAPI
from fastapi_socketio import SocketManager
from google import genai

# FastAPI アプリの作成
app = FastAPI()
socket = SocketManager(app)

# Google Gemini API クライアントを初期化
client = genai.Client(api_key="", http_options={'api_version': 'v1alpha'})
MODEL = "gemini-2.0-flash-exp"

@socket.on("connect")
async def connect(sid, environ):
    """ クライアントが接続した際に呼ばれる """
    print(f"以下のクライアントが接続しました: {sid}")

@socket.on("disconnect")
async def disconnect(sid):
    """ クライアントが切断された際に呼ばれる """
    print(f"以下のクライアントの接続が切れました: {sid}")

@socket.on("setup")
async def setup(sid, data):
    """ クライアントからのセットアップメッセージを処理し、Gemini API のセッションを開始する """
    config = data.get("setup", {})
    config["system_instruction"] = "You are a daily life assistant."
    session = await client.aio.live.connect(model=MODEL, config=config)
    app.state.sessions[sid] = session
    print(f"Gemini APIセッション開始: {sid}")

@socket.on("realtime_input")
async def send_to_gemini(sid, data):
    """ クライアントからのリアルタイムデータを Gemini API に送信する """
    session = app.state.sessions.get(sid)
    if not session:
        print(f"セッションなし: {sid}")
        return
    
    for chunk in data.get("media_chunks", []):
        mime_type = chunk.get("mime_type")
        chunk_data = chunk.get("data")
        
        if not mime_type or not chunk_data:
            continue
        
        if mime_type == "audio/pcm":
            await session.send(input={"mime_type": "audio/pcm", "data": chunk_data})
        
        elif mime_type == "image/jpeg":
            print(f"画像チャンクを送信します: {chunk_data[:50]}")
            await session.send(input={"mime_type": "image/jpeg", "data": chunk_data})


@socket.on("get_response")
async def receive_from_gemini(sid):
    """ Gemini API からのレスポンスを受信し、クライアントに送信する """
    session = app.state.sessions.get(sid)
    if not session:
        print(f"セッションなし: {sid}")
        return
    
    async for response in session.receive():
        if response.server_content:
            model_turn = response.server_content.model_turn
            if model_turn:
                for part in model_turn.parts:
                    if hasattr(part, 'text') and part.text:
                        # 受信したテキストをクライアントに送信
                        await socket.emit("response", {"text": part.text}, room=sid)
                    elif hasattr(part, 'inline_data') and part.inline_data:
                        # 受信した音声データを Base64 に変換してクライアントに送信
                        base64_audio = base64.b64encode(part.inline_data.data).decode('utf-8')
                        await socket.emit("response", {"audio": base64_audio}, room=sid)
    
        if response.server_content.turn_complete:
            print(f"Turn complete: {sid}")

if __name__ == "__main__":
    import uvicorn
    app.state.sessions = {}  # クライアントごとのセッションを管理する辞書
    uvicorn.run(app, host="0.0.0.0", port=9084)