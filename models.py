"""
SQLAlchemy ORM models for Achievement Management System.
All database interactions go through these models; SQLAlchemy handles
parameterization and escaping automatically.
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Student(db.Model):
    __tablename__ = "student"

    student_name = db.Column(db.String(120), nullable=False)
    student_id = db.Column(db.String(50), primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20))
    password = db.Column(db.String(256), nullable=False)
    student_gender = db.Column(db.String(20))
    student_dept = db.Column(db.String(80))

    achievements = db.relationship(
        "Achievement",
        backref="student",
        foreign_keys="Achievement.student_id",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<Student {self.student_id}>"


class Teacher(db.Model):
    __tablename__ = "teacher"

    teacher_name = db.Column(db.String(120), nullable=False)
    teacher_id = db.Column(db.String(50), primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20))
    password = db.Column(db.String(256), nullable=False)
    teacher_gender = db.Column(db.String(20))
    teacher_dept = db.Column(db.String(80))

    achievements = db.relationship(
        "Achievement",
        backref="teacher",
        foreign_keys="Achievement.teacher_id",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<Teacher {self.teacher_id}>"


class Achievement(db.Model):
    __tablename__ = "achievements"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(50), db.ForeignKey("student.student_id"), nullable=False)
    teacher_id = db.Column(db.String(50), db.ForeignKey("teacher.teacher_id"), nullable=False)
    achievement_type = db.Column(db.String(80), nullable=False)
    event_name = db.Column(db.String(200), nullable=False)
    achievement_date = db.Column(db.Date, nullable=False)
    organizer = db.Column(db.String(200), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    achievement_description = db.Column(db.Text)
    certificate_path = db.Column(db.String(300))
    symposium_theme = db.Column(db.String(200))
    programming_language = db.Column(db.String(80))
    coding_platform = db.Column(db.String(100))
    paper_title = db.Column(db.String(300))
    journal_name = db.Column(db.String(200))
    conference_level = db.Column(db.String(80))
    conference_role = db.Column(db.String(80))
    team_size = db.Column(db.Integer)
    project_title = db.Column(db.String(300))
    database_type = db.Column(db.String(80))
    difficulty_level = db.Column(db.String(80))
    other_description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Achievement {self.id} {self.event_name}>"
