from fastapi import FastAPI
import socketio
import uvicorn
from google import genai
import base64
import sounddevice as sd
import numpy as np
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

# SocketIO 初期化
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*", max_http_buffer_size=100* 1024 * 1024)
app = FastAPI()
socket_app = socketio.ASGIApp(sio, app)

# GenAI API 初期化
client = genai.Client(api_key="os.getenv('API_KEY')", http_options={'api_version': 'v1alpha'})
model_id = "gemini-2.0-flash-exp"
config = {"response_modalities": ["TEXT"]}

def play_pcm(pcm_data, samplerate=16000, channels=1):
    try:
        # PCMデータをnumpy配列に変換（int16型でリトルエンディアンを想定）
        audio_array = np.frombuffer(pcm_data, dtype=np.int16)

        # モノラル（1チャンネル）の場合はそのまま再生
        if channels == 1:
            sd.play(audio_array, samplerate=samplerate)

        # ステレオ（2チャンネル）の場合はデータをリシェイプ
        elif channels == 2:
            audio_array = audio_array.reshape(-1, 2)
            sd.play(audio_array, samplerate=samplerate)

        # 再生完了まで待機
        sd.wait()
    except Exception as e:
        print(f"音声再生エラー: {e}")
        
@sio.event
async def connect(sid, environ):
    print(f"✅ クライアント {sid} が接続しました")

@sio.event
async def chat_test(sid, data):
    try:
        async with client.aio.live.connect(model=model_id, config=config) as session:
            
            async def send_to_gemini():
                try:
                    for message in data["realtime_input"][0]:
                        if message["mime_type"] == "audio/pcm":
                            decoded_sound_data = base64.b64decode(message["data"])
                            # **2. 音声データを Gemini に送信**
                            await session.send(input={"mime_type": "audio/pcm", "data": decoded_sound_data})
                            print(f"音声チャンクを送信します: {decoded_sound_data[:50]}")
                            # PCMデータを再生
                            play_pcm(decoded_sound_data)
                            
                        if message["mime_type"] == "image/jpeg":
                            decoded_image_data = base64.b64decode(message["data"])
                            # **3. 画像データを Gemini に送信**
                            await session.send(input={"mime_type": "image/jpeg", "data": decoded_image_data})
                            print(f"画像チャンクを送信します: {decoded_image_data[:50]}")
                except Exception as e:
                    print(f"gemini送信エラー: {e}")            
             
             
            async def receive_from_gemini():  
                try:     
                    async for response in session.receive():
                            if response.text is None:
                                continue
                            print(response.text, end="")
                except Exception as e:
                    print(f"gemini受信エラー: {e}")
                finally:
                    await session.close()
            # if response.server_content:
            #         model_turn = response.server_content.model_turn
            #         if model_turn:
            #             for part in model_turn.parts:
            #                 if hasattr(part, 'text') and part.text:
            #                     print(f"テキストメッセージ: {part.text}")  # テキストメッセージを出力(part.text)
            
            
            # メッセージ送信ループを非同期タスクとして開始
            send_task = asyncio.create_task(send_to_gemini())
            # 受信ループをバックグラウンドタスクとして開始
            receive_task = asyncio.create_task(receive_from_gemini())
            # 両方のタスクを同時に実行
            await asyncio.gather(send_task, receive_task)
        
    except Exception as e:
        print(f"エラー: {e}")
    finally:
        print("セッションは終了しました")

@sio.event
async def disconnect(sid):
    print(f"❌ クライアント {sid} が切断しました")
    

# サーバー起動
if __name__ == "__main__":
    uvicorn.run(socket_app, host="0.0.0.0", port=8080)

# uvicorn main2:socket_app --host 0.0.0.0 --port 8080 --reload