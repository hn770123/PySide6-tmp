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
    sys.exit(0)

if __name__ == "__main__":
    test_password_visibility()
