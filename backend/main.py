import asyncio
import json
import os
import websockets
from google import genai
import base64

# 環境変数からAPIキーを設定する
os.environ['GOOGLE_API_KEY'] = ''  # 実際に使用するAPIキーをここに設定します
MODEL = "gemini-2.0-flash-exp"  # 使用するモデルID

# Google Gemini API クライアントを初期化
client = genai.Client(
  http_options={
    'api_version': 'v1alpha',  # 使用するAPIのバージョン
  }
)

# WebSocketサーバーの処理
async def gemini_session_handler(client_websocket: websockets.WebSocketServerProtocol):
    """Handles the interaction with Gemini API within a websocket session."""
    try:
        # クライアントから設定メッセージを受け取る
        config_message = await client_websocket.recv()
        config_data = json.loads(config_message)
        config = config_data.get("setup", {})
        
        # システムインストラクションを設定
        config["system_instruction"] = "You are a daily life assistant."
        
        # Gemini APIとの接続を開始
        async with client.aio.live.connect(model=MODEL, config=config) as session:
            print("Connected to Gemini API")

            # クライアントから受け取ったメッセージをGemini APIに送信
            async def send_to_gemini():
                """Sends messages from the client websocket to the Gemini API."""
                try:
                  async for message in client_websocket:
                      try:
                          data = json.loads(message)
                          if "realtime_input" in data:
                              # リアルタイムの入力データを処理
                              for chunk in data["realtime_input"]["media_chunks"]:
                                  # 音声データの場合
                                  if chunk["mime_type"] == "audio/pcm":
                                      # ここでは音声チャンクをGemini APIに送信
                                      await session.send(input={"mime_type": "audio/pcm", "data": chunk["data"]})
                                      
                                  # 画像データの場合
                                  elif chunk["mime_type"] == "image/jpeg":
                                      print(f"Sending image chunk: {chunk['data'][:50]}")
                                      await session.send(input={"mime_type": "image/jpeg", "data": chunk["data"]})
                                      
                      except Exception as e:
                          print(f"Error sending to Gemini: {e}")
                  print("Client connection closed (send)")
                except Exception as e:
                     print(f"Error sending to Gemini: {e}")
                finally:
                   print("send_to_gemini closed")


            # Gemini API からのレスポンスをクライアントに送信
            async def receive_from_gemini():
                """Receives responses from the Gemini API and forwards them to the client, looping until turn is complete."""
                try:
                    while True:
                        try:
                            print("receiving from gemini")
                            async for response in session.receive():
                                # サーバーからのコンテンツが空の場合、メッセージを無視
                                if response.server_content is None:
                                    print(f'Unhandled server message! - {response}')
                                    continue

                                model_turn = response.server_content.model_turn
                                if model_turn:
                                    # モデルのターンが存在する場合、出力を処理
                                    for part in model_turn.parts:
                                        if hasattr(part, 'text') and part.text is not None:
                                            # テキスト出力があればクライアントに送信
                                            await client_websocket.send(json.dumps({"text": part.text}))
                                        elif hasattr(part, 'inline_data') and part.inline_data is not None:
                                            # 音声出力があればBase64エンコードしてクライアントに送信
                                            print("audio mime_type:", part.inline_data.mime_type)
                                            base64_audio = base64.b64encode(part.inline_data.data).decode('utf-8')
                                            
                                            await client_websocket.send(json.dumps({"audio": base64_audio}))
                                            
                                            print("audio received")

                                # ターンが完了したら終了
                                if response.server_content.turn_complete:
                                    print('\n<Turn complete>')
                                    
                        except websockets.exceptions.ConnectionClosedOK:
                            # クライアントの接続が正常に閉じられた場合
                            print("Client connection closed normally (receive)")
                            break  # コネクションが閉じられたらループを終了
                        except Exception as e:
                            print(f"Error receiving from Gemini: {e}")
                            break  # エラーが発生した場合ループを終了

                except Exception as e:
                      print(f"Error receiving from Gemini: {e}")
                finally:
                      print("Gemini connection closed (receive)")


            # メッセージ送信ループを非同期タスクとして開始
            send_task = asyncio.create_task(send_to_gemini())
            # 受信ループをバックグラウンドタスクとして開始
            receive_task = asyncio.create_task(receive_from_gemini())
            # 両方のタスクを同時に実行
            await asyncio.gather(send_task, receive_task)


    except Exception as e:
        print(f"Error in Gemini session: {e}")
    finally:
        print("Gemini session closed.")


async def main() -> None:
    """Starts the WebSocket server and listens for incoming client connections."""
    async with websockets.serve(gemini_session_handler, "0.0.0.0", 9084):
        print("Running websocket server 0.0.0.0:9084...")
        await asyncio.Future()  # サーバーが常に動作し続けるように待機


if __name__ == "__main__":
    asyncio.run(main())
