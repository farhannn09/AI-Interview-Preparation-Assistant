import os
import uuid

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename

from database import get_db_connection
from resume_parser import (
    extract_text_from_pdf,
    extract_skills
)
from question_generator import generate_interview_questions
from answer_evaluator import evaluate_answer


app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "development_secret_key"
)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        # Validate name
        if not name:

            return "Name cannot be empty."

        # Validate email
        if "@" not in email or "." not in email:

            return "Please enter a valid email address."

        # Validate password
        if len(password) < 6:

            return "Password must contain at least 6 characters."

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check existing email
        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            cursor.close()
            connection.close()

            return "An account with this email already exists."

        # Hash password
        hashed_password = generate_password_hash(password)

        # Insert user
        cursor.execute(
            """
            INSERT INTO users
            (name, email, password)
            VALUES (%s, %s, %s)
            """,
            (
                name,
                email,
                hashed_password
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        return "Registration successful!"

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect("/dashboard")

        else:

            return "Invalid email or password!"

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor()

    # Get user
    cursor.execute(
        """
        SELECT name
        FROM users
        WHERE id = %s
        """,
        (session["user_id"],)
    )

    user = cursor.fetchone()

    # Check resume
    cursor.execute(
        """
        SELECT id
        FROM resumes
        WHERE user_id = %s
        LIMIT 1
        """,
        (session["user_id"],)
    )

    resume = cursor.fetchone()

    # Get interview statistics
    cursor.execute(
        """
        SELECT
            COUNT(*) AS total_interviews,
            MAX(total_score) AS best_score
        FROM interviews
        WHERE user_id = %s
        """,
        (session["user_id"],)
    )

    stats = cursor.fetchone()

    cursor.close()
    connection.close()

    total_interviews = stats["total_interviews"] or 0

    best_score = stats["best_score"] or 0

    return render_template(
        "dashboard.html",
        user=user,
        resume=resume,
        total_interviews=total_interviews,
        best_score=best_score,
        job_role=session.get("job_role")
    )


# =========================================================
# RESUME UPLOAD
# =========================================================

@app.route("/upload", methods=["GET", "POST"])
def upload_resume():

    if "user_id" not in session:

        return redirect("/login")

    if request.method == "POST":

        # Check file
        if "resume" not in request.files:

            return "Please select a resume file."

        file = request.files["resume"]

        # Check filename
        if file.filename == "":

            return "Please select a resume file."

        # Check extension
        if not file.filename.lower().endswith(".pdf"):

            return "Only PDF files are allowed."

        # Check file size
        file.seek(0, 2)

        file_size = file.tell()

        file.seek(0)

        if file_size > 5 * 1024 * 1024:

            return "Resume file must be smaller than 5 MB."

        # Secure original filename
        filename = secure_filename(
            file.filename
        )

        if not filename:

            return "Invalid file name."

        # Generate unique filename
        unique_filename = (
            str(uuid.uuid4())
            + "_"
            + filename
        )

        # Upload directory
        os.makedirs(
            "uploads",
            exist_ok=True
        )

        filepath = os.path.join(
            "uploads",
            unique_filename
        )

        # Save file
        file.save(filepath)

        # Extract text
        try:

            resume_text = extract_text_from_pdf(
                filepath
            )

        except Exception:

            return (
                "Unable to read the PDF. "
                "Please upload a valid PDF resume."
            )

        # Check extracted text
        if not resume_text.strip():

            return (
                "The uploaded PDF does not "
                "contain readable text."
            )

        # Save resume information
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO resumes
            (user_id, filename, resume_text)
            VALUES (%s, %s, %s)
            """,
            (
                session["user_id"],
                unique_filename,
                resume_text
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        return redirect("/resume")

    return render_template("upload.html")


# =========================================================
# VIEW RESUME
# =========================================================

@app.route("/resume")
def view_resume():

    if "user_id" not in session:

        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            filename,
            resume_text,
            uploaded_at
        FROM resumes
        WHERE user_id = %s
        ORDER BY uploaded_at DESC
        LIMIT 1
        """,
        (session["user_id"],)
    )

    resume = cursor.fetchone()

    cursor.close()
    connection.close()

    if not resume:

        return "No resume uploaded yet."

    skills = extract_skills(
        resume["resume_text"]
    )

    return render_template(
        "resume.html",
        resume=resume,
        skills=skills
    )


# =========================================================
# SELECT JOB ROLE
# =========================================================

@app.route("/role", methods=["GET", "POST"])
def select_role():

    if "user_id" not in session:

        return redirect("/login")

    if request.method == "POST":

        job_role = request.form["job_role"]

        session["job_role"] = job_role

        return f"""
        <h1>Job Role Selected</h1>

        <p>
            You selected:
            <strong>{job_role}</strong>
        </p>

        <p>
            Your resume and skills are ready
            for interview preparation.
        </p>

        <a href="/dashboard">
            Go to Dashboard
        </a>
        """

    return render_template("role.html")


# =========================================================
# START INTERVIEW
# =========================================================

@app.route("/start_interview")
def start_interview():

    if "user_id" not in session:

        return redirect("/login")

    if "job_role" not in session:

        return redirect("/role")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM resumes
        WHERE user_id = %s
        LIMIT 1
        """,
        (session["user_id"],)
    )

    resume = cursor.fetchone()

    cursor.close()
    connection.close()

    if not resume:

        return redirect("/upload")

    return render_template(
        "interview_start.html",
        job_role=session["job_role"]
    )


# =========================================================
# GENERATE INTERVIEW QUESTIONS
# =========================================================

@app.route("/generate_questions")
def generate_questions():

    if "user_id" not in session:

        return redirect("/login")

    if "job_role" not in session:

        return redirect("/role")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT resume_text
        FROM resumes
        WHERE user_id = %s
        ORDER BY uploaded_at DESC
        LIMIT 1
        """,
        (session["user_id"],)
    )

    resume = cursor.fetchone()

    cursor.close()
    connection.close()

    if not resume:

        return "Please upload your resume first."

    # Extract skills
    skills = extract_skills(
        resume["resume_text"]
    )

    # Generate questions using Gemini
    questions_text = generate_interview_questions(
        session["job_role"],
        skills,
        resume["resume_text"]
    )

    # Parse questions
    questions = []

    for line in questions_text.splitlines():

        line = line.strip()

        if (
            line
            and line[0].isdigit()
            and "." in line
        ):

            question = line.split(
                ".",
                1
            )[1].strip()

            if question:

                questions.append(question)

    # Check whether questions were generated
    if not questions:

        return (
            "Unable to generate interview questions "
            "right now. Please try again."
        )

    # Save questions in session
    session["questions"] = questions

    return render_template(
        "interview.html",
        questions=questions,
        job_role=session["job_role"]
    )


# =========================================================
# SUBMIT INTERVIEW
# =========================================================

@app.route(
    "/submit_interview",
    methods=["POST"]
)
def submit_interview():

    if "user_id" not in session:

        return redirect("/login")

    questions = session.get(
        "questions",
        []
    )

    if not questions:

        return redirect(
            "/generate_questions"
        )

    job_role = session.get(
        "job_role",
        "Unknown"
    )

    results = []

    total_score = 0

    # Evaluate every answer
    for i, question in enumerate(
        questions,
        start=1
    ):

        answer = request.form.get(
            f"answer_{i}",
            ""
        ).strip()

        evaluation = evaluate_answer(
            question,
            answer,
            job_role
        )

        technical_score = evaluation[
            "technical_score"
        ]

        communication_score = evaluation[
            "communication_score"
        ]

        average_score = (
            technical_score
            + communication_score
        ) / 2

        total_score += average_score

        results.append(
            {
                "question": question,
                "answer": answer,
                "technical_score":
                    technical_score,
                "communication_score":
                    communication_score,
                "feedback":
                    evaluation["feedback"]
            }
        )

    # Calculate overall score
    overall_score = (
        total_score / len(results)
    )

    # Save interview
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO interviews
        (user_id, job_role, total_score)
        VALUES (%s, %s, %s)
        """,
        (
            session["user_id"],
            job_role,
            overall_score
        )
    )

    interview_id = cursor.lastrowid

    # Save questions and answers
    for result in results:

        cursor.execute(
            """
            INSERT INTO questions
            (interview_id, question)
            VALUES (%s, %s)
            """,
            (
                interview_id,
                result["question"]
            )
        )

        question_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO answers
            (
                question_id,
                answer,
                technical_score,
                communication_score,
                feedback
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                question_id,
                result["answer"],
                result["technical_score"],
                result["communication_score"],
                result["feedback"]
            )
        )

    connection.commit()

    cursor.close()
    connection.close()

    return render_template(
        "results.html",
        results=results,
        overall_score=overall_score,
        job_role=job_role
    )


# =========================================================
# INTERVIEW HISTORY
# =========================================================

@app.route("/history")
def interview_history():

    if "user_id" not in session:

        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            job_role,
            total_score,
            created_at
        FROM interviews
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (session["user_id"],)
    )

    interviews = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "history.html",
        interviews=interviews
    )


# =========================================================
# INTERVIEW DETAILS
# =========================================================

@app.route(
    "/interview/<int:interview_id>"
)
def interview_detail(interview_id):

    if "user_id" not in session:

        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor()

    # Get interview
    cursor.execute(
        """
        SELECT
            id,
            job_role,
            total_score,
            created_at
        FROM interviews
        WHERE id = %s
        AND user_id = %s
        """,
        (
            interview_id,
            session["user_id"]
        )
    )

    interview = cursor.fetchone()

    if not interview:

        cursor.close()
        connection.close()

        return "Interview not found."

    # Get questions and answers
    cursor.execute(
        """
        SELECT
            q.question,
            a.answer,
            a.technical_score,
            a.communication_score,
            a.feedback
        FROM questions q
        LEFT JOIN answers a
        ON q.id = a.question_id
        WHERE q.interview_id = %s
        ORDER BY q.id
        """,
        (interview_id,)
    )

    results = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "interview_detail.html",
        interview=interview,
        results=results
    )


# =========================================================
# RUN APPLICATION
# =========================================================
# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "404.html"
    ), 404


@app.errorhandler(500)
def internal_server_error(error):

    return render_template(
        "500.html"
    ), 500

if __name__ == "__main__":

    app.run(
        debug=True
    )