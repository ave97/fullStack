from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    url_for,
    jsonify,
    send_file,
    flash,
    abort,
)
import database, random, json
from werkzeug.security import check_password_hash, generate_password_hash
from quiz import Question, Quiz
import os, re, io, csv, zipfile, traceback
from datetime import datetime, timedelta, UTC
from leveling import get_student_level_info
from tts_utils import generate_tts_audio_if_needed, clean_old_audio

from plotly.offline import plot
import plotly.graph_objs as go

app = Flask(__name__)
app.secret_key = os.urandom(24)  # 24 τυχαιοι χαρακτηρες


@app.route("/")
def home():
    if "user" in session:
        return dashboard()
    return render_template("home.html")


@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    userClass = request.form.get("class")
    role = request.form.get("role")

    if not username or not email or not password or not role:
        return render_template(
            "home.html", error="Please fill in all fields!", register=True
        )

    if len(password) < 6:
        return render_template(
            "home.html",
            error="Password must be at least 6 characters long!",
            register=True,
        )

    email_regex = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_regex, email):
        return render_template(
            "home.html", error="Invalid email format!", register=True
        )

    hashed_pass = generate_password_hash(password)

    connection = database.getConnection()
    cursor = connection.cursor()

    # Έλεγχος πρώτα στον users
    cursor.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?", (username, email)
    )
    existing_user = cursor.fetchone()

    if existing_user:
        connection.close()
        return render_template(
            "home.html",
            error="A user with this username or email already exists.",
            register=True,
        )

    # Μετά έλεγχος στο pending_teachers
    cursor.execute(
        "SELECT * FROM pending_teachers WHERE username = ? OR email = ?",
        (username, email),
    )
    existing_pending = cursor.fetchone()

    if existing_pending:
        connection.close()
        return render_template(
            "home.html",
            error="There is already a pending teacher request with this username or email.",
            register=True,
        )

    # Αν όλα καλά, proceed
    if role == "student":
        cursor.execute(
            "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, 'student')",
            (username, email, hashed_pass),
        )
        user_id = cursor.lastrowid
        sid = database.generate_id("student")  # Δημιούργησε SID
        cursor.execute(
            "INSERT INTO students (sid, user_id, class) VALUES (?, ?, ?)",
            (sid, user_id, userClass),
        )
        connection.commit()
        flash("Registration successful!", "success")
    elif role == "teacher":
        cursor.execute(
            "INSERT INTO pending_teachers (username, email, password) VALUES (?, ?, ?)",
            (username, email, hashed_pass),
        )
        connection.commit()
        flash(
            "Your teacher request has been submitted and is pending approval.", "info"
        )

    connection.close()
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = database.selectUser(username)
        if user:
            if check_password_hash(user[3], password):
                session.clear()
                session["user_id"] = user[0]
                session["user"] = user[1]
                session["role"] = user[4]

                if user[4] == "student":
                    unlocked = database.track_progress(user[0], "logins", 1)
                    for title in unlocked:
                        flash(
                            f"Συγχαρητήρια! Ξεκλείδωσες το επίτευγμα: {title}",
                            "success",
                        )

                if user[4] == "admin":
                    return redirect(url_for("admin_dashboard"))
                else:
                    return redirect(url_for("dashboard"))
            else:
                return render_template(
                    "home.html", error="Incorrect email or password.", login=True
                )

        # Αν δεν υπάρχει στον users, έλεγξε αν είναι σε pending_teachers
        pending = database.selectPendingTeacher(username)
        if pending:
            return render_template(
                "home.html",
                error="Your teacher account is pending approval.",
                login=True,
            )

        return render_template("home.html", error="User not found.", login=True)

    return render_template("home.html")


@app.route("/dashboard")
def dashboard():
    if "user" in session:
        userRole = session["role"]
        if userRole == "teacher":
            return redirect(url_for("teacher_dashboard"))
        elif userRole == "student":
            return redirect(url_for("student_dashboard"))
    return redirect(url_for("home"))


@app.route("/teacher/dashboard")
def teacher_dashboard():
    if "user" not in session or session["role"] != "teacher":
        return redirect(url_for("no_access"))

    teacher_username = session["user"]
    teacher = database.getTeacherInfo(teacher_username)
    teacher_id = teacher.getTid()

    # Latest quizzes
    latest_quizzes = database.getLatestQuizzesByTeacher(teacher_id)
    for quiz in latest_quizzes:
        quiz["created_at"] = quiz["created_at"].split(" ")[0]

    # Activity feed
    activity_feed = database.getRecentStudentActivity(teacher_id)  # list of strings

    # Most completed quiz
    top_quizzes = database.getMostCompletedQuizzesOfTeacher(teacher_id)

    # Insights
    insights = {
        "total_students": database.getUniqueStudentsForTeacher(teacher_id),
        "total_quizzes": len(latest_quizzes),
        "avg_score": database.getAverageAccuracyForTeacher(teacher_id),
        "completion_rate": database.getStudentCompletionRateForTeacher(teacher_id),
        "top_quizzes": top_quizzes,
    }

    # Leaderboard
    leaderboard = database.getStudentLeaderboard(teacher_id)
    all_lessons = database.getLessonsForTeacher(teacher_id)

    return render_template(
        "teacher_dashboard.html",
        user=teacher_username,
        current_date=datetime.now().strftime("%d %B %Y"),
        quizzes=latest_quizzes,
        activity_feed=activity_feed,
        insights=insights,
        leaderboard=leaderboard,
        all_lessons=all_lessons,
    )


@app.route("/student/dashboard")
def student_dashboard():
    if "user" not in session or session["role"] != "student":
        return redirect(url_for("no_access"))

    username = session["user"]
    student = database.getStudentInfo(username)

    if student is None:
        return render_template("home.html", error="User not found.", login=True)

    sid = student[0]

    database.cleanExpiredBonuses(sid)

    conn = database.getConnection()
    cursor = conn.cursor()

    # Recent quizzes
    cursor.execute(
        """
            SELECT q.title, r.score, r.completed_at
            FROM quiz_results r
            JOIN quiz q ON q.id = r.quiz_id
            WHERE r.sid = ?
            ORDER BY r.completed_at DESC
            LIMIT 5
        """,
        (sid,),
    )
    recent_quizzes = cursor.fetchall()

    # Quiz-to-do
    cursor.execute("SELECT class FROM students WHERE sid = ?", (sid,))
    student_class = cursor.fetchone()[0]

    # Πάρε όλα τα quiz της τάξης του μαθητή
    cursor.execute(
        """
        SELECT id, title
        FROM quiz
        WHERE target_class = ?
    """,
        (student_class,),
    )
    all_quizzes = cursor.fetchall()

    quizzes_to_do = []

    for quiz_id, title in all_quizzes:
        cursor.execute(
            """
            SELECT COUNT(*), MAX(completed_at)
            FROM quiz_results
            WHERE quiz_id = ? AND sid = ?
        """,
            (quiz_id, sid),
        )

        count, last_date = cursor.fetchone()
        count = count or 0

        # Ελέγχει αν μπορεί να ξαναπαίξει
        if count == 0:
            quizzes_to_do.append((quiz_id, title, count))
        elif count == 1 and last_date:
            last_dt = datetime.strptime(last_date, "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=UTC
            )
            now = datetime.now(UTC)
            hours_passed = (now - last_dt).total_seconds() / 3600
            if hours_passed >= 48:
                quizzes_to_do.append((quiz_id, title, count))

    # Δημιουργεί dictionary για το template
    quizzes = [{"id": q[0], "title": q[1], "attempts": q[2]} for q in quizzes_to_do]

    # Πλήθος κουίζ που έχει παίξει
    cursor.execute("SELECT COUNT(*) FROM quiz_results WHERE sid = ?", (sid,))
    quizzes_played = cursor.fetchone()[0]

    # Συνολικές σωστές και συνολικές ερωτήσεις
    cursor.execute(
        """
        SELECT SUM(correct_answers), SUM(total_questions)
        FROM quiz_results
        WHERE sid = ?
    """,
        (sid,),
    )
    correct, total = cursor.fetchone()
    correct = correct or 0
    total = total or 0
    correct_rate = round((correct / total) * 100, 1) if total > 0 else 0
    insights = {"quizzes_played": quizzes_played, "correct_rate": correct_rate}

    # Γραφή στατιστικών για τα μαθήματα
    cursor.execute(
        """
        SELECT q.lesson, SUM(r.correct_answers), SUM(r.total_questions)
        FROM quiz_results r
        JOIN quiz q ON q.id = r.quiz_id
        WHERE r.sid = ?
        GROUP BY q.lesson
        """,
        (sid,),
    )

    lesson_stats = cursor.fetchall()

    chart_data = []
    for lesson, correct, total in lesson_stats:
        if total > 0:
            rate = round((correct / total) * 100, 1)
            chart_data.append(
                {"label": lesson, "value": rate, "correct": correct, "total": total}
            )

    conn.close()

    all_achievements = database.getUserAchievements(session["user_id"])
    unlocked_achievements = [a for a in all_achievements if a["unlocked"]]

    achievements = unlocked_achievements

    bonuses = database.getActiveBonuses(sid)

    level_info = get_student_level_info(sid)
    level_data = {
        "level": level_info["level"],
        "current_xp": level_info["xp_into_level"],
        "required_xp": level_info["xp_for_next_level"],
        "progress_percent": level_info["progress_percent"],
        "total_xp": level_info["total_xp"],
        "remaining_xp": level_info["xp_for_next_level"] - level_info["xp_into_level"],
    }

    return render_template(
        "student_dashboard.html",
        user=session["user"],
        current_date=datetime.now().strftime("%d %B %Y"),
        level_data=level_data,
        quizzes=quizzes,
        achievements=achievements,
        bonuses=bonuses,
        recent_quizzes=recent_quizzes,
        insights=insights,
        chart_data=chart_data,
    )


@app.route("/daily_spin", methods=["POST"])
def daily_spin():
    if "user" not in session or session["role"] != "student":
        return redirect(url_for("no_access"))

    user = session["user"]
    sid = database.getStudentInfo(user)[0]
    today = datetime.now().date()

    if database.getDailySpins(sid, today):
        has_spun_today = True
        return (
            jsonify(
                {"error": "You already spun today!", "has_spun_today": has_spun_today}
            ),
            403,
        )

    data = request.get_json()
    chosen_index = data.get("chosen_index")

    bonuses = ["⭐ 2x XP", "⭐ 3x XP", "⭐ 5x XP", "🚫 Nothing"]
    selected_bonus = random.choice(bonuses)

    # Αφαίρεσε το επιλεγμένο για να μην το έχεις 2 φορές
    remaining = bonuses[:]
    remaining.remove(selected_bonus)
    random.shuffle(remaining)

    rewards = []
    for i in range(4):
        if i == chosen_index:
            rewards.append(selected_bonus)
        else:
            rewards.append(remaining.pop())

    if selected_bonus != "🚫 Nothing":
        start = datetime.now()
        expires = datetime.now() + timedelta(hours=24)
        database.insertActiveBonus(sid, selected_bonus, start, expires)

    database.insertDailySpins(sid, today, selected_bonus)

    return jsonify(
        {
            "success": True,
            "rewards": rewards,
            "your_bonus": selected_bonus,
            "correct_index": chosen_index,
        }
    )


@app.route("/has_spun_today")
def has_spun_today():
    if "user" not in session or session["role"] != "student":
        return jsonify({"error": "unauthorized"}), 403

    sid = database.getStudentInfo(session["user"])[0]
    today = datetime.now().date()
    spun = database.getDailySpins(sid, today) is not None

    return jsonify({"spun": spun})


@app.route("/account")
def myAccount():
    if "user" not in session:
        return redirect(url_for("login"))

    username = session["user"]
    role = session["role"]
    user = database.selectUser(username)

    if role == "teacher":
        teacher = database.getTeacherInfo(username)
        tid = teacher.getTid()
        quizzes = database.getQuizzesByTeacher(tid)
        total_quizzes = len(quizzes)

        online_user = {
            "username": user[1],
            "id": tid,
            "email": user[2],
            "quiz_count": total_quizzes,
            "full_name": teacher.getUsername(),
            "role": "teacher",
        }

        return render_template(
            "teacher_account.html", user=online_user, quizzes=quizzes
        )

    elif role == "student":
        student = database.getStudentInfo(username)
        sid = student[0]
        userClass = student[1]

        level_info = get_student_level_info(sid)
        level_data = {
            "level": level_info["level"],
            "current_xp": level_info["xp_into_level"],
            "required_xp": level_info["xp_for_next_level"],
            "progress_percent": level_info["progress_percent"],
            "total_xp": level_info["total_xp"],
            "remaining_xp": level_info["xp_for_next_level"]
            - level_info["xp_into_level"],
        }

        online_user = {
            "username": user[1],
            "id": sid,
            "email": user[2],
            "class": userClass,
            "role": "student",
        }

        return render_template(
            "student_account.html",
            user=online_user,
            level_data=level_data,
        )


@app.route("/update_account", methods=["POST"])
def update_account():
    old_username = session["user"]
    new_username = request.form["name"]
    new_email = request.form["email"]
    new_password = request.form["password"]

    user = database.selectUser(old_username)

    if new_password:
        if len(new_password) < 6:
            flash("Password must be at least 6 characters long!", "error")
            return redirect(url_for("myAccount"))
        else:
            hashed_pass = generate_password_hash(new_password)
    else:
        hashed_pass = user[3]

    database.updateUser(old_username, new_username, new_email, hashed_pass)

    session["user"] = new_username
    flash("Changes saved successfully!", "success")

    return redirect(url_for("myAccount"))


@app.route("/create")
def create_quiz():
    if "user" not in session or session["role"] != "teacher":
        return redirect(url_for("no_access"))

    lessons = database.getAllLessons()
    return render_template("create_quiz.html", user=session["user"], lessons=lessons)


@app.route("/create_quiz", methods=["GET", "POST"])
def save_quiz():
    if request.method == "POST":
        if "user" not in session or session["role"] != "teacher":
            return redirect(url_for("no_access"))

        teacher = database.getTeacherInfo(session["user"])

        quizTitle = request.form.get("quizTitle")
        quizLesson = request.form.get("quizLesson")
        quizClass = request.form.get("quizClass")

        # Έλεγχος αν τα πεδία του κουίζ είναι κενά
        if not quizTitle or not quizLesson:
            return render_template(
                "create_quiz.html", error="Quiz title and lesson are required."
            )

        quiz = Quiz(quizTitle, quizLesson)

        try:
            # Εισαγωγή του κουίζ στη βάση
            quiz_id = database.insertQuiz(quiz, teacher, quizClass)

            questionNum = 1
            while f"question_{questionNum}" in request.form:
                questionText = request.form.get(f"question_{questionNum}")
                if not questionText:
                    return render_template(
                        "create_quiz.html",
                        error=f"Question {questionNum} text is required.",
                    )

                questionType = request.form.get(f"questionType_{questionNum}")
                correctAnswer = None

                option1 = None
                option2 = None
                option3 = None
                option4 = None

                # Αποθήκευση για Multiple Choice
                if questionType == "multiple_choice":
                    option1 = request.form.get(f"option_{questionNum}_1")
                    option2 = request.form.get(f"option_{questionNum}_2")
                    option3 = request.form.get(f"option_{questionNum}_3")
                    option4 = request.form.get(f"option_{questionNum}_4")
                    correctAnswer = request.form.get(f"correct_{questionNum}")

                    if not option1 or not option2 or not option3 or not option4:
                        return render_template(
                            "create_quiz.html",
                            error=f"All options for question {questionNum} are required.",
                        )

                    if not correctAnswer:
                        return render_template(
                            "create_quiz.html",
                            error=f"Correct answer for question {questionNum} is required.",
                        )

                # Αποθήκευση για True/False
                elif questionType == "true_false":
                    correctAnswer = request.form.get(f"trueFalseAnswer_{questionNum}")
                    if not correctAnswer:
                        return render_template(
                            "create_quiz.html",
                            error=f"Correct answer for question {questionNum} is required.",
                        )

                # Αποθήκευση για Matching
                elif questionType == "matching":
                    matchingItems = []
                    matchingNum = 1
                    while f"matching_{questionNum}_{matchingNum}" in request.form:
                        matching_item = request.form.get(
                            f"matching_{questionNum}_{matchingNum}"
                        )
                        matchingItems.append(matching_item)
                        matchingNum += 1
                    if len(matchingItems) < 2:
                        return render_template(
                            "create_quiz.html",
                            error=f"Both items for question {questionNum} are required.",
                        )

                # Δημιουργία ερώτησης και αποθήκευση στη βάση
                question = Question(
                    questionNum,
                    questionText,
                    questionType,
                    option1,
                    option2,
                    option3,
                    option4,
                    correctAnswer,
                    matchingItems=matchingItems if questionType == "matching" else None,
                )

                # Εισαγωγή της ερώτησης στη βάση δεδομένων
                database.insertQuestion(quiz_id, question)

                questionNum += 1

            return redirect(url_for("history"))

        except Exception as e:
            print(f"Error while saving the quiz: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return render_template(
                "create_quiz.html",
                error="An error occurred while saving the quiz. Please try again.",
            )

    return render_template("teacher_dashboard.html", user=session["user"])


@app.route("/teacher/student_scores")
def teacher_student_scores():
    if "user" not in session or session["role"] != "teacher":
        return redirect(url_for("no_access"))

    teacher = database.getTeacherInfo(session["user"])
    teacher_id = teacher.getTid()

    quiz_id = request.args.get("quiz_id")
    quiz_title = None

    if quiz_id:
        results = database.getQuizResultsForTeacher(teacher_id, quiz_id=quiz_id)
        quiz_title = database.getQuizTitle(quiz_id)
    else:
        results = database.getQuizResultsForTeacher(teacher_id)

    return render_template(
        "teacher_student_scores.html",
        user=session["user"],
        results=results,
        quiz_title=quiz_title,
        current_date=datetime.now().strftime("%d %B %Y"),
    )


@app.route("/teacher/quiz_summary/<int:quiz_id>/<sid>")
def quiz_summary_detail(quiz_id, sid):
    if "user" not in session or session["role"] != "teacher":
        return redirect(url_for("no_access"))

    # Φόρτωσε δεδομένα για το συγκεκριμένο quiz_result_id
    summary_data = database.get_quiz_summary_extended(sid, quiz_id)
    if not summary_data:
        return "Summary not found", 404

    quiz_title = database.getQuizTitleById(quiz_id)

    return render_template(
        "teacher_quiz_summary.html",
        summary=summary_data,
        quiz_title=quiz_title,
        sid=sid,
    )


@app.route("/history")
def history():
    if "user" not in session or session["role"] != "teacher":
        return redirect(url_for("no_access"))

    teacher = database.getTeacherInfo(session["user"])
    quizzes = database.getQuizzesByTeacher(teacher.getTid())
    lessons = database.getAllLessons()

    return render_template(
        "history.html", user=session["user"], quizzes=quizzes, lessons=lessons
    )


@app.route("/quiz/<int:quiz_id>")
def get_quiz(quiz_id):
    if "user" not in session or session["role"] != "teacher":
        return redirect(url_for("no_access"))

    quiz = database.getQuizById(quiz_id)
    questions = database.getQuestionsBy(quiz_id)

    if not quiz:
        return jsonify({"found": "no", "error": "Quiz not found"}), 404

    quiz_data = {
        "id": quiz["id"],
        "title": quiz["title"],
        "lesson": quiz["lesson"],
        "class": quiz["target_class"],
        "questions": [
            {
                "id": q["id"],
                "question_text": q["question_text"],
                "options": [q["option_1"], q["option_2"], q["option_3"], q["option_4"]],
                "correct_answer": q["correct_answer"],
            }
            for q in questions
        ],
    }

    return jsonify({"success": True, "quiz_data": quiz_data})


@app.route("/view_quiz/<int:quiz_id>")
def view_quiz(quiz_id):
    if "user" not in session or session["role"] != "teacher":
        return redirect(url_for("no_access"))

    quiz = database.getQuizById(quiz_id)
    questions = database.getQuestionsBy(quiz_id)
    lessons = database.getAllLessons()

    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    quiz_data = {
        "id": quiz["id"],
        "title": quiz["title"],
        "lesson": quiz["lesson"],
        "class": quiz["target_class"],
        "questions": [
            {
                "id": q["id"],
                "question_text": q["question_text"],
                "question_type": q["question_type"],
                "options": [q["option_1"], q["option_2"], q["option_3"], q["option_4"]],
                "correct_answer": q["correct_answer"],
                "matching_items": (
                    database.getMatchingItems(q["id"])
                    if q["question_type"] == "matching"
                    else []
                ),
            }
            for q in questions
        ],
    }

    return render_template(
        "view_quiz.html", user=session["user"], quiz=quiz_data, lessons=lessons
    )


@app.route("/delete_quizzes", methods=["POST"])
def delete_quizzes():
    if "user" not in session or session["role"] != "teacher":
        return redirect(url_for("no_access"))

    data = request.get_json()
    quiz_ids = data.get("quiz_ids", [])

    if not quiz_ids:
        return jsonify({"error": "No quizzes selected"}), 400

    try:
        # Κλήση της συνάρτησης για διαγραφή των κουίζ
        database.deleteQuizzes(quiz_ids)
        return jsonify({"success": True, "message": "Quizzes deleted successfully!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/quick_edit_quiz", methods=["POST"])
def quick_edit_quiz():
    if "user" not in session or session["role"] != "teacher":
        return redirect(url_for("no_access"))

    data = request.get_json()

    quiz_id = data.get("quiz_id")
    title = data.get("title")
    lesson = data.get("lesson")
    quizClass = data.get("class")

    if not quiz_id or not title or not lesson:
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    database.quickEditQuiz(quiz_id, title, lesson, quizClass)

    return jsonify({"success": True})


@app.route("/update_quiz/<int:quizId>", methods=["POST"])
def update_quiz(quizId):
    if "user" not in session or session["role"] != "teacher":
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data received"}), 400

    try:
        quiz_title = data.get("quizTitle")
        quiz_lesson = data.get("quizLesson")
        quiz_class = data.get("quizClass")
        questions_data = data.get("questions")

        # 1. Ενημέρωση quiz
        database.updateQuiz(quizId, quiz_title, quiz_lesson, quiz_class)

        # 2. Πάρε όλες τις υπάρχουσες ερωτήσεις του quiz
        existing_questions = database.getQuestionsBy(quizId)
        existing_ids = {str(q["id"]) for q in existing_questions}
        incoming_ids = {
            str(q_data.get("id"))
            for q_data in questions_data.values()
            if q_data.get("id")
        }

        # 3. Βρες ποιες πρέπει να διαγραφούν
        to_delete_ids = existing_ids - incoming_ids
        for qid in to_delete_ids:
            database.deleteQuestionById(qid)

        # 4. Επεξεργασία κάθε ερώτησης από το JSON
        for i, (q_key, q_data) in enumerate(questions_data.items(), start=1):
            q_id = q_data.get("id")
            q_text = q_data.get("question_text")
            q_type = q_data.get("question_type")
            correct = q_data.get("correct_answer")

            option1 = q_data.get(f"option_1")
            option2 = q_data.get("option_2")
            option3 = q_data.get("option_3")
            option4 = q_data.get("option_4")
            matching = q_data.get("matching")

            if q_id:
                # Υπάρχουσα ερώτηση → update
                database.updateQuestion(
                    q_id, q_text, q_type, option1, option2, option3, option4, correct
                )
                if q_type == "matching":
                    database.replaceMatchingPairs(q_id, matching)
            else:
                # Νέα ερώτηση → insert
                question = Question(
                    questionNum=i,
                    questionText=q_text,
                    questionType=q_type,
                    option1=option1,
                    option2=option2,
                    option3=option3,
                    option4=option4,
                    correctAnswer=correct,
                    matchingItems=matching,
                )
                database.insertQuestion(quizId, question)

        return jsonify({"success": True})

    except Exception as e:
        print("Error in update_quiz:", e)
        print(traceback.format_exc())
        return jsonify({"success": False, "error": "Internal server error"}), 500


@app.route("/export_quizzes", methods=["POST"])
def export_quizzes():
    if "user" not in session or session["role"] != "teacher":
        return redirect(url_for("no_access"))

    data = request.get_json()
    quiz_ids = data.get("quiz_ids")
    export_type = data.get("export_type", "quiz")

    if not quiz_ids:
        return "No quizzes selected", 400

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for qid in quiz_ids:
            quiz = database.getQuizById(qid)
            if not quiz:
                continue

            folder = f"quiz_{quiz['id']}/"

            if export_type in ("quiz", "all"):
                questions = database.getQuestionsBy(qid)
                csv_buffer = io.StringIO()
                csv_writer = csv.writer(csv_buffer)
                csv_writer.writerow(
                    [
                        "Quiz ID",
                        "Quiz Title",
                        "Lesson",
                        "Question",
                        "Option 1",
                        "Option 2",
                        "Option 3",
                        "Option 4",
                        "Correct Answer",
                    ]
                )
                for question in questions:
                    csv_writer.writerow(
                        [
                            quiz["id"],
                            quiz["title"],
                            quiz["lesson"],
                            question["question_text"],
                            question["option_1"],
                            question["option_2"],
                            question["option_3"],
                            question["option_4"],
                            question["correct_answer"],
                        ]
                    )
                csv_buffer.seek(0)
                zip_file.writestr(folder + "quiz_questions.csv", csv_buffer.getvalue())

            if export_type in ("answers", "all"):
                results = database.getStudentAnswersByQuiz(qid)
                answers_buffer = io.StringIO()
                answers_writer = csv.writer(answers_buffer)
                answers_writer.writerow(
                    [
                        "Student ID",
                        "Student Name",
                        "Question",
                        "Answer Given",
                        "Correct Answer",
                        "Is Correct",
                        "Submitted At",
                    ]
                )
                for result in results:
                    answers_writer.writerow(
                        [
                            result["student_id"],
                            result["student_name"],
                            result["question_text"],
                            result["answer_given"],
                            result["correct_answer"],
                            "Yes" if result["is_correct"] else "No",
                            result["submitted_at"],
                        ]
                    )
                answers_buffer.seek(0)
                zip_file.writestr(folder + "answers.csv", answers_buffer.getvalue())

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="quizzes_export.zip",
    )


@app.route("/teacher/manage_students", methods=["GET", "POST"])
def manage_students():
    if "user" not in session or session["role"] != "teacher":
        return redirect(url_for("login"))

    tid = database.getTeacherInfo(session["user"]).getTid()

    if request.method == "POST":
        student_id = request.form["student_id"]
        new_class = request.form["class"]
        database.updateStudentClass(student_id, new_class)
        flash("Class updated successfully!", "success")
        return redirect(url_for("manage_students"))

    all_students = database.getAllStudents()

    students_by_class = {
        "A": [],
        "B": [],
        "C": [],
    }

    for s in all_students:
        if s[2] == "A":
            students_by_class["A"].append(s)
        elif s[2] == "B":
            students_by_class["B"].append(s)
        elif s[2] == "C":
            students_by_class["C"].append(s)

    return render_template("manage_students.html", students_by_class=students_by_class)


@app.route("/teacher/student/<sid>/stats", methods=["GET", "POST"])
def student_stats(sid):
    if "user" not in session or session["role"] != "teacher":
        return redirect(url_for("no_access"))

    selected_lesson = request.form.get("lesson") if request.method == "POST" else None
    lessons = database.getAllLessons()

    conn = database.getConnection()
    cursor = conn.cursor()

    query = """
        SELECT q.title, r.score, r.correct_answers, r.total_questions, r.completed_at
        FROM quiz_results r
        JOIN quiz q ON q.id = r.quiz_id
        WHERE r.sid = ?
    """
    params = [sid]

    if selected_lesson:
        query += " AND q.lesson = ?"
        params.append(selected_lesson)

    query += " ORDER BY r.completed_at DESC"
    cursor.execute(query, params)
    results = cursor.fetchall()

    enhanced_results = []

    for r in results:
        correct_answer = r[2]
        total_questions = r[3]
        accuracy = (correct_answer / total_questions) * 100
        final_result = r + (round(accuracy),)
        enhanced_results.append(final_result)

    cursor.execute(
        "SELECT sid, class, xp, total_points FROM students s JOIN users u ON u.id = s.user_id WHERE s.sid = ?",
        (sid,),
    )
    student_info = cursor.fetchone()

    conn.close()
    return render_template(
        "student_stats.html",
        results=enhanced_results,
        student=student_info,
        selected_lesson=selected_lesson,
        lessons=lessons,
    )


@app.route("/teacher/progress", methods=["GET", "POST"])
def teacher_progress():
    if "user" not in session or session["role"] != "teacher":
        return redirect(url_for("no_access"))

    teacher = database.getTeacherInfo(session["user"])
    tid = teacher.getTid()  # ή teacher["id"], ανάλογα τη δομή σου

    conn = database.getConnection()
    cursor = conn.cursor()

    # Φέρνουμε όλα τα κουίζ που έχει δημιουργήσει ο καθηγητής
    cursor.execute(
        "SELECT id, title FROM quiz WHERE created_by = ? ORDER BY title ASC",
        (tid,),
    )
    quizzes = cursor.fetchall()

    selected_quiz_id = request.form.get("quiz_id") if request.method == "POST" else None
    quiz_data = []

    if selected_quiz_id:
        cursor.execute(
            """
            SELECT s.sid, r.score, r.correct_answers, r.total_questions, r.completed_at
            FROM quiz_results r
            JOIN students s ON s.sid = r.sid
            WHERE r.quiz_id = ?
            ORDER BY r.completed_at DESC
            """,
            (selected_quiz_id,),
        )
        quiz_data = cursor.fetchall()

    conn.close()

    return render_template(
        "teacher_progress.html",
        quizzes=quizzes,
        selected_quiz_id=selected_quiz_id,
        quiz_data=quiz_data,
    )


@app.route("/teacher/chart-data")
def teacher_chart_data():
    if "user" not in session or session["role"] != "teacher":
        return redirect(url_for("no_access"))

    teacher = database.getTeacherInfo(session["user"])
    tid = teacher.getTid()

    conn = database.getConnection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT q.lesson, ROUND(AVG(r.score), 2) as avg_score
        FROM quiz q
        JOIN quiz_results r ON r.quiz_id = q.id
        WHERE q.created_by = ?
        GROUP BY q.id
        ORDER BY q.lesson
    """,
        (tid,),
    )
    data = cursor.fetchall()
    conn.close()

    labels = [row[0] for row in data]
    scores = [row[1] for row in data]

    return jsonify({"labels": labels, "data": scores})


@app.route("/play_quiz/<int:quiz_id>")
def play_quiz(quiz_id):
    if "user" not in session or session["role"] != "student":
        return redirect(url_for("no_access"))

    quiz = database.getQuizById(quiz_id)
    questions = database.getQuestionsBy(quiz_id)

    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    quiz_data = {
        "id": quiz["id"],
        "title": quiz["title"],
        "lesson": quiz["lesson"],
        "questions": [],
    }

    for q in questions:
        question_id = q["id"]
        question_text = q["question_text"]

        # Δημιουργία ήχου για την ερώτηση (αν δεν υπάρχει ήδη)
        filename = f"quiz_{quiz_data['id']}_question_{question_id}"
        audio_path = generate_tts_audio_if_needed(question_text, filename)

        question_data = {
            "id": q["id"],
            "question_text": q["question_text"],
            "question_type": q["question_type"],
            "options": [q["option_1"], q["option_2"], q["option_3"], q["option_4"]],
            "correct_answer": q["correct_answer"],
            "audio_url": "/" + audio_path,
        }

        # ➕ μόνο αν είναι matching
        if q["question_type"] == "matching":
            question_data["matching_pairs"] = database.getMatchingItems(q["id"])
            random.shuffle(question_data["matching_pairs"])

        quiz_data["questions"].append(question_data)

    return render_template(
        "play_quiz.html", user=session["user"], quiz=quiz_data, role=session["role"]
    )


@app.route("/quiz_summary_data", methods=["POST"])
def quiz_summary_data():
    if "user" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    data = request.get_json()
    sid = database.getStudentInfo(session["user"])[0]
    quiz_id = data.get("quiz_id")

    score = data["score"]
    correct = data["correct"]
    base_xp = score // 10 + correct * 2

    bonus = database.getNextActiveBonus(sid)
    multiplier = 1
    if bonus:
        if "2x" in bonus:
            multiplier = 2
        elif "3x" in bonus:
            multiplier = 3
        elif "5x" in bonus:
            multiplier = 5

    xp_earned = base_xp * multiplier

    if bonus:
        database.use_bonus(sid, quiz_id)

    connection = database.getConnection()
    cursor = connection.cursor()

    # Ενημέρωση των συνολικών πόντων (total_points)
    cursor.execute("SELECT total_points FROM students WHERE sid = ?", (sid,))
    current_points = cursor.fetchone()[0] or 0
    new_points = current_points + score
    cursor.execute(
        "UPDATE students SET total_points = ? WHERE sid = ?", (new_points, sid)
    )

    # Ενημέρωση XP του μαθητή
    cursor.execute("SELECT xp FROM students WHERE sid = ?", (sid,))
    current_xp = cursor.fetchone()[0]
    new_xp = current_xp + xp_earned
    cursor.execute("UPDATE students SET xp = ? WHERE sid = ?", (new_xp, sid))

    # Υπολογισμός αριθμού spins
    cursor.execute(
        "SELECT COALESCE(MAX(total_spins), 0) + 1 FROM quiz_results WHERE sid = ? AND quiz_id = ?",
        (sid, quiz_id),
    )
    total_spins = cursor.fetchone()[0]

    connection.commit()
    connection.close()

    database.track_progress(session["user_id"], "points")

    # Αποθήκευση αποτελέσματος
    quiz_result_id = database.save_quiz_result(
        sid=sid,
        quiz_id=quiz_id,
        score=score,
        correct=correct,
        total=data["total"],
        xp=xp_earned,
        time_taken=data["totalTime"],
        total_spins=data["total_spins"],
        base_xp=base_xp,
        bonus=bonus if bonus else None,
    )

    # Αποθήκευση απαντήσεων
    for entry in data["answers"]:
        q = entry["question"]
        user_ans = entry["userResponse"]
        if isinstance(user_ans, list):
            user_ans = json.dumps(user_ans)

        database.save_student_answer(
            quiz_result_id=quiz_result_id,
            sid=sid,
            quiz_id=quiz_id,
            question_id=q["id"],
            user_answer=user_ans,
            is_correct=entry["correct"],
        )

    database.track_progress(session["user_id"], "quizzes")

    return "", 204


@app.route("/quiz_summary/<int:quiz_id>")
def quiz_summary(quiz_id):
    if "user" not in session:
        return redirect(url_for("login"))

    sid = database.getStudentInfo(session["user"])[0]
    summary = database.get_quiz_summary(sid, quiz_id)

    if not summary:
        flash("Δεν βρέθηκε σύνοψη για αυτό το quiz", "error")
        return redirect(url_for("dashboard"))

    # Ανάλυση matching απαντήσεων
    for ans in summary["answers"]:
        if isinstance(ans["user_answer"], str) and ans["user_answer"].startswith("["):
            try:
                ans["user_answer"] = json.loads(ans["user_answer"])
            except json.JSONDecodeError:
                ans["user_answer"] = []

    return render_template("quiz_summary.html", summary=summary)


@app.route("/available_quizzes")
def available_quizzes():
    if "user" not in session or session["role"] != "student":
        return redirect(url_for("no_access"))

    sid = database.getStudentInfo(session["user"])[0]
    conn = database.getConnection()
    cursor = conn.cursor()

    cursor.execute("SELECT class FROM students WHERE sid = ?", (sid,))
    student_class = cursor.fetchone()

    # Φέρνουμε όλα τα κουίζ
    cursor.execute(
        "SELECT id, title, lesson FROM quiz WHERE target_class= ?", (student_class)
    )
    all_quizzes = cursor.fetchall()

    quizzes_data = []

    for quiz_id, title, lesson in all_quizzes:
        # Πόσες φορές έχει κάνει ο μαθητής αυτό το quiz;
        cursor.execute(
            "SELECT COUNT(*), MAX(completed_at) FROM quiz_results WHERE quiz_id = ? AND sid = ?",
            (quiz_id, sid),
        )
        count, last_date = cursor.fetchone()
        count = count or 0

        can_play = False
        reason = ""

        if count < 2:
            if last_date is None:
                can_play = True
            else:
                last_dt = datetime.strptime(last_date, "%Y-%m-%d %H:%M:%S")
                last_dt = last_dt.replace(tzinfo=UTC)  # κάνε UTC-aware

                now = datetime.now(UTC)
                hours_passed = (now - last_dt).total_seconds() / 3600
                if hours_passed >= 48:
                    can_play = True
                else:
                    reason = f"Available again in {round(48 - hours_passed)} hours"

        quizzes_data.append(
            {
                "id": quiz_id,
                "title": title,
                "lesson": lesson,
                "attempts": count,
                "can_play": can_play,
                "reason": reason,
            }
        )

    conn.close()

    return render_template("available_quizzes.html", quizzes=quizzes_data)


@app.route("/my_quizzes")
def my_quizzes():
    if "user" not in session:
        return redirect(url_for("login"))

    sid = database.getStudentInfo(session["user"])[0]
    conn = database.getConnection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT q.id, q.title, r.score, r.correct_answers, r.total_questions, r.time_taken, r.xp_earned, r.completed_at
        FROM quiz_results r
        JOIN quiz q ON q.id = r.quiz_id
        WHERE r.sid = ?
        ORDER BY r.completed_at DESC
    """,
        (sid,),
    )
    quizzes = cursor.fetchall()
    conn.close()

    return render_template("my_quizzes.html", quizzes=quizzes)


@app.route("/achievements")
def my_achievements():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    all_achievements = (
        database.getAllAchievements()
    )  # επιστρέφει (id, name, description, type, target, xp)

    user_progress = database.getUserAchievementProgress(user_id)
    # Μορφή: {achievement_id: {"current_value": x, "unlocked": bool, "updated_at": timestamp}}

    achievements = []
    for ach in all_achievements:
        ach_id, name, description, type_, target, xp = ach
        progress = user_progress.get(ach_id)

        achievements.append(
            {
                "name": name,
                "description": description,
                "xp": xp,
                "earned": progress["unlocked"] if progress else False,
                "date_earned": (
                    datetime.strptime(
                        progress["updated_at"], "%Y-%m-%d %H:%M:%S"
                    ).strftime("%Y-%m-%d")
                    if progress and progress["unlocked"]
                    else None
                ),
            }
        )

    return render_template(
        "my_achievements.html", achievements=achievements, user=session["user"]
    )


@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        abort(403)

    connection = database.getConnection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
    student_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'teacher'")
    teacher_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE created_at >= date('now', '-7 days')"
    )
    recent_registrations = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pending_teachers")
    pending_teacher_requests = cursor.fetchone()[0]

    cursor.execute("SELECT id, name FROM lessons")
    rows = cursor.fetchall()
    lessons = [{"id": row[0], "name": row[1]} for row in rows]

    connection.close()

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        student_count=student_count,
        teacher_count=teacher_count,
        recent_registrations=recent_registrations,
        pending_teacher_requests=pending_teacher_requests,
        lessons=lessons,
    )


@app.route("/admin/users")
def admin_users():
    if session.get("role") != "admin":
        abort(403)

    connection = database.getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT id, username, email, role, created_at
        FROM users WHERE role != 'admin'
        ORDER BY created_at DESC
    """
    )
    users = cursor.fetchall()
    connection.close()

    return render_template("admin/users.html", users=users)


@app.route("/admin/delete_user", methods=["POST"])
def delete_user():
    if session.get("role") != "admin":
        abort(403)

    user_id = request.form.get("user_id")
    connection = database.getConnection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    connection.commit()
    connection.close()
    flash("Ο χρήστης διαγράφηκε.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/edit_user_modal", methods=["POST"])
def admin_edit_user_modal():
    if session.get("role") != "admin":
        abort(403)

    user_id = request.form["user_id"]
    new_username = request.form["username"]
    new_email = request.form["email"]
    new_role = request.form["role"]

    connection = database.getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE users
        SET username = ?, email = ?, role = ?
        WHERE id = ?
        """,
        (new_username, new_email, new_role, user_id),
    )
    connection.commit()
    connection.close()

    flash("Ο χρήστης ενημερώθηκε.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/teacher_requests")
def admin_teacher_requests():
    if session.get("role") != "admin":
        abort(403)

    connection = database.getConnection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, username, email, submitted_at
        FROM pending_teachers
        ORDER BY submitted_at DESC
    """
    )
    requests = cursor.fetchall()
    connection.close()

    return render_template("admin/teacher_requests.html", requests=requests)


@app.route("/admin/handle_teacher_request", methods=["POST"])
def handle_teacher_request():
    if session.get("role") != "admin":
        abort(403)

    action = request.form.get("action")
    request_id = request.form.get("request_id")

    connection = database.getConnection()
    cursor = connection.cursor()

    if action == "accept":
        cursor.execute(
            "SELECT username, email, password FROM pending_teachers WHERE id = ?",
            (request_id,),
        )
        user_data = cursor.fetchone()

        if not user_data:
            flash("Request not found.", "error")
            return redirect(url_for("admin_teacher_requests"))

        username, email, hashed_password = user_data

        # Εισαγωγή στον πίνακα users
        cursor.execute(
            "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, 'teacher')",
            (username, email, hashed_password),
        )
        user_id = cursor.lastrowid

        # Δημιουργία μοναδικού teacher ID
        tid = database.generate_id("teacher")

        # Εισαγωγή στον πίνακα teachers
        cursor.execute(
            "INSERT INTO teachers (tid, user_id) VALUES (?, ?)", (tid, user_id)
        )

        # Διαγραφή από pending
        cursor.execute("DELETE FROM pending_teachers WHERE id = ?", (request_id,))
        flash("Teacher approved successfully.", "success")

    elif action == "reject":
        cursor.execute("DELETE FROM pending_teachers WHERE id = ?", (request_id,))
        flash("Teacher request rejected.", "info")

    connection.commit()
    connection.close()
    return redirect(url_for("admin_teacher_requests"))


@app.route("/admin/achievements")
def admin_achievements():
    if session.get("role") != "admin":
        abort(403)

    achievements = database.getAllAchievements()
    return render_template("admin/achievements.html", achievements=achievements)


@app.route("/add_achievement", methods=["POST"])
def add_achievement():
    if session.get("role") != "admin":
        abort(403)

    title = request.form.get("title")
    description = request.form.get("description")
    xp = request.form.get("xp")
    ach_type = request.form.get("type")
    target = request.form.get("target")

    if not title or not description or not xp or not ach_type or not target:
        flash("Please fill in all fields.", "error")
        return redirect(url_for("admin_achievements"))

    try:
        xp = int(xp)
        target = int(target)
        if xp < 1 or target < 1:
            raise ValueError("XP and target must be positive integers.")

        database.insertAchievement(title, description, xp, ach_type, target)
        flash("Achievement added successfully!", "success")

    except ValueError:
        flash("XP and target must be positive whole numbers.", "error")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")

    return redirect(url_for("admin_achievements"))


@app.route("/edit_achievement", methods=["POST"])
def edit_achievement():
    if session.get("role") != "admin":
        abort(403)

    id = request.form["id"]
    title = request.form["title"]
    description = request.form["description"]
    xp = request.form["xp"]
    type_ = request.form["type"]
    target = request.form["target"]

    if not title or not description or not xp or not type_ or not target:
        flash("Please fill in all fields.", "error")
        return redirect(url_for("admin_achievements"))

    try:
        xp = int(xp)
        target = int(target)
        if xp < 1 or target < 1:
            raise ValueError("XP and target must be positive integers.")

        database.update_achievement(id, title, description, xp, type_, target)
        flash("Achievement updated successfully!", "success")

    except ValueError:
        flash("XP and target must be positive whole numbers.", "error")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")

    return redirect(url_for("admin_achievements"))


@app.route("/delete_achievement", methods=["POST"])
def delete_achievement():
    if session.get("role") != "admin":
        abort(403)

    achievement_id = request.form.get("achievement_id")

    if achievement_id:
        database.deleteAchievement(achievement_id)
        flash("Achievement deleted.", "info")

    return redirect(url_for("admin_achievements"))


@app.route("/admin/add_lesson", methods=["POST"])
def admin_add_lesson():
    if "user" not in session or session["role"] != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    lesson_name = data.get("lesson_name")

    if not lesson_name:
        return jsonify({"error": "Missing lesson name"}), 400

    # Προσθήκη στη βάση
    lesson_id = database.addLesson(lesson_name)

    return jsonify({"id": lesson_id, "name": lesson_name})


@app.route("/admin/delete_lesson/<int:lesson_id>", methods=["POST"])
def admin_delete_lesson(lesson_id):
    if "user" not in session or session["role"] != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    database.deleteLesson(lesson_id)
    return jsonify({"success": True})


@app.route("/admin/update_lesson", methods=["POST"])
def admin_update_lesson():
    if session.get("role") != "admin":
        abort(403)

    data = request.get_json()
    lesson_id = data.get("id")
    new_name = data.get("name", "").strip()

    if not new_name:
        return "Missing name", 400

    # Έλεγξε αν υπάρχει ήδη άλλο lesson με το ίδιο όνομα
    existing = database.getLessonByName(new_name)
    if existing and existing["id"] != int(lesson_id):
        return "Name already exists", 409

    database.updateLesson(lesson_id, new_name)
    return "", 200


@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)
    return redirect(url_for("home"))


@app.route("/no_access")
def no_access():
    return render_template("no_access.html")


if __name__ == "__main__":
    clean_old_audio()  # Εκκαθάριση παλιών αρχείων πριν ξεκινήσει ο server
    app.run(debug=True)


# if __name__ == "__main__":
#     import os

#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port)
