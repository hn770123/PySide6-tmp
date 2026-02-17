"""
ログインウィンドウモジュール
==========================

このモジュールは、ユーザーログイン用のウィンドウを提供します。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QCheckBox, QLabel, QMessageBox
)
from PySide6.QtCore import Signal, Qt

try:
    from auth import authenticate
except ImportError:
    from src.auth import authenticate

class LoginWindow(QWidget):
    """
    ログイン画面を表示するクラスです。
    ユーザー名とパスワードの入力、およびパスワード表示の切り替え機能を提供します。
    """
    # ログイン成功時に発火するシグナル
    login_successful = Signal()

    def __init__(self):
        """
        LoginWindowの初期化を行います。
        """
        super().__init__()
        self.setWindowTitle("ログイン")
        self.resize(300, 200)

        self.username_input = None
        self.password_input = None
        self.show_password_cb = None
        self.login_button = None

        self._setup_ui()

    def _setup_ui(self):
        """
        UIコンポーネントを初期化し、レイアウトを設定します。
        """
        layout = QVBoxLayout()

        # ユーザー名入力
        username_label = QLabel("ユーザー名:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("ユーザー名")
        layout.addWidget(username_label)
        layout.addWidget(self.username_input)

        # パスワード入力
        password_label = QLabel("パスワード:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("パスワード")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(password_label)
        layout.addWidget(self.password_input)

        # パスワード表示チェックボックス
        self.show_password_cb = QCheckBox("パスワードを表示")
        # stateChangedシグナルを利用してパスワードの表示/非表示を切り替える
        self.show_password_cb.stateChanged.connect(self._toggle_password_visibility)
        layout.addWidget(self.show_password_cb)

        # ログインボタン
        self.login_button = QPushButton("ログイン")
        self.login_button.clicked.connect(self._handle_login)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def _toggle_password_visibility(self, state):
        """
        パスワードの表示/非表示を切り替えます。

        Args:
            state (int): チェックボックスの状態
        """
        if self.show_password_cb.isChecked():
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def _handle_login(self):
        """
        ログイン処理を実行します。
        簡易的なバリデーションを行い、成功した場合はシグナルを発行します。
        """
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "エラー", "ユーザー名とパスワードを入力してください。")
            return

        if authenticate(username, password):
            # 成功した場合はシグナルを発行
            self.login_successful.emit()
        else:
            QMessageBox.warning(self, "エラー", "ユーザー名またはパスワードが間違っています。")
