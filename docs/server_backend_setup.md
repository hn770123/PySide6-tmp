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
*   **クライアント側 (Frontend)**: PySide6 (QtNetworkモジュール)

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
PySide6では、標準のPythonライブラリ（`requests`など）ではなく、Qtフレームワークに統合された **`QtNetwork`** モジュールを使用することを推奨します。

1.  **ライブラリの追加**:
    PySide6標準の機能を使用するため、追加のライブラリインストールは不要です。

2.  **`src/auth.py` などの書き換え**:
    QtNetworkは **非同期** で動作するため、関数の戻り値で結果を返すのではなく、**Signal（シグナル）** を使用して結果を通知する設計に変更する必要があります。

    **例: src/auth_manager.py の実装イメージ**
    ```python
    import json
    from PySide6.QtCore import QObject, Signal, Slot, QUrl
    from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

    API_BASE_URL = "http://your-server-address:8000"

    class AuthManager(QObject):
        # 認証結果を通知するシグナル (成功可否, メッセージ)
        login_finished = Signal(bool, str)

        def __init__(self):
            super().__init__()
            self.manager = QNetworkAccessManager(self)
            # レスポンス受信時のシグナル接続
            self.manager.finished.connect(self.handle_response)

        def login(self, username, password):
            url = QUrl(f"{API_BASE_URL}/login")
            request = QNetworkRequest(url)
            request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")

            data = json.dumps({"username": username, "password": password}).encode('utf-8')
            # 非同期でPOSTリクエスト送信
            self.manager.post(request, data)

        @Slot(QNetworkReply)
        def handle_response(self, reply):
            if reply.error() == QNetworkReply.NetworkError.NoError:
                # 成功時の処理
                self.login_finished.emit(True, "Login successful")
            else:
                # エラー時の処理
                self.login_finished.emit(False, reply.errorString())

            reply.deleteLater()
    ```

    **呼び出し側の変更イメージ (Windowクラス内)**:
    ```python
    def on_login_button_clicked(self):
        username = self.ui.username_input.text()
        password = self.ui.password_input.text()

        # 認証マネージャーのインスタンス化（または依存注入）
        self.auth_manager = AuthManager()
        self.auth_manager.login_finished.connect(self.on_login_finished)

        # ローディング表示などを開始
        self.ui.status_label.setText("ログイン中...")

        # 非同期ログイン実行
        self.auth_manager.login(username, password)

    @Slot(bool, str)
    def on_login_finished(self, success, message):
        if success:
            self.ui.status_label.setText("成功！")
            # 画面遷移処理
        else:
            self.ui.status_label.setText(f"失敗: {message}")
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

*   **非同期処理とUI**: `QtNetwork` は非同期で動作するため、リクエスト送信時にUIをフリーズさせません。`requests` などのブロッキングライブラリを使用する場合に必要となる `QThread` などのスレッド管理が不要になります。ただし、レスポンスが返ってくるまでの間、ユーザーが重複操作を行わないよう、ボタンを無効化するなどのUI制御が必要です。
*   **SSL/TLS**: 通信経路は必ずSSL/TLS (HTTPS) で暗号化してください。QtNetworkはOpenSSLをサポートしています。
*   **エラーハンドリング**: サーバーダウンやネットワーク切断などのエラーは `QNetworkReply.error()` で検知し、適切にユーザーに通知してください。

---

## 5. 参考資料

*   **FastAPI Documentation**: https://fastapi.tiangolo.com/ja/
*   **PySide6 QtNetwork**: https://doc.qt.io/qtforpython/PySide6/QtNetwork/index.html
*   **QNetworkAccessManager**: https://doc.qt.io/qtforpython/PySide6/QtNetwork/QNetworkAccessManager.html
