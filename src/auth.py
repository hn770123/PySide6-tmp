"""
認証モジュール
============

ユーザー認証とパスワードハッシュ化機能を提供します。
"""

import hashlib
import os
import binascii
try:
    from database import get_user
except ImportError:
    from src.database import get_user

def hash_password(password):
    """
    パスワードをソルト付きでハッシュ化します (PBKDF2_HMAC).

    Args:
        password (str): 平文のパスワード

    Returns:
        str: ソルトとハッシュ化されたパスワード（hex文字列）の組み合わせ (salt:hash)
    """
    salt = os.urandom(32) # 32 bytes salt
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000 # iterations
    )
    return f"{binascii.hexlify(salt).decode('utf-8')}:{binascii.hexlify(pwd_hash).decode('utf-8')}"

def verify_password(stored_password, input_password):
    """
    入力されたパスワードが保存されたハッシュと一致するか検証します。

    Args:
        stored_password (str): 保存されているパスワード文字列 (salt:hash)
        input_password (str): 入力されたパスワード

    Returns:
        bool: 一致する場合はTrue
    """
    try:
        salt_hex, hash_hex = stored_password.split(':')
        salt = binascii.unhexlify(salt_hex)
        stored_hash = binascii.unhexlify(hash_hex)

        input_hash = hashlib.pbkdf2_hmac(
            'sha256',
            input_password.encode('utf-8'),
            salt,
            100000
        )
        # 比較には定数時間比較を用いるのが望ましいが、ここでは簡易的に等価演算子を使用
        return stored_hash == input_hash
    except (ValueError, binascii.Error):
        return False

def authenticate(username, password):
    """
    ユーザー名とパスワードを使用して認証を行います。

    Args:
        username (str): ユーザー名
        password (str): パスワード

    Returns:
        bool: 認証成功時はTrue、失敗時はFalse
    """
    user = get_user(username)
    if not user:
        return False

    # user[2] is password_hash (id, username, password_hash)
    stored_hash = user[2]
    return verify_password(stored_hash, password)
