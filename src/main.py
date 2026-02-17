"""
メインモジュール
==============

PySide6を使用したアプリケーションのエントリーポイントです。
ログイン画面を表示し、認証成功後にメインウィンドウを表示します。
"""

import sys
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
try:
    from login_window import LoginWindow
except ImportError:
    # src/main.pyとして直接実行される場合と、パッケージとして実行される場合の両方に対応
    from src.login_window import LoginWindow


class MainWindow(QWidget):
    """
    アプリケーションのメインウィンドウクラスです。
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hello World App")
        self.resize(400, 300)
        self._setup_ui()

    def _setup_ui(self):
        """
        UIコンポーネントを初期化します。
        """
        layout = QVBoxLayout()
        label = QLabel("Hello World")
        layout.addWidget(label)
        self.setLayout(layout)


def main():
    """
    アプリケーションのメイン関数です。
    ログインウィンドウを表示し、ログイン成功時にメインウィンドウに切り替えます。
    """
    app = QApplication(sys.argv)

    # ログインウィンドウとメインウィンドウのインスタンス作成
    login_window = LoginWindow()
    main_window = MainWindow()

    def show_main_window():
        """
        ログイン成功時に呼び出され、メインウィンドウを表示します。
        """
        login_window.close()
        main_window.show()

    # ログイン成功シグナルを接続
    login_window.login_successful.connect(show_main_window)

    # ログインウィンドウを表示
    login_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
