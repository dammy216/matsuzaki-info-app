from fastapi import FastAPI
import socketio
import uvicorn
from google import genai
import sounddevice as sd
import numpy as np
import base64

# SocketIO 初期化
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = FastAPI()
socket_app = socketio.ASGIApp(sio, app)

# GenAI API 初期化
client = genai.Client(api_key="", http_options={'api_version': 'v1alpha'})
model_id = "gemini-2.0-flash-exp"
config = {"responseModalities": ["AUDIO"]}

@sio.event
async def connect(sid, environ):
    print(f"✅ クライアント {sid} が接続しました")

@sio.event
async def chatTest(sid, data):
    audio_buffer = b""  # 音声データを貯めるバッファ

    async with client.aio.live.connect(model=model_id, config=config) as session:
        
        message = data["realtime_input"][0]
            
        if message["mime_type"] == "audio/pcm":
            decoded_data = base64.b64decode(message["data"])
             # **2. 音声データを Gemini に送信**
            await session.send(input={"mime_type": "audio/pcm", "data": decoded_data})
            print(f"音声チャンクを送信します: {decoded_data[:50]}")
        # elif message["mime_type"] == "image/jpeg":
        #      # **3. 画像データを Gemini に送信**
        #     await session.send(input={"mime_type": "image/jpeg", "data": decoded_data})

        # 一文字生成するごとにレスポンスを返してる
        async for response in session.receive():
            print(f"レスポンス: {response}")
            if response.server_content:
                    model_turn = response.server_content.model_turn
                    if model_turn:
                        for part in model_turn.parts:
                            if hasattr(part, 'text') and part.text:
                                print(part.text)
                            elif hasattr(part, 'inline_data') and part.inline_data:
                                audio_buffer += part.inline_data.data  # バッファにデータを追加

        if audio_buffer:
            audio_array = np.frombuffer(audio_buffer, dtype=np.int16)  # バッファからnumpy配列に変換
            sd.play(audio_array, samplerate=24000)  # 一気に再生
            sd.wait()

@sio.event
async def disconnect(sid):
    print(f"❌ クライアント {sid} が切断しました")

# サーバー起動
if __name__ == "__main__":
    uvicorn.run(socket_app, host="0.0.0.0", port=8080)

# uvicorn main2:socket_app --host 0.0.0.0 --port 8080 --reload