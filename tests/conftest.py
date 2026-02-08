"""
Pytest configuration and fixtures for testing the Achievement Management System.

This module provides shared fixtures for:
- Flask test client
- Test database setup and teardown
- Sample test data
- Database connection helpers
"""

import pytest
import sqlite3
import os
import tempfile
from flask import Flask
import sys

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app


@pytest.fixture(scope='function')
def app():
    """
    Create and configure a Flask application instance for testing.
    
    This fixture creates a new app instance with testing configuration
    for each test function. The app uses a temporary test database.
    
    Yields:
        Flask: Configured Flask application instance
    """
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Configure app for testing
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret-key-for-testing-only'
    flask_app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    # Override the database path for testing
    flask_app.config['DB_PATH'] = db_path
    
    # Store original DB_PATH to restore later
    original_db_path = None
    if hasattr(flask_app, 'DB_PATH'):
        original_db_path = flask_app.DB_PATH
    
    # Update the global DB_PATH in app module
    import app as app_module
    app_module.DB_PATH = db_path
    
    yield flask_app
    
    # Cleanup: close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)
    
    # Restore original DB_PATH if it existed
    if original_db_path:
        app_module.DB_PATH = original_db_path


@pytest.fixture(scope='function')
def client(app):
    """
    Create a test client for the Flask application.
    
    This fixture provides a test client that can be used to make
    requests to the application without running a server.
    
    Args:
        app: Flask application fixture
        
    Returns:
        FlaskClient: Test client for making requests
    """
    return app.test_client()


@pytest.fixture(scope='function')
def test_db(app):
    """
    Initialize a test database with the required schema.
    
    This fixture creates the student, teacher, and achievements tables
    in the test database. The database is automatically cleaned up
    after each test.
    
    Args:
        app: Flask application fixture
        
    Returns:
        str: Path to the test database file
    """
    db_path = app.config['DB_PATH']
    
    # Create tables
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    
    # Create student table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS student (
        student_name TEXT NOT NULL,
        student_id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        phone_number TEXT,
        password TEXT NOT NULL,
        student_gender TEXT,
        student_dept TEXT
    )
    ''')
    
    # Create teacher table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS teacher (
        teacher_name TEXT NOT NULL,
        teacher_id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        phone_number TEXT,
        password TEXT NOT NULL,
        teacher_gender TEXT,
        teacher_dept TEXT
    )
    ''')
    
    # Create achievements table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id TEXT NOT NULL,
        student_id TEXT NOT NULL,
        achievement_type TEXT NOT NULL,
        event_name TEXT NOT NULL,
        achievement_date DATE NOT NULL,
        organizer TEXT NOT NULL,
        position TEXT NOT NULL,
        achievement_description TEXT,
        certificate_path TEXT,
        
        symposium_theme TEXT,
        programming_language TEXT,
        coding_platform TEXT,
        paper_title TEXT,
        journal_name TEXT,
        conference_level TEXT,
        conference_role TEXT,
        team_size INTEGER,
        project_title TEXT,
        database_type TEXT,
        difficulty_level TEXT,
        other_description TEXT,
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES student(student_id),
        FOREIGN KEY (teacher_id) REFERENCES teacher(teacher_id)
    )
    ''')
    
    connection.commit()
    connection.close()
    
    return db_path


@pytest.fixture(scope='function')
def db_connection(test_db):
    """
    Provide a database connection for direct database operations in tests.
    
    This fixture creates a connection to the test database and ensures
    it's properly closed after the test completes.
    
    Args:
        test_db: Test database fixture
        
    Yields:
        sqlite3.Connection: Database connection object
    """
    connection = sqlite3.connect(test_db)
    yield connection
    connection.close()


@pytest.fixture
def sample_student_data():
    """
    Provide sample student data for testing.
    
    Returns:
        dict: Dictionary containing sample student information
    """
    return {
        'student_name': 'John Doe',
        'student_id': 'S12345',
        'email': 'john.doe@example.com',
        'phone_number': '1234567890',
        'password': 'SecurePassword123!',
        'student_gender': 'Male',
        'student_dept': 'Computer Science'
    }


@pytest.fixture
def sample_teacher_data():
    """
    Provide sample teacher data for testing.
    
    Returns:
        dict: Dictionary containing sample teacher information
    """
    return {
        'teacher_name': 'Jane Smith',
        'teacher_id': 'T67890',
        'email': 'jane.smith@example.com',
        'phone_number': '0987654321',
        'password': 'TeacherPass456!',
        'teacher_gender': 'Female',
        'teacher_dept': 'Computer Science'
    }


@pytest.fixture
def sample_achievement_data():
    """
    Provide sample achievement data for testing.
    
    Returns:
        dict: Dictionary containing sample achievement information
    """
    return {
        'student_id': 'S12345',
        'teacher_id': 'T67890',
        'achievement_type': 'Coding Competition',
        'event_name': 'National Coding Challenge 2024',
        'achievement_date': '2024-01-15',
        'organizer': 'Tech Institute',
        'position': '1st Place',
        'achievement_description': 'Won first place in algorithm competition',
        'programming_language': 'Python',
        'coding_platform': 'HackerRank'
    }


@pytest.fixture
def authenticated_student_session(client, test_db, sample_student_data):
    """
    Create an authenticated student session for testing protected routes.
    
    This fixture registers a student, logs them in, and provides a client
    with an active session.
    
    Args:
        client: Flask test client
        test_db: Test database fixture
        sample_student_data: Sample student data fixture
        
    Returns:
        tuple: (client, student_data) - Client with active session and student info
    """
    # Register the student (with plain text password for now)
    connection = sqlite3.connect(test_db)
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO student (student_name, student_id, email, phone_number, 
                           password, student_gender, student_dept)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        sample_student_data['student_name'],
        sample_student_data['student_id'],
        sample_student_data['email'],
        sample_student_data['phone_number'],
        sample_student_data['password'],
        sample_student_data['student_gender'],
        sample_student_data['student_dept']
    ))
    connection.commit()
    connection.close()
    
    # Log in the student
    with client:
        client.post('/student', data={
            'sname': sample_student_data['student_id'],
            'password': sample_student_data['password']
        })
    
    return client, sample_student_data


@pytest.fixture
def authenticated_teacher_session(client, test_db, sample_teacher_data):
    """
    Create an authenticated teacher session for testing protected routes.
    
    This fixture registers a teacher, logs them in, and provides a client
    with an active session.
    
    Args:
        client: Flask test client
        test_db: Test database fixture
        sample_teacher_data: Sample teacher data fixture
        
    Returns:
        tuple: (client, teacher_data) - Client with active session and teacher info
    """
    # Register the teacher (with plain text password for now)
    connection = sqlite3.connect(test_db)
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO teacher (teacher_name, teacher_id, email, phone_number, 
                           password, teacher_gender, teacher_dept)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        sample_teacher_data['teacher_name'],
        sample_teacher_data['teacher_id'],
        sample_teacher_data['email'],
        sample_teacher_data['phone_number'],
        sample_teacher_data['password'],
        sample_teacher_data['teacher_gender'],
        sample_teacher_data['teacher_dept']
    ))
    connection.commit()
    connection.close()
    
    # Log in the teacher
    with client:
        client.post('/teacher', data={
            'tname': sample_teacher_data['teacher_id'],
            'password': sample_teacher_data['password']
        })
    
    return client, sample_teacher_data


# Hypothesis strategies for property-based testing
# These will be imported by test files that need them

def get_valid_student_id_strategy():
    """
    Get a Hypothesis strategy for generating valid student IDs.
    
    Returns:
        SearchStrategy: Strategy for generating student IDs
    """
    from hypothesis import strategies as st
    return st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='_-'
    ))


def get_valid_email_strategy():
    """
    Get a Hypothesis strategy for generating valid email addresses.
    
    Returns:
        SearchStrategy: Strategy for generating emails
    """
    from hypothesis import strategies as st
    return st.emails()


def get_valid_password_strategy():
    """
    Get a Hypothesis strategy for generating valid passwords.
    
    Returns:
        SearchStrategy: Strategy for generating passwords
    """
    from hypothesis import strategies as st
    return st.text(min_size=1, max_size=200)


def get_valid_name_strategy():
    """
    Get a Hypothesis strategy for generating valid names.
    
    Returns:
        SearchStrategy: Strategy for generating names
    """
    from hypothesis import strategies as st
    return st.text(min_size=1, max_size=100, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll'),
        whitelist_characters=' -.'
    ))
