from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# FastAPIインスタンスの作成
app = FastAPI()

# CORSミドルウェアの設定
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],  # 任意のオリジンを許可（開発中は * でも可）
  allow_credentials=True,
  allow_methods=["*"],  # 任意のHTTPメソッドを許可
  allow_headers=["*"],  # 任意のヘッダーを許可
)