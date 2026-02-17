"""
メインモジュール
==============

PySide6を使用したシンプルなHello Worldアプリケーションのエントリーポイントです。
"""

import sys
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout


def main():
    """
    アプリケーションのメイン関数です。
    ウィンドウを作成し、"Hello World" ラベルを表示します。
    """
    # アプリケーションのインスタンスを作成
    app = QApplication(sys.argv)

    # メインウィンドウを作成
    window = QWidget()
    window.setWindowTitle("Hello World App")
    window.resize(400, 300)

    # レイアウトを作成
    layout = QVBoxLayout()

    # ラベルを作成してレイアウトに追加
    label = QLabel("Hello World")
    layout.addWidget(label)

    # ウィンドウにレイアウトを設定
    window.setLayout(layout)

    # ウィンドウを表示
    window.show()

    # イベントループを開始
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
