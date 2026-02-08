"""
Integration tests for student registration with password hashing.

Tests that the /student-new route properly hashes passwords before storing them.
"""

import pytest
import sys
import os
import sqlite3

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, DB_PATH, verify_password


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def clean_db():
    """Clean up the test database before and after tests."""
    # Remove any existing test data
    if os.path.exists(DB_PATH):
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM student WHERE student_id LIKE 'TEST%'")
        connection.commit()
        connection.close()
    
    yield
    
    # Clean up after test
    if os.path.exists(DB_PATH):
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM student WHERE student_id LIKE 'TEST%'")
        connection.commit()
        connection.close()


class TestStudentRegistration:
    """Test suite for student registration with password hashing."""
    
    def test_student_registration_hashes_password(self, client, clean_db):
        """Test that student registration hashes the password before storing."""
        # Register a new student
        plain_password = "TestPassword123!"
        response = client.post('/student-new', data={
            'student_name': 'Test Student',
            'student_id': 'TEST001',
            'email': 'test001@example.com',
            'phone_number': '1234567890',
            'password': plain_password,
            'student_gender': 'Male',
            'student_dept': 'Computer Science'
        }, follow_redirects=False)
        
        # Should redirect to login page on success
        assert response.status_code == 302
        assert '/student' in response.location
        
        # Query database to verify password is hashed
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        cursor.execute("SELECT password FROM student WHERE student_id = ?", ('TEST001',))
        result = cursor.fetchone()
        connection.close()
        
        assert result is not None
        stored_password = result[0]
        
        # Verify password is hashed (not plain text)
        assert stored_password != plain_password
        
        # Verify it's a valid hash format
        assert stored_password.startswith('scrypt:') or stored_password.startswith('pbkdf2:sha256:')
        
        # Verify the hash can be verified with the original password
        assert verify_password(stored_password, plain_password) is True
    
    def test_student_registration_empty_password_error(self, client, clean_db):
        """Test that registration with empty password shows error."""
        response = client.post('/student-new', data={
            'student_name': 'Test Student 2',
            'student_id': 'TEST002',
            'email': 'test002@example.com',
            'phone_number': '1234567890',
            'password': '',
            'student_gender': 'Female',
            'student_dept': 'Computer Science'
        }, follow_redirects=True)
        
        # Should show error message
        assert response.status_code == 200
        assert b'Password cannot be empty' in response.data or b'Unable to create account' in response.data
    
    def test_student_registration_with_special_characters(self, client, clean_db):
        """Test that registration works with special characters in password."""
        plain_password = "P@ssw0rd!#$%^&*()"
        response = client.post('/student-new', data={
            'student_name': 'Test Student 3',
            'student_id': 'TEST003',
            'email': 'test003@example.com',
            'phone_number': '1234567890',
            'password': plain_password,
            'student_gender': 'Male',
            'student_dept': 'Computer Science'
        }, follow_redirects=False)
        
        # Should redirect to login page on success
        assert response.status_code == 302
        
        # Query database to verify password is hashed
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        cursor.execute("SELECT password FROM student WHERE student_id = ?", ('TEST003',))
        result = cursor.fetchone()
        connection.close()
        
        assert result is not None
        stored_password = result[0]
        
        # Verify password is hashed and can be verified
        assert stored_password != plain_password
        assert verify_password(stored_password, plain_password) is True
