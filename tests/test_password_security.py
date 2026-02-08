"""
Unit tests for password hashing and verification functions.

Tests the hash_password() and verify_password() functions to ensure
they properly hash passwords and verify them against stored hashes.
"""

import pytest
import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import hash_password, verify_password


class TestPasswordHashing:
    """Test suite for password hashing functionality."""
    
    def test_hash_password_returns_hashed_string(self):
        """Test that hash_password returns a hashed password string."""
        plain_password = "MySecurePassword123!"
        hashed = hash_password(plain_password)
        
        # Verify it's a string
        assert isinstance(hashed, str)
        # Verify it's not the same as the plain password
        assert hashed != plain_password
        # Verify it has a valid hash format (scrypt or pbkdf2)
        assert hashed.startswith('scrypt:') or hashed.startswith('pbkdf2:sha256:')
    
    def test_hash_password_different_for_same_input(self):
        """Test that hashing the same password twice produces different hashes (due to salt)."""
        plain_password = "TestPassword456"
        hash1 = hash_password(plain_password)
        hash2 = hash_password(plain_password)
        
        # Hashes should be different due to random salt
        assert hash1 != hash2
    
    def test_hash_password_raises_error_for_none(self):
        """Test that hash_password raises ValueError for None input."""
        with pytest.raises(ValueError, match="Password cannot be empty or None"):
            hash_password(None)
    
    def test_hash_password_raises_error_for_empty_string(self):
        """Test that hash_password raises ValueError for empty string."""
        with pytest.raises(ValueError, match="Password cannot be empty or None"):
            hash_password("")


class TestPasswordVerification:
    """Test suite for password verification functionality."""
    
    def test_verify_password_correct_password(self):
        """Test that verify_password returns True for correct password."""
        plain_password = "CorrectPassword789"
        hashed = hash_password(plain_password)
        
        # Verify with correct password
        assert verify_password(hashed, plain_password) is True
    
    def test_verify_password_incorrect_password(self):
        """Test that verify_password returns False for incorrect password."""
        plain_password = "CorrectPassword789"
        wrong_password = "WrongPassword123"
        hashed = hash_password(plain_password)
        
        # Verify with wrong password
        assert verify_password(hashed, wrong_password) is False
    
    def test_verify_password_none_hash(self):
        """Test that verify_password returns False for None hash."""
        assert verify_password(None, "somepassword") is False
    
    def test_verify_password_none_password(self):
        """Test that verify_password returns False for None password."""
        hashed = hash_password("testpassword")
        assert verify_password(hashed, None) is False
    
    def test_verify_password_empty_hash(self):
        """Test that verify_password returns False for empty hash."""
        assert verify_password("", "somepassword") is False
    
    def test_verify_password_empty_password(self):
        """Test that verify_password returns False for empty password."""
        hashed = hash_password("testpassword")
        assert verify_password(hashed, "") is False
    
    def test_verify_password_with_special_characters(self):
        """Test password verification with special characters."""
        plain_password = "P@ssw0rd!#$%^&*()"
        hashed = hash_password(plain_password)
        
        assert verify_password(hashed, plain_password) is True
        assert verify_password(hashed, "P@ssw0rd!#$%^&*()X") is False
    
    def test_verify_password_with_long_password(self):
        """Test password verification with a long password."""
        plain_password = "a" * 200  # 200 character password
        hashed = hash_password(plain_password)
        
        assert verify_password(hashed, plain_password) is True
        assert verify_password(hashed, "a" * 199) is False


class TestPasswordSecurityIntegration:
    """Integration tests for password security functions."""
    
    def test_multiple_passwords_hash_and_verify(self):
        """Test hashing and verifying multiple different passwords."""
        passwords = [
            "Password1",
            "AnotherPassword2",
            "YetAnotherOne3",
            "FinalPassword4"
        ]
        
        # Hash all passwords
        hashes = [hash_password(pwd) for pwd in passwords]
        
        # Verify each password matches its own hash
        for i, pwd in enumerate(passwords):
            assert verify_password(hashes[i], pwd) is True
        
        # Verify passwords don't match other hashes
        for i, pwd in enumerate(passwords):
            for j, hash_val in enumerate(hashes):
                if i != j:
                    assert verify_password(hash_val, pwd) is False
