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
    """WebSocketセッション内でGemini APIとの対話を処理する."""
    try:
        # geminiのレスポンス設定
        config_message = await client_websocket.recv()
        config_data = json.loads(config_message)
        config = config_data.get("setup", {})
        
        # 追加でプロンプトを設定
        config["system_instruction"] = "日本語で答えてください"
        
        # Gemini APIとの接続を開始
        async with client.aio.live.connect(model=MODEL, config=config) as session:
            print("Gemini APIに接続")

            # クライアントから受け取ったメッセージをGemini APIに送信
            async def send_to_gemini():
                """クライアントWebSocketからGemini APIにメッセージを送信します."""
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
                                      print(f"画像チャンクを送信します: {chunk['data'][:50]}")
                                      await session.send(input={"mime_type": "image/jpeg", "data": chunk["data"]})
                                      
                      except Exception as e:
                          print(f"ジェミニへのエラーの送信: {e}")
                  print("クライアント接続が閉じました (send)")
                except Exception as e:
                     print(f"ジェミニへのエラーの送信: {e}")
                finally:
                   print("send_to_gemini閉じた")


            # Gemini API からのレスポンスをクライアントに送信
            async def receive_from_gemini():
                """Gemini APIから回答を受け取り、クライアントに転送し、ターンが完了するまでループする."""
                try:
                    while True:
                        try:
                            print("ジェミニから受信")
                            async for response in session.receive():
                                # サーバーからのコンテンツが空の場合、メッセージを無視
                                if response.server_content is None:
                                    print(f'未処理のサーバーメッセージ! - {response}')
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
                            print("クライアント接続は正常に閉じられました (receive)")
                            break  # コネクションが閉じられたらループを終了
                        except Exception as e:
                            print(f"ジェミニからのエラーの受信エラー: {e}")
                            break  # エラーが発生した場合ループを終了

                except Exception as e:
                      print(f"ジェミニからのエラーの受信エラー: {e}")
                finally:
                      print("Gemini接続は閉じました (receive)")


            # メッセージ送信ループを非同期タスクとして開始
            send_task = asyncio.create_task(send_to_gemini())
            # 受信ループをバックグラウンドタスクとして開始
            receive_task = asyncio.create_task(receive_from_gemini())
            # 両方のタスクを同時に実行
            await asyncio.gather(send_task, receive_task)


    except Exception as e:
        print(f"ジェミニセッションのエラー: {e}")
    finally:
        print("ジェミニセッションは終了しました.")


# gemini_session_handler を起動
async def main() -> None:
    """WebSocketサーバーを起動し、着信クライアント接続のためにリッスンします."""
    async with websockets.serve(gemini_session_handler, "0.0.0.0", 9084):
        print("WebSocketServer 0.0.0.0:9084の実行中...")
        await asyncio.Future()  # サーバーが常に動作し続けるように待機


if __name__ == "__main__":
    asyncio.run(main())
