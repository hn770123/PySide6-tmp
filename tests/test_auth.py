import unittest
import sys
import os

# Add src to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import database
import auth

class TestAuth(unittest.TestCase):
    def setUp(self):
        # Use a test database
        self.test_db = "test_app.db"
        # Monkey patch database.DB_NAME
        database.DB_NAME = self.test_db
        database.init_db()

    def tearDown(self):
        # Clean up database
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_hash_password(self):
        password = "password123"
        hashed = auth.hash_password(password)
        self.assertNotEqual(password, hashed)
        # Check format salt:hash
        parts = hashed.split(':')
        self.assertEqual(len(parts), 2)
        self.assertEqual(len(parts[0]), 64) # 32 bytes salt = 64 hex chars
        self.assertEqual(len(parts[1]), 64) # SHA256 hash = 64 hex chars

    def test_verify_password(self):
        password = "password123"
        hashed = auth.hash_password(password)
        self.assertTrue(auth.verify_password(hashed, password))
        self.assertFalse(auth.verify_password(hashed, "wrongpassword"))

    def test_add_and_get_user(self):
        username = "testuser"
        password = "password123"
        hashed = auth.hash_password(password)

        # Add user
        self.assertTrue(database.add_user(username, hashed))

        # Get user
        user = database.get_user(username)
        self.assertIsNotNone(user)
        self.assertEqual(user[1], username)
        self.assertEqual(user[2], hashed)

        # Duplicate user
        self.assertFalse(database.add_user(username, hashed))

    def test_authenticate(self):
        username = "authuser"
        password = "secretpassword"
        hashed = auth.hash_password(password)
        database.add_user(username, hashed)

        # Success
        self.assertTrue(auth.authenticate(username, password))

        # Fail - wrong password
        self.assertFalse(auth.authenticate(username, "wrong"))

        # Fail - wrong user
        self.assertFalse(auth.authenticate("unknown", password))

if __name__ == '__main__':
    unittest.main()
