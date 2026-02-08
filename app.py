from flask import Flask, render_template, request, redirect, url_for, session
import os
import secrets
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import logging

from models import db, Student, Teacher, Achievement

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Stable Secret Key Configuration
# Load SECRET_KEY from environment variable for production
SECRET_KEY = os.environ.get('SECRET_KEY')
if SECRET_KEY:
    # Validate minimum key length (32 bytes = 64 hex characters)
    if len(SECRET_KEY) < 64:
        app.logger.warning("SECRET_KEY is shorter than recommended 64 characters (32 bytes)")
    app.secret_key = SECRET_KEY
else:
    # Development fallback - generate a new key
    app.secret_key = secrets.token_hex(32)  # 32 bytes = 64 hex characters
    app.logger.warning("Using generated secret key. Set SECRET_KEY environment variable for production.")

# Database: SQLAlchemy ORM (parameterized queries and escaping handled automatically)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
instance_dir = os.path.join(BASE_DIR, "instance")
os.makedirs(instance_dir, exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(instance_dir, "ams.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)


# Password Security Module
def hash_password(plain_password):
    """
    Hash a plain-text password using werkzeug's generate_password_hash.
    
    Args:
        plain_password: The plain-text password to hash
        
    Returns:
        The hashed password string
        
    Raises:
        ValueError: If password is empty or None
    """
    if plain_password is None or plain_password == "":
        raise ValueError("Password cannot be empty or None")
    
    try:
        return generate_password_hash(plain_password)
    except Exception as e:
        app.logger.error(f"Password hashing failed: {e}")
        raise


def verify_password(stored_hash, provided_password):
    """
    Verify a provided password against a stored hash.
    
    Args:
        stored_hash: The stored password hash from database
        provided_password: The plain-text password provided by user
        
    Returns:
        True if password matches, False otherwise
    """
    if stored_hash is None or provided_password is None:
        return False
    
    if stored_hash == "" or provided_password == "":
        return False
    
    try:
        return check_password_hash(stored_hash, provided_password)
    except Exception as e:
        app.logger.error(f"Password verification failed: {e}")
        return False


def init_db():
    """Create tables if they do not exist. Safe to call on every startup."""
    with app.app_context():
        db.create_all()


# Define a function to check allowed file extensions
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Define upload folder path for certificates
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')

# Create the upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/index")
def index():
    return render_template("index.html")


@app.route("/student", methods=["GET", "POST"])
def student():
    if request.method == "POST":
        student_id = request.form.get("sname")
        password = request.form.get("password")
        try:
            student_obj = Student.query.filter_by(student_id=student_id).first()
            if student_obj and verify_password(student_obj.password, password):
                session["logged_in"] = True
                session["student_id"] = student_obj.student_id
                session["student_name"] = student_obj.student_name
                session["student_dept"] = student_obj.student_dept
                return redirect(url_for("student-dashboard"))
            app.logger.warning("Failed login attempt for student_id: %s", student_id)
            return render_template("student.html", error="Invalid credentials. Please try again.")
        except Exception as e:
            app.logger.exception("Database error in student login")
            return render_template("student.html", error="A database error occurred. Please try again.")
    return render_template("student.html")


@app.route("/teacher", methods=["GET", "POST"])
def teacher():
    if request.method == "POST":
        teacher_id = request.form.get("tname")
        password = request.form.get("password")
        try:
            teacher_obj = Teacher.query.filter_by(teacher_id=teacher_id).first()
            if teacher_obj and verify_password(teacher_obj.password, password):
                session["logged_in"] = True
                session["teacher_id"] = teacher_obj.teacher_id
                session["teacher_name"] = teacher_obj.teacher_name
                session["teacher_dept"] = teacher_obj.teacher_dept
                return redirect(url_for("teacher-dashboard"))
            app.logger.warning("Failed login attempt for teacher_id: %s", teacher_id)
            return render_template("teacher.html", error="Invalid credentials. Please try again.")
        except Exception as e:
            app.logger.exception("Database error in teacher login")
            return render_template("teacher.html", error="A database error occurred. Please try again.")
    return render_template("teacher.html")


@app.route("/logout")
def logout():
    """
    Clear user session and redirect to home page.
    
    This route handles logout for both students and teachers.
    It clears all session data and redirects to the home page.
    """
    try:
        session.clear()
    except Exception as e:
        app.logger.error(f"Error during logout: {e}")
    return redirect(url_for('home'))


@app.route("/student-new", methods=["GET", "POST"])
def student_new():
    if request.method == "POST":
        student_name = request.form.get("student_name")
        student_id = request.form.get("student_id")
        email = request.form.get("email")
        phone_number = request.form.get("phone_number")
        password = request.form.get("password")
        student_gender = request.form.get("student_gender")
        student_dept = request.form.get("student_dept")
        try:
            hashed_password = hash_password(password)
        except ValueError:
            return render_template(
                "student_new_2.html",
                error="Password cannot be empty. Please try again.",
            )
        except Exception:
            app.logger.exception("Password hashing failed")
            return render_template(
                "student_new_2.html",
                error="Unable to create account. Please try again.",
            )
        try:
            student_obj = Student(
                student_name=student_name,
                student_id=student_id,
                email=email,
                phone_number=phone_number,
                password=hashed_password,
                student_gender=student_gender,
                student_dept=student_dept,
            )
            db.session.add(student_obj)
            db.session.commit()
            return redirect(url_for("student"))
        except Exception:
            db.session.rollback()
            app.logger.exception("Database error in student registration")
            return render_template(
                "student_new_2.html",
                error="A database error occurred. Please try again.",
            )
    return render_template("student_new_2.html")


@app.route("/teacher-new", endpoint="teacher-new", methods=["GET", "POST"])
def teacher_new():
    if request.method == "POST":
        teacher_name = request.form.get("teacher_name")
        teacher_id = request.form.get("teacher_id")
        email = request.form.get("email")
        phone_number = request.form.get("phone_number")
        password = request.form.get("password")
        teacher_gender = request.form.get("teacher_gender")
        teacher_dept = request.form.get("teacher_dept")
        try:
            hashed_password = hash_password(password)
        except ValueError:
            return render_template(
                "teacher_new_2.html",
                error="Password cannot be empty. Please try again.",
            )
        except Exception:
            app.logger.exception("Password hashing failed")
            return render_template(
                "teacher_new_2.html",
                error="Unable to create account. Please try again.",
            )
        try:
            teacher_obj = Teacher(
                teacher_name=teacher_name,
                teacher_id=teacher_id,
                email=email,
                phone_number=phone_number,
                password=hashed_password,
                teacher_gender=teacher_gender,
                teacher_dept=teacher_dept,
            )
            db.session.add(teacher_obj)
            db.session.commit()
            return redirect(url_for("teacher"))
        except Exception:
            db.session.rollback()
            app.logger.exception("Database error in teacher registration")
            return render_template(
                "teacher_new_2.html",
                error="A database error occurred. Please try again.",
            )
    return render_template("teacher_new_2.html")


@app.route("/teacher-achievements", endpoint="teacher-achievements")
def teacher_achievements():
    return render_template("teacher_achievements_2.html")


@app.route("/submit_achievements", endpoint="submit_achievements", methods=["GET", "POST"])
def submit_achievements():
    if not session.get("logged_in") or not session.get("teacher_id"):
        return redirect(url_for("teacher"))
    teacher_id = session.get("teacher_id")

    if request.method == "POST":
        student_id = request.form.get("student_id")
        student_obj = Student.query.filter_by(student_id=student_id).first()
        if not student_obj:
            return render_template(
                "submit_achievements.html",
                error="Student ID does not exist in the system.",
            )
        student_name = student_obj.student_name

        certificate_path = None
        if "certificate" in request.files:
            file = request.files["certificate"]
            if file and file.filename:
                if allowed_file(file.filename):
                    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    secure_name = f"{timestamp}_{secure_filename(file.filename)}"
                    file_path = os.path.join(UPLOAD_FOLDER, secure_name)
                    file.save(file_path)
                    certificate_path = f"uploads/{secure_name}"
                else:
                    return render_template(
                        "submit_achievements.html",
                        error="Invalid file type. Please upload PDF, PNG, JPG, or JPEG files.",
                    )

        team_size_raw = request.form.get("team_size")
        team_size = int(team_size_raw) if team_size_raw and team_size_raw.strip() else None

        date_str = request.form.get("achievement_date")
        if not date_str:
            return render_template(
                "submit_achievements.html",
                error="Achievement date is required.",
            )
        try:
            achievement_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return render_template(
                "submit_achievements.html",
                error="Invalid date format. Please use YYYY-MM-DD.",
            )
        try:
            achievement = Achievement(
                student_id=student_id,
                teacher_id=teacher_id,
                achievement_type=request.form.get("achievement_type"),
                event_name=request.form.get("event_name"),
                achievement_date=achievement_date,
                organizer=request.form.get("organizer"),
                position=request.form.get("position"),
                achievement_description=request.form.get("achievement_description"),
                certificate_path=certificate_path,
                symposium_theme=request.form.get("symposium_theme"),
                programming_language=request.form.get("programming_language"),
                coding_platform=request.form.get("coding_platform"),
                paper_title=request.form.get("paper_title"),
                journal_name=request.form.get("journal_name"),
                conference_level=request.form.get("conference_level"),
                conference_role=request.form.get("conference_role"),
                team_size=team_size,
                project_title=request.form.get("project_title"),
                database_type=request.form.get("database_type"),
                difficulty_level=request.form.get("difficulty_level"),
                other_description=request.form.get("other_description"),
            )
            db.session.add(achievement)
            db.session.commit()
            return render_template(
                "submit_achievements.html",
                success=f"Achievement of {student_name} has been successfully registered!!",
            )
        except Exception:
            db.session.rollback()
            app.logger.exception("Error submitting achievement")
            return render_template(
                "submit_achievements.html",
                error="An error occurred. Please try again.",
            )

    return redirect(url_for("teacher-dashboard", success="Achievement submitted successfully!"))


@app.route("/student-achievements", endpoint="student-achievements")
def student_achievements():
    # Check if user is logged in
    if not session.get('logged_in'):
        return redirect(url_for('student'))

    # Get the current user data from session
    student_data = {
        'id': session.get('student_id'),
        'name': session.get('student_name'),
        'dept': session.get('student_dept')
    }
    return render_template("student_achievements_1.html", student=student_data)


@app.route("/student-dashboard", endpoint="student-dashboard")
def student_dashboard():
    # Check if user is logged in
    if not session.get('logged_in'):
        return redirect(url_for('student'))

    # Get the current user data from session
    student_data = {
        'id': session.get('student_id'),
        'name': session.get('student_name'),
        'dept': session.get('student_dept')
    }
        
    return render_template("student_dashboard.html", student=student_data)


@app.route("/teacher-dashboard", endpoint="teacher-dashboard")
def teacher_dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("teacher"))
    teacher_id = session.get("teacher_id")
    teacher_data = {
        "id": teacher_id,
        "name": session.get("teacher_name"),
        "dept": session.get("teacher_dept"),
    }

    total_achievements = Achievement.query.filter_by(teacher_id=teacher_id).count()
    students_managed = (
        db.session.query(db.func.count(db.func.distinct(Achievement.student_id)))
        .filter(Achievement.teacher_id == teacher_id)
        .scalar()
        or 0
    )
    one_week_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).date()
    this_week_count = (
        Achievement.query.filter(
            Achievement.teacher_id == teacher_id,
            Achievement.achievement_date >= one_week_ago,
        ).count()
    )
    recent_entries = (
        Achievement.query.filter_by(teacher_id=teacher_id)
        .order_by(Achievement.created_at.desc())
        .limit(5)
        .all()
    )

    stats = {
        "total_achievements": total_achievements,
        "students_managed": students_managed,
        "this_week": this_week_count,
    }
    return render_template(
        "teacher_dashboard.html",
        teacher=teacher_data,
        stats=stats,
        recent_entries=recent_entries,
    )



@app.route("/all-achievements", endpoint="all-achievements")
def all_achievements():
    if not session.get("logged_in"):
        return redirect(url_for("teacher"))
    teacher_id = session.get("teacher_id")
    achievements = (
        Achievement.query.filter_by(teacher_id=teacher_id)
        .order_by(Achievement.achievement_date.desc())
        .all()
    )
    return render_template("all_achievements.html", achievements=achievements)

    
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)