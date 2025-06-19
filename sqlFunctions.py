import sqlite3
from werkzeug.security import generate_password_hash


def getConnection():
    connection = sqlite3.connect("eduplay.db")
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


# Users
def createUsersDB():
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE NOT NULL, 
        email TEXT UNIQUE NOT NULL, 
        password TEXT NOT NULL, 
        role TEXT CHECK(role IN ('student', 'teacher', 'admin')) NOT NULL, 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    connection.commit()
    connection.close()


# Students
# Χρηση του user_id για τη συνδεση των πινακων users και students
def createStudentsDB():
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sid TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        class TEXT NOT NULL,
        xp INTEGER DEFAULT 0,
        total_points INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )
    connection.commit()
    connection.close()


# Teachers
def createTeachersDB():
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tid TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )
    connection.commit()
    connection.close()


def createTeacherStudentsDB():
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS teacher_students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tid INTEGER NOT NULL,
            sid INTEGER NOT NULL,
            FOREIGN KEY (tid) REFERENCES teachers(id) ON DELETE CASCADE,
            FOREIGN KEY (sid) REFERENCES students(id) ON DELETE CASCADE,
            UNIQUE (tid, sid)
        );
        """
    )
    connection.commit()
    connection.close()


# Pending Teachers
def createPendingTeachersDB():
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pending_teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL, 
        email TEXT UNIQUE NOT NULL, 
        password TEXT NOT NULL, 
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    connection.commit()
    connection.close()


# Lesson
def createLessonsDB():
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
        """
    )
    connection.commit()
    connection.close()


# Quiz
def createQuizDB():
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS quiz (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        title TEXT NOT NULL, 
        lesson TEXT,  
        created_by TEXT NOT NULL, 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        target_class TEXT  -- <-- νέο πεδίο
        );
        """
    )
    connection.commit()
    connection.close()


# Questions
def createQuestionsDB():
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        quiz_id INTEGER NOT NULL, 
        question_num INTEGER, 
        question_text TEXT NOT NULL,
        question_type TEXT NOT NULL,
        option_1 TEXT, 
        option_2 TEXT, 
        option_3 TEXT, 
        option_4 TEXT, 
        correct_answer INTEGER,  
        FOREIGN KEY (quiz_id) REFERENCES quiz(id) ON DELETE CASCADE
        );
        """
    )
    connection.commit()
    connection.close()


# Matching Type of Question
def createMatchingDB():
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS matching (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL,
        item_1 TEXT NOT NULL,
        item_2 TEXT NOT NULL,
        FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
        );
        """
    )
    connection.commit()
    connection.close()


# Quiz Results
def createQuizResultsDB():
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS quiz_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER NOT NULL,
        sid INTEGER NOT NULL,
        score INTEGER NOT NULL,
        correct_answers INTEGER NOT NULL,
        time_taken INTEGER NOT NULL,
        xp_earned INTEGER NOT NULL,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (quiz_id) REFERENCES quiz(id) ON DELETE CASCADE,
        FOREIGN KEY (sid) REFERENCES students(sid) ON DELETE CASCADE
        );
        """
    )


# Daily Spin
def createDailySpinDB():
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_spin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sid INTEGER NOT NULL,
        spin_date DATE NOT NULL,
        bonus TEXT NOT NULL,
        FOREIGN KEY (sid) REFERENCES students(sid) ON DELETE CASCADE
        );
        """
    )
    connection.commit()
    connection.close()


# Active Bonus
def createActiveBonusDB():
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS active_bonus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sid INTEGER NOT NULL,
        bonus TEXT NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        used INTEGER DEFAULT 0,
        used_for_qid INTEGER DEFAULT NULL,
        FOREIGN KEY (sid) REFERENCES students(sid) ON DELETE CASCADE
        );
        """
    )
    connection.commit()
    connection.close()


# Quiz Answers
def createQuizResultsDB():
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sid INTEGER NOT NULL,
            quiz_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            correct_answers INTEGER,
            total_questions INTEGER,
            xp_earned INTEGER,
            time_taken INTEGER,
            total_spins INTEGER,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            bonus TEXT,
            base_xp INTEGER,
            FOREIGN KEY (sid) REFERENCES students(sid) ON DELETE CASCADE,
            FOREIGN KEY (quiz_id) REFERENCES quiz(id) ON DELETE CASCADE
        );
        """
    )
    connection.commit()
    connection.close()


# Δημιουργία πίνακα student_answers
def createStudentAnswersDB():
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS student_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_result_id INTEGER NOT NULL,
            sid INTEGER NOT NULL,
            quiz_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            user_answer TEXT NOT NULL,
            is_correct BOOLEAN NOT NULL,
            answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_result_id) REFERENCES quiz_results(id) ON DELETE CASCADE,
            FOREIGN KEY (sid) REFERENCES students(sid) ON DELETE CASCADE,
            FOREIGN KEY (quiz_id) REFERENCES quiz(id) ON DELETE CASCADE,
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
        );
        """
    )
    connection.commit()
    connection.close()


# Achievements
def createAchievementsDB():
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                xp INTEGER DEFAULT 0,
                type TEXT,
                target INTEGER DEFAULT 1
            );
        """
    )
    connection.commit()
    connection.close()


def createUserAchievementsDB():
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute(
        """
            CREATE TABLE IF NOT EXISTS user_achievement_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_id INTEGER NOT NULL,
                current_value INTEGER DEFAULT 0,
                unlocked BOOLEAN DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (achievement_id) REFERENCES achievements(id) ON DELETE CASCADE,
                UNIQUE(user_id, achievement_id)
            );
        """
    )
    connection.commit()
    connection.close()


def hash_existing_passwords():
    connection = getConnection()
    cursor = connection.cursor()

    cursor.execute("SELECT username, password FROM users")
    users = cursor.fetchall()

    for username, password in users:
        hashed_password = generate_password_hash(password)
        cursor.execute(
            "UPDATE users SET password = ? WHERE username = ?",
            (hashed_password, username),
        )

    connection.commit()
    connection.close()


def deleteUser():
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM users WHERE username=(?)", ("teacher1",))
    print("Done!")
    connection.commit()
    connection.close()


def drop():
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute("DROP TABLE students;")
    connection.commit()
    connection.close()


def change():
    connection = getConnection()
    cursor = connection.cursor()

    cursor.execute("ALTER TABLE quiz ADD COLUMN target_class TEXT;")
    connection.commit()
    connection.close()


# Uncomment the following lines to create the necessary databases
# drop()
# change()
# createUsersDB()
# createStudentsDB()
# createTeachersDB()
# createTeacherStudentsDB()
# createPendingTeachersDB()
# createLessonsDB()
# createQuizDB()
# createQuestionsDB()
# createMatchingDB()
# createAnsweredQuizDB()
# createDailySpinDB()
# createActiveBonusDB()
# createQuizResultsDB()
# createStudentAnswersDB()
# createAchievementsDB()
# createUserAchievementsDB()

# def change():
#     connection = getConnection()
#     cursor = connection.cursor()

#     # 1. Απενεργοποίηση foreign key constraint για τη διάρκεια της αλλαγής
#     cursor.execute("PRAGMA foreign_keys = OFF;")

#     # 2. Εκτέλεση αλλαγής πίνακα users με νέο schema (με admin στο role)
#     cursor.executescript("""
#         CREATE TABLE users_new (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             username TEXT UNIQUE NOT NULL,
#             email TEXT UNIQUE NOT NULL,
#             password TEXT NOT NULL,
#             role TEXT CHECK(role IN ('student', 'teacher', 'admin')) NOT NULL,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         );

#         INSERT INTO users_new (id, username, email, password, role, created_at)
#         SELECT id, username, email, password, role, created_at FROM users;

#         DROP TABLE users;

#         ALTER TABLE users_new RENAME TO users;
#     """)

#     # 3. Ενεργοποίηση ξανά των foreign key constraints
#     cursor.execute("PRAGMA foreign_keys = ON;")

#     connection.commit()
#     connection.close()

# change()


def delete(i):
    connection = getConnection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM quiz WHERE id = ?", ((i,)))
    connection.commit()
    connection.close()
