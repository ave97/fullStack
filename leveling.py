from sqlFunctions import getConnection

def xp_required_for_level(level):
    return int(100 * (level ** 1.5))

def calculate_level_and_progress(total_xp):
    level = 1
    xp_for_next = xp_required_for_level(level)

    while total_xp >= xp_for_next:
        total_xp -= xp_for_next
        level += 1
        xp_for_next = xp_required_for_level(level)

    return {
        "level": level,
        "xp_into_level": total_xp,
        "xp_for_next_level": xp_for_next,
        "progress_percent": int((total_xp / xp_for_next) * 100)
    }

def get_student_level_info(sid):
    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute("SELECT xp FROM students WHERE sid = ?", (sid,))
    row = cursor.fetchone()
    if not row:
        return None

    total_xp = row[0]
    info = calculate_level_and_progress(total_xp)
    info["total_xp"] = total_xp
    return info