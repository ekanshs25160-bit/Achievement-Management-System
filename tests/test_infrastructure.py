"""
Test the testing infrastructure setup.

This module contains basic tests to verify that the testing infrastructure
is properly configured and all fixtures are working correctly.
"""

import pytest
import sqlite3
import os


def test_app_fixture(app):
    """Test that the app fixture provides a Flask application."""
    assert app is not None
    assert app.config['TESTING'] is True
    assert 'DB_PATH' in app.config


def test_client_fixture(client):
    """Test that the client fixture provides a test client."""
    assert client is not None
    # Test that we can make a request
    response = client.get('/')
    assert response.status_code == 200


def test_test_db_fixture(test_db):
    """Test that the test_db fixture creates a database with proper schema."""
    assert test_db is not None
    assert os.path.exists(test_db)
    
    # Verify tables exist
    connection = sqlite3.connect(test_db)
    cursor = connection.cursor()
    
    # Check student table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student'")
    assert cursor.fetchone() is not None
    
    # Check teacher table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teacher'")
    assert cursor.fetchone() is not None
    
    # Check achievements table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='achievements'")
    assert cursor.fetchone() is not None
    
    connection.close()


def test_db_connection_fixture(db_connection):
    """Test that the db_connection fixture provides a working connection."""
    assert db_connection is not None
    
    # Test that we can execute a query
    cursor = db_connection.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    assert result[0] == 1


def test_sample_student_data_fixture(sample_student_data):
    """Test that the sample_student_data fixture provides valid data."""
    assert sample_student_data is not None
    assert 'student_name' in sample_student_data
    assert 'student_id' in sample_student_data
    assert 'email' in sample_student_data
    assert 'password' in sample_student_data
    assert 'student_dept' in sample_student_data


def test_sample_teacher_data_fixture(sample_teacher_data):
    """Test that the sample_teacher_data fixture provides valid data."""
    assert sample_teacher_data is not None
    assert 'teacher_name' in sample_teacher_data
    assert 'teacher_id' in sample_teacher_data
    assert 'email' in sample_teacher_data
    assert 'password' in sample_teacher_data
    assert 'teacher_dept' in sample_teacher_data


def test_sample_achievement_data_fixture(sample_achievement_data):
    """Test that the sample_achievement_data fixture provides valid data."""
    assert sample_achievement_data is not None
    assert 'student_id' in sample_achievement_data
    assert 'teacher_id' in sample_achievement_data
    assert 'achievement_type' in sample_achievement_data
    assert 'event_name' in sample_achievement_data


def test_database_isolation(test_db, db_connection):
    """Test that each test gets a fresh database."""
    # Insert a record
    cursor = db_connection.cursor()
    cursor.execute("""
        INSERT INTO student (student_name, student_id, email, phone_number, 
                           password, student_gender, student_dept)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ('Test Student', 'TEST001', 'test@example.com', '1234567890',
          'password', 'Male', 'CS'))
    db_connection.commit()
    
    # Verify it was inserted
    cursor.execute("SELECT COUNT(*) FROM student")
    count = cursor.fetchone()[0]
    assert count == 1


def test_database_isolation_verification(test_db, db_connection):
    """Verify that the previous test's data is not present (database isolation works)."""
    cursor = db_connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM student")
    count = cursor.fetchone()[0]
    # Should be 0 because each test gets a fresh database
    assert count == 0


@pytest.mark.unit
def test_unit_marker():
    """Test that the unit marker is properly configured."""
    assert True


@pytest.mark.property
def test_property_marker():
    """Test that the property marker is properly configured."""
    assert True


@pytest.mark.integration
def test_integration_marker():
    """Test that the integration marker is properly configured."""
    assert True
