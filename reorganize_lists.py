# -*- coding: utf-8 -*-
import sqlite3
import os
import zipfile
from config import DATABASE_PATH
from database import init_db

def reorganize():
    init_db()
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()

    cur.execute("SELECT id, username FROM users")
    users = cur.fetchall()

    for user_id, uname in users:
        print(f"Organizing lists for user [{uname}] (ID: {user_id})...")

        # 1. Create or update Test List: up, down, left, right
        test_list_name = "【测试专用】Direction Test (up, down, left, right)"
        cur.execute("SELECT id FROM vocab_lists WHERE user_id = ? AND name LIKE '%测试%'", (user_id,))
        test_row = cur.fetchone()
        if test_row:
            test_list_id = test_row[0]
            cur.execute("UPDATE vocab_lists SET name = ?, sort_order = 0 WHERE id = ?", (test_list_name, test_list_id))
        else:
            cur.execute("""
                INSERT INTO vocab_lists (user_id, name, description, sort_order)
                VALUES (?, ?, '4个基础方向词专用快速测试库', 0)
            """, (user_id, test_list_name))
            test_list_id = cur.lastrowid

        # Insert 4 test words: up, down, left, right
        test_words = [
            {
                "word": "up",
                "phonetic": "/ʌp/",
                "meaning": "向上；在上面；向更高处",
                "example_en": "Look up at the stars shining in the night sky.",
                "example_cn": "抬头向上看夜空中闪烁的繁星。"
            },
            {
                "word": "down",
                "phonetic": "/daʊn/",
                "meaning": "向下；在下面；往低处",
                "example_en": "Please sit down and take a rest after the walk.",
                "example_cn": "散步之后请坐下休息片刻。"
            },
            {
                "word": "left",
                "phonetic": "/left/",
                "meaning": "左边的；向左；左侧",
                "example_en": "Turn left at the next street intersection.",
                "example_cn": "在下一个街道十字路口向左拐。"
            },
            {
                "word": "right",
                "phonetic": "/raɪt/",
                "meaning": "右边的；向右；右侧；正确的",
                "example_en": "Raise your right hand if you agree with the proposal.",
                "example_cn": "如果你赞同这项提议，请举起你的右手。"
            }
        ]

        # Clear existing words in test list to avoid duplicates
        cur.execute("DELETE FROM words WHERE user_id = ? AND list_id = ?", (user_id, test_list_id))
        for tw in test_words:
            cur.execute("""
                INSERT INTO words (list_id, user_id, word, meaning, phonetic, example_en, example_cn)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (test_list_id, user_id, tw["word"], tw["meaning"], tw["phonetic"], tw["example_en"], tw["example_cn"]))

        # 2. Rename existing lists cleanly to Packet * format and set 1, 2, 3 sequence
        cur.execute("SELECT id, name FROM vocab_lists WHERE user_id = ?", (user_id,))
        all_lists = cur.fetchall()

        for lid, lname in all_lists:
            if "Unit 11" in lname or ("Packet 3" in lname and "Workshop" in lname):
                cur.execute("UPDATE vocab_lists SET name = 'Packet 3 - Vocabulary Workshop', sort_order = 5 WHERE id = ?", (lid,))
            elif "Packet 1" in lname and ("Workshop" in lname or "G8-S" in lname):
                cur.execute("UPDATE vocab_lists SET name = 'Packet 1 - Vocabulary Workshop', sort_order = 1 WHERE id = ?", (lid,))
            elif "Packet 1" in lname and "Reading" in lname:
                cur.execute("UPDATE vocab_lists SET name = 'Packet 1 - Intensive Reading', sort_order = 2 WHERE id = ?", (lid,))
            elif "Packet 2" in lname and "Workshop" in lname:
                cur.execute("UPDATE vocab_lists SET name = 'Packet 2 - Vocabulary Workshop', sort_order = 3 WHERE id = ?", (lid,))
            elif "Packet 2" in lname and "Reading" in lname:
                cur.execute("UPDATE vocab_lists SET name = 'Packet 2 - Intensive Reading', sort_order = 4 WHERE id = ?", (lid,))
            elif "Word of the Day" in lname:
                cur.execute("UPDATE vocab_lists SET name = 'G8 EC Word of the Day #1-15', sort_order = 6 WHERE id = ?", (lid,))
            elif "首选" in lname or "全量" in lname:
                cur.execute("UPDATE vocab_lists SET name = '我的首选词库 (全量合集)', sort_order = 7 WHERE id = ?", (lid,))

    conn.commit()
    conn.close()
    print("Database lists reorganized successfully!")

    # Update ec_project.zip
    zip_path = 'd:\\EC项目\\ec_project.zip'
    exclude_dirs = {'__pycache__', '.git', '.gemini'}
    exclude_files = {'ec_project.zip'}

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('d:\\EC项目'):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for f in files:
                if f in exclude_files or f.endswith('.pyc'):
                    continue
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, 'd:\\EC项目')
                zipf.write(full_path, rel_path)

    print("Updated ec_project.zip package successfully!")

if __name__ == '__main__':
    reorganize()
