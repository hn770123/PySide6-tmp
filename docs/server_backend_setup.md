# PySide6 アプリケーションのバックエンドサーバー化手順

このドキュメントでは、現在ローカル（SQLite）で動作しているPySide6アプリケーションのバックエンド部分を、サーバー上で動作させるための手順とアーキテクチャ設計について解説します。

## 1. 概要とアーキテクチャ

デスクトップアプリケーションの「バックエンドをサーバーで動かす」場合、主に以下の2つのアプローチがあります。

1.  **APIサーバー方式（推奨）**:
    *   ビジネスロジックとデータベースアクセスをWeb API（REST/GraphQL）としてサーバーに配置します。
    *   クライアント（PySide6）はHTTPリクエストを通じてデータを取得・操作します。
    *   **メリット**: セキュリティが高い、DB接続情報をクライアントに持たせなくて良い、Web版やスマホ版への展開が容易。
    *   **デメリット**: 開発工数が増える（API開発が必要）。

2.  **直接DB接続方式（非推奨）**:
    *   データベース（PostgreSQL/MySQLなど）のみをサーバーに置き、クライアントから直接SQLを発行します。
    *   **メリット**: 変更が少ない。
    *   **デメリット**: DBの接続情報がクライアントに含まれるためセキュリティリスクが高い、ネットワーク遅延の影響を受けやすい、スキーマ変更時に全クライアントの更新が必要。

本ドキュメントでは、拡張性とセキュリティの観点から**「APIサーバー方式」**への移行手順を解説します。

---

## 2. 推奨構成

*   **サーバー側 (Backend)**: Python (FastAPI), Uvicorn, PostgreSQL/MySQL
*   **クライアント側 (Frontend)**: PySide6, Requests (HTTPクライアント)

---

## 3. 移行手順

### ステップ1: サーバーサイドAPIの構築

まず、データベース操作と認証ロジックを担当するAPIサーバーを作成します。

1.  **プロジェクト構成の作成**:
    `src/` とは別に `backend/` ディレクトリを作成し、FastAPIプロジェクトをセットアップします。

    ```bash
    mkdir backend
    cd backend
    pip install fastapi uvicorn sqlalchemy psycopg2-binary
    ```

2.  **APIの実装例**:
    現在の `src/auth.py` や `src/database.py` のロジックをFastAPIのエンドポイントに移植します。

    **例: backend/main.py**
    ```python
    from fastapi import FastAPI, HTTPException, Depends
    from pydantic import BaseModel
    # 既存のロジック（DB接続など）をインポートまたは移植

    app = FastAPI()

    class LoginRequest(BaseModel):
        username: str
        password: str

    @app.post("/login")
    def login(req: LoginRequest):
        # 既存の auth.authenticate ロジックをここで実行
        # DBはSQLiteではなくPostgreSQL等を使用するように変更
        is_valid = check_password(req.username, req.password)
        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {"token": "dummy_token_or_jwt", "message": "Login successful"}
    ```

### ステップ2: データベースの移行

ローカルのSQLite (`app.db`) から、サーバー用データベース（PostgreSQLなど）へ移行します。

1.  **DBサーバーの構築**:
    Docker等を使用してPostgreSQLを立ち上げます。
2.  **テーブル作成**:
    `src/database.py` の `init_db` 内のCREATE文を元に、PostgreSQL上でテーブルを作成します。
3.  **接続設定**:
    サーバー側のコード（SQLAlchemyなど）で、接続文字列をSQLiteからPostgreSQLに変更します。

### ステップ3: クライアント（PySide6）の改修

クライアント側のコードを変更し、直接DBを触るのではなく、APIを呼び出すようにします。

1.  **ライブラリの追加**:
    `requests` ライブラリを導入します。
    ```bash
    pip install requests
    ```

2.  **`src/database.py` / `src/auth.py` の書き換え**:
    直接SQLを実行していた部分を、APIリクエストに置き換えます。

    **例: src/auth.py の改修イメージ**
    ```python
    import requests

    API_BASE_URL = "http://your-server-address:8000"

    def authenticate(username, password):
        """
        サーバーAPIを叩いて認証を行う
        """
        try:
            response = requests.post(
                f"{API_BASE_URL}/login",
                json={"username": username, "password": password},
                timeout=5
            )
            if response.status_code == 200:
                return True
            return False
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            return False
    ```

### ステップ4: デプロイ

1.  **サーバーの起動**:
    サーバー上でUvicornを使用してAPIを起動します。
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```
    ※本番環境では Gunicorn + Uvicorn Worker や Docker コンテナ化、Nginx（リバースプロキシ）の利用を推奨します。

2.  **クライアントの配布**:
    APIのURLを設定ファイル（config.iniや環境変数）に外出しし、接続先を切り替えられるようにして配布します。
    配布方法は既存の「フォルダ配布（Embeddable Python）」のままで問題ありません。

---

## 4. 注意点

*   **エラーハンドリング**: ネットワークエラー（接続不可、タイムアウト）が発生する可能性があるため、PySide6側で適切に `try-except` し、ユーザーに通知する仕組みが必要です。
*   **セキュリティ**: 通信経路は必ずSSL/TLS (HTTPS) で暗号化してください。
*   **非同期処理**: APIリクエストは時間がかかる場合があるため、UIスレッド（メインスレッド）で実行すると画面がフリーズします。`QThread` や `QRunnable` を使用して、別スレッドで実行することを強く推奨します。

---

## 5. 参考資料

*   **FastAPI Documentation**: https://fastapi.tiangolo.com/ja/
*   **SQLAlchemy**: https://www.sqlalchemy.org/
*   **PySide6 Threading**: https://doc.qt.io/qtforpython/overviews/thread.html
