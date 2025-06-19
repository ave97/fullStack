import sqlite3, traceback, json
from werkzeug.security import generate_password_hash
from users import Student, Teacher
from quiz import Question, Quiz
from datetime import datetime
from sqlFunctions import getConnection


def selectUser(username):
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    connection.close()
    return user


def getTeacherInfo(username):
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT teachers.tid, users.username, users.email, users.password FROM users JOIN teachers on users.id = teachers.user_id WHERE users.username = ?",
        (username,),
    )
    teacher_data = cursor.fetchone()
    connection.close()

    if teacher_data:
        return Teacher(*teacher_data)
    return None


def getStudentInfo(username):
    try:
        connection = getConnection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT students.sid, students.class FROM users JOIN students on users.id = students.user_id WHERE users.username = ?",
            (username,),
        )
        student_info = cursor.fetchone()
        return student_info
    except sqlite3.Error as error:
        print(f"An error occured in function getStudentInfo: {error}")
    finally:
        connection.close()
    return 0


def insertUser(username, email, password, role):
    try:
        connection = getConnection()
        cursor = connection.cursor()
        hashed_password = password
        cursor.execute(
            "INSERT INTO users (username, email, password, role) VALUES (?,?,?,?)",
            (username, email, hashed_password, role),
        )

        user_id = cursor.lastrowid
        if role == "student":
            sid = generate_id("student")
            cursor.execute(
                "INSERT INTO students (sid, user_id) VALUES (?,?)", (sid, user_id)
            )
        else:
            tid = generate_id("teacher")
            cursor.execute(
                "INSERT INTO teachers (tid, user_id) VALUES (?,?)", (tid, user_id)
            )
        connection.commit()
        print(f"✅ User {username} ({role}) created successfully!")
    except sqlite3.Error as error:
        print(f"An error occured in function insertUser: {error}")
        connection.rollback()
    finally:
        connection.close()

    return


def updateUser(old_username, username, email, password):
    try:
        connection = getConnection()
        cursor = connection.cursor()
        update_query = (
            "UPDATE users SET username = ?, email = ?, password = ? WHERE username = ?;"
        )
        # Εκτέλεση της εντολής με τα δεδομένα που στείλαμε
        cursor.execute(update_query, (username, email, password, old_username))
        connection.commit()
    except sqlite3.Error as error:
        print(f"An error occured in function updateUser: {error}")
        connection.rollback()
    finally:
        connection.close()
    return


def selectPendingTeacher(username):
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM pending_teachers WHERE username = ?", (username,))
    result = cursor.fetchone()
    connection.close()
    return result


def insertPendingTeacher(username, email, password):
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO pending_teachers (username, email, password)
        VALUES (?, ?, ?)
    """,
        (username, email, password),
    )
    connection.commit()
    connection.close()


def approvePendingTeacher(pending_id):
    connection = getConnection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT username, email, password FROM pending_teachers
        WHERE id = ?
    """,
        (pending_id,),
    )
    row = cursor.fetchone()

    if not row:
        connection.close()
        return False

    username, email, password = row

    cursor.execute(
        """
        INSERT INTO users (username, email, password, role)
        VALUES (?, ?, ?, 'teacher')
    """,
        (username, email, password),
    )

    user_id = cursor.lastrowid

    tid = generate_id("teacher")
    cursor.execute(
        """
        INSERT INTO teachers (tid, user_id)
        VALUES (?, ?)
    """,
        (tid, user_id),
    )

    cursor.execute(
        """
        DELETE FROM pending_teachers WHERE id = ?
    """,
        (pending_id,),
    )

    connection.commit()
    connection.close()
    return True


# Στοχος να δημιουργηθει το sid ή tid αναλογα με τον ρολο του χρηστη, π.χ. st2501, αν ο χρηστης ειναι student, γραφτηκε το 2025 και ειναι ο πρωτος στη λιστα που γραφτηκε
def generate_id(role):
    conn = getConnection()
    cursor = conn.cursor()

    year_suffix = datetime.now().year % 100
    prefix = "st" if role == "student" else "te"

    cursor.execute(f"SELECT COUNT(*) FROM {role}s")
    count = cursor.fetchone()[0] + 1

    conn.close()
    return f"{prefix}{year_suffix}{count:02d}"


def insertQuiz(quiz: Quiz, teacher: Teacher, target_class):
    title = quiz.getTitle()
    lesson = quiz.getLesson()

    tid = teacher.getTid()

    try:
        connection = getConnection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO quiz (title, lesson, created_by, target_class) VALUES (?, ?, ?, ?)",
            (title, lesson, tid, target_class),
        )

        quiz_id = cursor.lastrowid  # για να παρουμε το τελευταιο id
        connection.commit()
    except sqlite3.Error as error:
        print(f"An error occured in function insertQuiz: {error}")
        connection.rollback()
    finally:
        connection.close()

    return quiz_id


def insertQuestion(quiz_id, question: Question):
    qNum = question.getQuestionNum()
    qText = question.getQuestionText()
    print(f"Here is again the qTxt inside insertQuestion: {qText}")
    qType = question.getQuestionType()

    print(f"QType is {qType}")
    # Getting the options (for multiple choice questions)
    if qType == "multiple_choice":
        options = question.getOptions()
        option1 = options.get("option1")
        option2 = options.get("option2")
        option3 = options.get("option3")
        option4 = options.get("option4")
    else:
        option1 = None
        option2 = None
        option3 = None
        option4 = None

    # Get the correct answer for all question types
    correctAnswer = question.getCorrectAnswer()

    print(f"Correct answer is {correctAnswer}")

    # For matching questions, get the matching items if available
    matchingItems = question.getMatchingItems() if qType == "matching" else None

    try:
        conn = getConnection()
        cursor = conn.cursor()

        # Debugging output for all the parameters
        print(
            f"DEBUG: quiz_id={quiz_id}, qNum={qNum}, qText={qText}, qType={qType}, "
            f"option1={option1}, option2={option2}, option3={option3}, option4={option4}, "
            f"correctAnswer={correctAnswer}, matchingItems={matchingItems}"
        )

        # If it's a matching question, don't insert a correct answer (set it to NULL)
        if qType == "matching":
            correctAnswer = None

        # Insert the question into the database
        cursor.execute(
            """
            INSERT INTO questions (quiz_id, question_num, question_text, question_type, option_1, option_2, option_3, option_4, correct_answer)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                quiz_id,
                qNum,
                qText,
                qType,
                option1,
                option2,
                option3,
                option4,
                correctAnswer,
            ),
        )

        question_id = cursor.lastrowid
        conn.commit()

        if qType == "matching" and matchingItems:
            print(f"DEBUG: Inserting matching items for question_id {question_id}")
            for i in range(0, len(matchingItems), 2):
                print(
                    f"DEBUG: Matching items: {matchingItems[i]}, {matchingItems[i + 1]}"
                )
                item_1 = matchingItems[i]
                item_2 = matchingItems[i + 1]
                cursor.execute(
                    "INSERT INTO matching (question_id, item_1, item_2) VALUES (?, ?, ?)",
                    (question_id, item_1, item_2),
                )
            conn.commit()

    except sqlite3.Error as error:
        print(f"An error occurred in function insertQuestion: {error}")
        print(f"Traceback: {traceback.format_exc()}")
        conn.rollback()
    finally:
        conn.close()


def getQuizById(quiz_id):
    connection = sqlite3.connect("eduplay.db")
    connection.row_factory = (
        sqlite3.Row
    )  # Μετατρέπει τα αποτελέσματα σε dictionary-like αντικείμενα
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM quiz WHERE id = ?", (quiz_id,))
    quiz = cursor.fetchone()
    connection.close()

    return dict(quiz) if quiz else None  # Μετατρέπει σε dictionary αν υπάρχει


def getQuizByTitle(quiz_title):
    connection = getConnection()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM quiz WHERE title = ?", ((quiz_title,)))
    quiz = cursor.fetchall()
    connection.close()
    return quiz


def getQuizTitle(quiz_id):
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute("SELECT title FROM quiz WHERE id = ?", (quiz_id,))
    row = cursor.fetchone()
    connection.close()
    return row[0] if row else None


# get quizzes created by teacher id
def getQuizzesByTeacher(tid):
    connection = getConnection()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT quiz.id, quiz.title, quiz.lesson, quiz.target_class, quiz.created_at, COUNT(questions.id) as numOfQuestions 
        FROM quiz 
        LEFT JOIN questions ON quiz.id = questions.quiz_id 
        WHERE quiz.created_by = ? 
        GROUP BY quiz.id
        """,
        (tid,),
    )

    quizzes = cursor.fetchall()
    connection.close()

    return [dict(quiz) for quiz in quizzes]  # Μετατροπή κάθε Row σε dictionary


def getLatestQuizzesByTeacher(tid, limit=5):
    query = """
        SELECT 
            q.id,
            q.title,
            q.lesson,
            q.target_class,
            q.created_at,
            COUNT(qr.id) AS completions,
            qr.correct_answers,
            qr.total_questions
        FROM quiz q
        LEFT JOIN quiz_results qr ON q.id = qr.quiz_id
        WHERE q.created_by = ?
        GROUP BY q.id
        ORDER BY q.created_at DESC
        LIMIT ?
    """
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(query, (tid, limit))
    rows = cursor.fetchall()
    connection.close()

    quizzes = []
    for row in rows:
        correct = row[6]
        total = row[7]

        if correct is not None and total not in (None, 0):
            accuracy_rate = round(correct / total * 100, 2)
        else:
            accuracy_rate = None

        quizzes.append(
            {
                "id": row[0],
                "title": row[1],
                "lesson": row[2],
                "class": row[3],
                "created_at": row[4].split(" ")[0],
                "completed_count": row[5],
                "accuracy_rate": accuracy_rate,
            }
        )

    return quizzes


# get quizzes by quiz_id
def getQuestionsBy(quiz_id):
    connection = getConnection()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM questions WHERE quiz_id = ?", ((quiz_id,)))
    questions = cursor.fetchall()
    connection.close()
    return [dict(q) for q in questions]


def deleteQuizzes(quiz_ids):
    try:
        connection = getConnection()
        cursor = connection.cursor()

        placeholders = ",".join("?" for _ in quiz_ids)
        cursor.execute(f"DELETE FROM quiz WHERE id IN ({placeholders})", quiz_ids)
        connection.commit()

    except sqlite3.Error as error:
        print(f"An error occurred in function deleteQuizzes: {error}")
        connection.rollback()
    finally:
        connection.close()
    return


def deleteQuestionById(question_id):
    conn = getConnection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        conn.commit()
    except Exception as e:
        print("Error deleting question:", e)
        conn.rollback()
    finally:
        conn.close()


def quickEditQuiz(quiz_id, title, lesson, target_class=None):
    try:
        connection = getConnection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE quiz SET title = ?, lesson = ?, target_class = ? WHERE id = ?",
            (title, lesson, target_class, quiz_id),
        )
        connection.commit()
        print("Quiz updated successfully!")
    except sqlite3.Error as error:
        print(f"An error occured: {error}")
    finally:
        connection.close()
    return


# Get all quizzes created by a specific teacher or all quizzes
def getAllQuizzes(tid=None):
    try:
        connection = getConnection()
        cursor = connection.cursor()

        if tid:
            # Quiz count μόνο για τον συγκεκριμένο καθηγητή
            cursor.execute(
                """
                SELECT * FROM quiz
                WHERE created_by = ?
                """,
                (tid,),
            )
        else:
            # Συνολικός αριθμός quiz (όλων των καθηγητών)
            cursor.execute("SELECT * FROM quiz")

        result = cursor.fetchall()
        return result

    except sqlite3.Error as error:
        print(f"An error occurred: {error}")
        return 0
    finally:
        connection.close()


# Get matching items for a specific question
def getMatchingItems(question_id):
    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT item_1, item_2 FROM matching WHERE question_id = ?", (question_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    # επιστρέφει [{item_1: ..., item_2: ...}, ...]
    return [{"item_1": row[0], "item_2": row[1]} for row in rows]


# Update Quiz function
def updateQuiz(quiz_id, title, lesson, target_class):
    conn = getConnection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE quiz
            SET title = ?, lesson = ?, target_class = ?
            WHERE id = ?
        """,
            (title, lesson, target_class, quiz_id),
        )
        conn.commit()
    except Exception as e:
        print("Error updating quiz:", e)
        conn.rollback()
        raise
    finally:
        conn.close()


# Update Question function
def updateQuestion(
    question_id,
    text,
    qtype,
    option1=None,
    option2=None,
    option3=None,
    option4=None,
    correctAnswer=None,
):

    print(
        f"Updating question {question_id} with text: {text}, type: {qtype}, options: {option1}, {option2}, {option3}, {option4}, correct answer: {correctAnswer}"
    )
    conn = getConnection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE questions
            SET question_text = ?, question_type = ?, option_1 = ?, option_2 = ?, option_3 = ?, option_4 = ?, correct_answer = ?
            WHERE id = ?
        """,
            (
                text,
                qtype,
                option1,
                option2,
                option3,
                option4,
                correctAnswer,
                question_id,
            ),
        )
        conn.commit()
    except Exception as e:
        print("Error updating question:", e)
        conn.rollback()
        raise
    finally:
        conn.close()


# Update Matching function
def replaceMatchingPairs(question_id, matching_items):
    conn = getConnection()
    cursor = conn.cursor()
    try:
        # Διαγραφή παλιών
        cursor.execute("DELETE FROM matching WHERE question_id = ?", (question_id,))

        # Προσθήκη νέων (ανα 2)
        for i in range(0, len(matching_items), 2):
            item_1 = matching_items[i]
            item_2 = matching_items[i + 1]
            cursor.execute(
                """
                INSERT INTO matching (question_id, item_1, item_2)
                VALUES (?, ?, ?)
            """,
                (question_id, item_1, item_2),
            )

        conn.commit()
    except Exception as e:
        print("Error replacing matching pairs:", e)
        conn.rollback()
        raise
    finally:
        conn.close()


def getAllStudents():
    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT s.sid, u.username, s.class
        FROM students s
        JOIN users u ON s.user_id = u.id
    """
    )
    result = cursor.fetchall()
    conn.close()
    return result


def updateStudentClass(student_id, new_class):
    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE students SET class = ? WHERE sid = ?", (new_class, student_id)
    )
    conn.commit()
    conn.close()


def getStudentsByTeacher(teacher_id):
    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT s.id, u.username, s.class
        FROM students s
        JOIN users u ON s.user_id = u.id
        JOIN teacher_students ts ON ts.sid = s.id
        WHERE ts.tid = ?
    """,
        (teacher_id,),
    )
    students = cursor.fetchall()
    conn.close()
    return students


def getUnassignedStudents():
    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT s.id, u.username, s.class
        FROM students s
        JOIN users u ON s.user_id = u.id
        LEFT JOIN teacher_students ts ON ts.sid = s.id
        WHERE ts.sid IS NULL
    """
    )
    result = cursor.fetchall()
    conn.close()
    return result


# Save quiz result
def save_quiz_result(
    sid,
    quiz_id,
    score,
    correct,
    total,
    xp,
    time_taken,
    total_spins,
    base_xp,
    bonus=None,
):
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO quiz_results (sid, quiz_id, score, correct_answers, total_questions, xp_earned, time_taken, total_spins, bonus, base_xp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            sid,
            quiz_id,
            score,
            correct,
            total,
            xp,
            time_taken,
            total_spins,
            bonus,
            base_xp,
        ),
    )
    quiz_result_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return quiz_result_id


# Save student answers
def save_student_answer(
    quiz_result_id, sid, quiz_id, question_id, user_answer, is_correct
):
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO student_answers (quiz_result_id, sid, quiz_id, question_id, user_answer, is_correct)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (quiz_result_id, sid, quiz_id, question_id, user_answer, is_correct),
    )
    connection.commit()
    connection.close()


# Get quiz summary for a specific student and quiz
def get_quiz_summary(sid, quiz_id):
    connection = getConnection()
    cursor = connection.cursor()

    # Το πιο πρόσφατο αποτέλεσμα και το ID του
    cursor.execute(
        """
            SELECT id, score, correct_answers, total_questions, xp_earned, time_taken, completed_at, total_spins, bonus, base_xp
            FROM quiz_results
            WHERE sid = ? AND quiz_id = ?
            ORDER BY completed_at DESC
            LIMIT 1
        """,
        (sid, quiz_id),
    )
    result = cursor.fetchone()

    if not result:
        connection.close()
        return None

    (
        quiz_result_id,
        score,
        correct,
        total,
        xp,
        time_taken,
        completed_at,
        total_spins,
        bonus,
        base_xp,
    ) = result

    # Απαντήσεις ΜΟΝΟ για αυτό το attempt
    cursor.execute(
        """
            SELECT sa.question_id, sa.user_answer, sa.is_correct, q.question_text, q.question_type
            FROM student_answers sa
            JOIN questions q ON sa.question_id = q.id
            WHERE sa.quiz_result_id = ?
        """,
        (quiz_result_id,),
    )

    answers = cursor.fetchall()

    connection.close()

    return {
        "score": score,
        "correct": correct,
        "total": total,
        "xp": xp,
        "time_taken": time_taken,
        "completed_at": completed_at,
        "total_spins": total_spins,
        "answers": [
            {
                "question_id": a[0],
                "user_answer": json.loads(a[1]) if a[4] == "matching" else a[1],
                "is_correct": bool(a[2]),
                "question_text": a[3],
                "question_type": a[4],
            }
            for a in answers
        ],
        "bonus": bonus,
        "base_xp": base_xp,
    }


def get_quiz_summary_extended(sid, quiz_id):
    connection = getConnection()
    cursor = connection.cursor()

    # Πάρε το πιο πρόσφατο αποτέλεσμα κλπ
    cursor.execute(
        """
            SELECT id, score, correct_answers, total_questions, xp_earned, time_taken, completed_at, total_spins
            FROM quiz_results
            WHERE sid = ? AND quiz_id = ?
            ORDER BY completed_at DESC
            LIMIT 1
        """,
        (sid, quiz_id),
    )
    result = cursor.fetchone()
    if not result:
        connection.close()
        return None

    quiz_result_id, score, correct, total, xp, time_taken, completed_at, total_spins = (
        result
    )

    # Φόρτωσε απαντήσεις με τις επιλογές και σωστή απάντηση
    cursor.execute(
        """
            SELECT sa.question_id, sa.user_answer, sa.is_correct, q.question_text, q.question_type,
                   q.option_1, q.option_2, q.option_3, q.option_4, q.correct_answer
            FROM student_answers sa
            JOIN questions q ON sa.question_id = q.id
            WHERE sa.quiz_result_id = ?
        """,
        (quiz_result_id,),
    )
    answers = cursor.fetchall()

    # Φόρτωσε σωστά ζευγάρια για matching ερωτήσεις
    cursor.execute(
        """
            SELECT question_id, item_1, item_2
            FROM matching
            WHERE question_id IN (
                SELECT question_id FROM student_answers WHERE quiz_result_id = ?
            )
        """,
        (quiz_result_id,),
    )
    matching_pairs_raw = cursor.fetchall()

    # Οργάνωση matching ζευγαριών ανά question_id
    matching_pairs = {}
    for question_id, item_1, item_2 in matching_pairs_raw:
        matching_pairs.setdefault(question_id, []).append(
            {"item_1": item_1, "item_2": item_2}
        )

    connection.close()

    answer_list = []
    for a in answers:
        correct_pos = a[9]
        correct_text = None
        if a[4] == "matching":
            correct_text = matching_pairs.get(a[0], [])
        else:
            options = [a[5], a[6], a[7], a[8]]
            try:
                correct_pos_int = int(correct_pos)
            except (ValueError, TypeError):
                correct_pos_int = None

            if correct_pos_int is not None and 1 <= correct_pos_int <= 4:
                correct_text = options[correct_pos_int - 1]
            else:
                correct_text = None

        user_answer = json.loads(a[1]) if a[4] == "matching" else a[1]

        answer_list.append(
            {
                "question_id": a[0],
                "user_answer": user_answer,
                "is_correct": bool(a[2]),
                "question_text": a[3],
                "question_type": a[4],
                "correct_answer": correct_text,
            }
        )

    return {
        "score": score,
        "correct": correct,
        "total": total,
        "xp": xp,
        "time_taken": time_taken,
        "completed_at": completed_at,
        "total_spins": total_spins,
        "answers": answer_list,
    }


def getQuizTitleById(quiz_id):
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute("SELECT title FROM quiz WHERE id = ?", (quiz_id,))
    result = cursor.fetchone()
    connection.close()

    if result:
        return result[0]
    return None


# Daily Spins
def getDailySpins(sid, date):
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT * FROM daily_spin WHERE sid = ? AND spin_date = ?
        """,
        (sid, date),
    )
    result = cursor.fetchone()
    connection.close()
    return result


# Insert Daily Spins
def insertDailySpins(sid, date, bonus):
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO daily_spin (sid, spin_date, bonus) VALUES (?, ?, ?)
        """,
        (sid, date, bonus),
    )
    connection.commit()
    connection.close()


# Active Bonus
def insertActiveBonus(sid, bonus, starts_at, expires_at):
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO active_bonus (sid, bonus, start_date, end_date) VALUES (?, ?, ?, ?)
        """,
        (sid, bonus, starts_at, expires_at),
    )
    connection.commit()
    connection.close()


# Get Active Bonus
def getActiveBonuses(sid):
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT bonus, end_date FROM active_bonus
        WHERE sid = ? AND end_date > CURRENT_TIMESTAMP AND used = 0
        ORDER BY end_date ASC
        """,
        (sid,),
    )
    results = cursor.fetchall()
    connection.close()

    bonuses = []
    for bonus_type, expires in results:
        expires_dt = datetime.fromisoformat(expires)
        formatted = expires_dt.strftime("%d/%m/%Y %H:%M")
        bonuses.append({"bonus": bonus_type, "expires": formatted})
    return bonuses


def cleanExpiredBonuses(sid):
    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM active_bonus
        WHERE sid = ? AND used = 0 AND end_date < datetime('now')
    """,
        (sid,),
    )
    conn.commit()
    conn.close()


def use_bonus(sid, quiz_id):
    conn = getConnection()
    cursor = conn.cursor()

    # Βρες το πιο παλιό ενεργό και μη χρησιμοποιημένο bonus
    cursor.execute(
        """
        SELECT id FROM active_bonus
        WHERE sid = ? AND used = 0 AND end_date > datetime('now')
        ORDER BY end_date ASC
        LIMIT 1
        """,
        (sid,),
    )
    row = cursor.fetchone()

    if row:
        bonus_id = row[0]
        cursor.execute(
            """
            UPDATE active_bonus
            SET used = 1,
                used_for_qid = ?
            WHERE id = ?
            """,
            (quiz_id, bonus_id),
        )
        conn.commit()

    conn.close()


def getNextActiveBonus(sid):
    connection = getConnection()
    cursor = connection.cursor()
    now = datetime.now()

    cursor.execute(
        """
        SELECT id, bonus FROM active_bonus
        WHERE sid = ? AND end_date > ? AND used = 0
        ORDER BY end_date ASC
        LIMIT 1
    """,
        (sid, now),
    )
    result = cursor.fetchone()

    connection.close()

    if result:
        return result[1]
    return None


def insertAchievement(title, description, xp, ach_type, target):
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO achievements (name, description, xp, type, target)
        VALUES (?, ?, ?, ?, ?)
        """,
        (title, description, xp, ach_type, target),
    )
    connection.commit()
    connection.close()


def getAllAchievements():
    connection = getConnection()
    cursor = connection.cursor()

    cursor.execute("SELECT id, name, description, type, target, xp FROM achievements")
    achievements = cursor.fetchall()

    connection.close()
    return achievements


def deleteAchievement(achievement_id):
    connection = getConnection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM achievements WHERE id = ?", (achievement_id,))

    connection.commit()
    connection.close()


def update_achievement(id, title, description, xp, type_, target):
    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE achievements
        SET name = ?, description = ?, xp = ?, type = ?, target = ?
        WHERE id = ?
    """,
        (title, description, xp, type_, target, id),
    )
    conn.commit()
    conn.close()


def get_recently_unlocked_achievements(user_id):
    connection = getConnection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT a.title
        FROM achievements a
        JOIN user_achievement_progress uap ON a.id = uap.achievement_id
        WHERE uap.user_id = ? AND uap.unlocked = 1
              AND DATE(uap.updated_at) = DATE('now')
        ORDER BY uap.updated_at DESC
    """,
        (user_id,),
    )

    result = [row[0] for row in cursor.fetchall()]
    connection.close()
    return result


def getUserAchievements(user_id):
    conn = getConnection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT a.name, a.description, a.xp, a.type, a.target,
               u.current_value, u.unlocked, u.updated_at
        FROM achievements a
        JOIN user_achievement_progress u ON u.achievement_id = a.id
        WHERE u.user_id = ?
    """,
        (user_id,),
    )

    data = cursor.fetchall()
    conn.close()

    # Optional: mapping σε dict
    achievements = []
    for row in data:
        achievements.append(
            {
                "name": row[0],
                "description": row[1],
                "xp": row[2],
                "type": row[3],
                "target": row[4],
                "progress": row[5],
                "unlocked": row[6],
                "updated_at": row[7],
            }
        )

    return achievements


def track_progress(user_id, achievement_type, amount=1):
    conn = getConnection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, target, xp
        FROM achievements
        WHERE type = ?
        """,
        (achievement_type,),
    )
    achievements = cursor.fetchall()

    unlocked_titles = []

    for achievement_id, title, target, xp_reward in achievements:
        cursor.execute(
            """
            SELECT current_value, unlocked
            FROM user_achievement_progress
            WHERE user_id = ? AND achievement_id = ?
            """,
            (user_id, achievement_id),
        )
        result = cursor.fetchone()

        if result:
            current_value, unlocked = result
            if unlocked:
                continue

            new_value = current_value + amount
            if new_value >= target:
                cursor.execute(
                    """
                    UPDATE user_achievement_progress
                    SET current_value = ?, unlocked = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND achievement_id = ?
                    """,
                    (new_value, user_id, achievement_id),
                )
                # ➕ Πρόσθεσε XP
                cursor.execute(
                    """
                    UPDATE students
                    SET xp = xp + ?
                    WHERE user_id = ?
                    """,
                    (xp_reward, user_id),
                )
                unlocked_titles.append(title)
            else:
                cursor.execute(
                    """
                    UPDATE user_achievement_progress
                    SET current_value = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND achievement_id = ?
                    """,
                    (new_value, user_id, achievement_id),
                )
        else:
            is_unlocked = 1 if amount >= target else 0
            cursor.execute(
                """
                INSERT INTO user_achievement_progress
                (user_id, achievement_id, current_value, unlocked)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, achievement_id, amount, is_unlocked),
            )

            if is_unlocked:
                # ➕ Πρόσθεσε XP
                cursor.execute(
                    """
                    UPDATE students
                    SET xp = xp + ?
                    WHERE user_id = ?
                    """,
                    (xp_reward, user_id),
                )
                unlocked_titles.append(title)

    conn.commit()
    conn.close()

    return unlocked_titles


def getUserAchievementProgress(user_id):
    conn = getConnection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT achievement_id, current_value, unlocked, updated_at
        FROM user_achievement_progress
        WHERE user_id = ?
    """,
        (user_id,),
    )

    rows = cursor.fetchall()
    conn.close()

    progress_map = {}
    for row in rows:
        progress_map[row[0]] = {
            "current_value": row[1],
            "unlocked": row[2],
            "updated_at": row[3],
        }

    return progress_map


def getUniqueStudentsForTeacher(tid):
    query = """
        SELECT COUNT(DISTINCT qr.sid)
        FROM quiz_results qr
        JOIN quiz q ON qr.quiz_id = q.id
        WHERE q.created_by = ?
    """
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(query, (tid,))
    result = cursor.fetchone()[0]
    connection.close()
    return result or 0


def getAverageAccuracyForTeacher(tid):
    query = """
        SELECT AVG(CAST(qr.correct_answers AS FLOAT) / qr.total_questions) * 100
        FROM quiz_results qr
        JOIN quiz q ON qr.quiz_id = q.id
        WHERE q.created_by = ?
    """
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(query, (tid,))
    avg = cursor.fetchone()[0]
    connection.close()
    return round(avg, 2) if avg else 0


def getStudentCompletionRateForTeacher(tid):
    connection = getConnection()
    cursor = connection.cursor()

    # Πάρε τις μοναδικές τάξεις στις οποίες έχει δημιουργήσει quiz ο καθηγητής
    cursor.execute(
        """
        SELECT DISTINCT target_class
        FROM quiz
        WHERE created_by = ?
    """,
        (tid,),
    )
    classes = [row[0] for row in cursor.fetchall()]

    if not classes:
        connection.close()
        return 0

    # Υπολόγισε πόσοι μαθητές υπάρχουν συνολικά σε αυτές τις τάξεις
    cursor.execute(
        f"""
        SELECT COUNT(*)
        FROM students
        WHERE class IN ({','.join(['?'] * len(classes))})
    """,
        classes,
    )
    total_students = cursor.fetchone()[0]

    # Υπολόγισε πόσοι από αυτούς έχουν συμπληρώσει τουλάχιστον ένα quiz του καθηγητή
    cursor.execute(
        f"""
        SELECT COUNT(DISTINCT qr.sid)
        FROM quiz_results qr
        JOIN quiz q ON qr.quiz_id = q.id
        JOIN students s ON s.sid = qr.sid
        WHERE q.created_by = ? AND s.class IN ({','.join(['?'] * len(classes))})
    """,
        [tid] + classes,
    )
    completed_students = cursor.fetchone()[0]

    connection.close()

    if total_students == 0:
        return 0
    return round((completed_students / total_students) * 100)


def getCompletionRateForTeacher(tid):
    connection = getConnection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM quiz WHERE created_by = ?", (tid,))
    total_quizzes = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(DISTINCT qr.quiz_id)
        FROM quiz_results qr
        JOIN quiz q ON qr.quiz_id = q.id
        WHERE q.created_by = ?
    """,
        (tid,),
    )
    completed = cursor.fetchone()[0]

    connection.close()

    if total_quizzes == 0:
        return 0
    return round((completed / total_quizzes) * 100)


def getChartDataForTeacher(tid):
    query = """
        SELECT q.title, AVG(qr.score) AS avg_score
        FROM quiz_results qr
        JOIN quiz q ON qr.quiz_id = q.id
        WHERE q.created_by = ?
        GROUP BY q.id
        ORDER BY q.created_at DESC
        LIMIT 5
    """
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(query, (tid,))
    rows = cursor.fetchall()
    connection.close()

    labels = [row[0] for row in rows]
    scores = [round(row[1], 2) if row[1] else 0 for row in rows]
    return {"labels": labels, "scores": scores}


def getMostCompletedQuizzesOfTeacher(tid, limit=3):
    query = """
        SELECT q.id, q.title, COUNT(qr.id) as count
        FROM quiz q
        LEFT JOIN quiz_results qr ON q.id = qr.quiz_id
        WHERE q.created_by = ?
        GROUP BY q.id        
        ORDER BY count DESC
        LIMIT ?
    """
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(query, (tid, limit))
    rows = cursor.fetchall()
    connection.close()

    return [{"id": row[0], "title": row[1], "count": row[2]} for row in rows]


def getRecentStudentActivity(tid, limit=5):
    query = """
        SELECT qr.sid, q.title, qr.correct_answers, qr.total_questions, q.id
        FROM quiz_results qr
        JOIN quiz q ON qr.quiz_id = q.id
        WHERE q.created_by = ?
        ORDER BY qr.completed_at DESC
        LIMIT ?
    """
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(query, (tid, limit))
    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "sid": row[0],
            "quiz_title": row[1],
            "correct_asnwers": row[2],
            "total_questions": row[3],
            "quiz_id": row[4],
            "message": f'Student {row[0]} completed "{row[1]}" ({(row[2]/row[3])*100:.2f} %)',
        }
        for row in rows
    ]


def getStudentLeaderboard(tid, limit=5):
    connection = getConnection()
    cursor = connection.cursor()

    # Get top students based on total_points
    cursor.execute(
        """
        SELECT s.sid, u.username, s.class, s.total_points
        FROM students s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.total_points DESC
        LIMIT ?
        """,
        (limit,),
    )
    students = cursor.fetchall()

    leaderboard = []

    for sid, username, sclass, points in students:
        # Get per-lesson accuracy (only for quizzes by this teacher)
        cursor.execute(
            """
            SELECT q.lesson,
                   SUM(qr.correct_answers) * 1.0 / SUM(qr.total_questions) * 100 AS accuracy
            FROM quiz_results qr
            JOIN quiz q ON q.id = qr.quiz_id
            WHERE qr.sid = ? AND q.created_by = ?
            GROUP BY q.lesson
            """,
            (sid, tid),
        )
        results = cursor.fetchall()
        lesson_accuracies = {row[0]: round(row[1], 1) for row in results}

        # Calculate overall average accuracy
        if results:
            avg_accuracy = round(sum(row[1] for row in results) / len(results), 2)
        else:
            avg_accuracy = "—"  # or 0 if you prefer

        leaderboard.append(
            {
                "sid": sid,
                "username": username,
                "class": sclass,
                "points": points,
                "lesson_accuracies": lesson_accuracies,
                "avg_accuracy": avg_accuracy,
            }
        )

    connection.close()
    return leaderboard


def getLessonsForTeacher(tid):
    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT DISTINCT lesson
        FROM quiz
        WHERE created_by = ?
        ORDER BY lesson
    """,
        (tid,),
    )
    lessons = [row[0] for row in cursor.fetchall()]
    conn.close()
    return lessons


def getQuizResultsForTeacher(tid, quiz_id=None):
    connection = getConnection()
    cursor = connection.cursor()

    query = """
        SELECT qr.id, u.username, q.title, qr.correct_answers, qr.total_questions, qr.completed_at, s.sid, q.id
        FROM quiz_results qr
        JOIN quiz q ON qr.quiz_id = q.id
        JOIN students s ON qr.sid = s.sid
        JOIN users u ON s.user_id = u.id
        WHERE q.created_by = ?
    """

    params = [tid]

    if quiz_id:
        query += " AND q.id = ?"
        params.append(quiz_id)

    query += " ORDER BY qr.completed_at DESC LIMIT 50"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    connection.close()

    results = []
    for row in rows:
        accuracy_rate = (row[3] / row[4]) * 100
        results.append(
            {
                "result_id": row[0],
                "username": row[1],
                "quiz_title": row[2],
                "accuracy_rate": accuracy_rate,
                "completed_at": row[5].split(" ")[0] if row[5] else "",
                "sid": row[6],
                "quiz_id": row[7],
            }
        )
    return results


def getStudentAnswersByQuiz(quiz_id):
    connection = getConnection()
    cursor = connection.cursor()

    query = """
        SELECT 
            u.username AS student_name,
            s.sid AS student_id,
            qn.question_text,
            sa.user_answer,
            qn.correct_answer,
            (sa.user_answer = qn.correct_answer) AS is_correct,
            sa.answered_at
        FROM student_answers sa
        JOIN students s ON sa.sid = s.sid
        JOIN users u ON s.user_id = u.id
        JOIN questions qn ON sa.question_id = qn.id
        WHERE sa.quiz_id = ?
        ORDER BY sa.answered_at DESC
    """

    cursor.execute(query, (quiz_id,))
    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "student_name": row[0],
            "student_id": row[1],
            "question_text": row[2],
            "answer_given": row[3],
            "correct_answer": row[4],
            "is_correct": bool(row[5]),
            "submitted_at": row[6],
        }
        for row in rows
    ]


def getAllLessons():
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, name FROM lessons")
    lessons = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
    connection.close()
    return lessons


def addLesson(name):
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO lessons (name) VALUES (?)", (name,))
    connection.commit()
    connection.close()


def deleteLesson(lesson_id):
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
    connection.commit()
    connection.close()


def getLessonByName(name):
    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM lessons WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    return {"id": row[0], "name": row[1]} if row else None


def updateLesson(lesson_id, new_name):
    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute("UPDATE lessons SET name = ? WHERE id = ?", (new_name, lesson_id))
    conn.commit()
    conn.close()
