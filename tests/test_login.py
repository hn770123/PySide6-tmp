import sys
import os
from PySide6.QtWidgets import QApplication, QLineEdit

# srcディレクトリをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from login_window import LoginWindow

def test_password_visibility():
    """
    パスワード表示切替機能のテスト
    """
    # QApplicationのインスタンスが必要
    app = QApplication(sys.argv)

    window = LoginWindow()

    # 初期状態の確認 (Passwordモードであるべき)
    if window.password_input.echoMode() != QLineEdit.EchoMode.Password:
        print("FAIL: Initial echo mode is not Password")
        sys.exit(1)

    # チェックボックスをONにする
    window.show_password_cb.setChecked(True)

    # 表示モードが変わったか確認 (Normalモードであるべき)
    if window.password_input.echoMode() != QLineEdit.EchoMode.Normal:
        print("FAIL: Echo mode did not change to Normal when checked")
        sys.exit(1)

    # チェックボックスをOFFにする
    window.show_password_cb.setChecked(False)

    # 表示モードが戻ったか確認 (Passwordモードであるべき)
    if window.password_input.echoMode() != QLineEdit.EchoMode.Password:
        print("FAIL: Echo mode did not revert to Password when unchecked")
        sys.exit(1)

    print("PASS: Password visibility toggle works correctly")
    window.close()

def test_login_success():
    """
    ログイン成功時のシグナル発火テスト
    """
    import database
    import auth

    # テスト用DBの設定
    test_db = "test_login.db"
    # databaseモジュールのDB_NAMEを書き換え
    original_db_name = database.DB_NAME
    database.DB_NAME = test_db

    # 既存のDBがあれば削除
    if os.path.exists(test_db):
        os.remove(test_db)

    database.init_db()

    # テストユーザー追加
    username = "gui_test_user"
    password = "password123"
    hashed = auth.hash_password(password)
    database.add_user(username, hashed)

    # QApplicationインスタンス取得
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    window = LoginWindow()

    # 入力設定
    window.username_input.setText(username)
    window.password_input.setText(password)

    # シグナル受信確認用
    signal_received = []
    window.login_successful.connect(lambda: signal_received.append(True))

    # ログイン処理実行
    window._handle_login()

    # 後始末
    window.close()
    if os.path.exists(test_db):
        os.remove(test_db)
    database.DB_NAME = original_db_name # Restore

    if not signal_received:
        print("FAIL: Login successful signal was not emitted")
        sys.exit(1)

    print("PASS: Login logic works correctly (Signal emitted)")

if __name__ == "__main__":
    test_password_visibility()
    test_login_success()
    sys.exit(0)
