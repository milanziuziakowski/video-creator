import sqlite3

conn = sqlite3.connect('video_creator.db')
c = conn.cursor()
c.execute("SELECT id, status, video_task_id, video_url, audio_url FROM segments WHERE project_id = 'fedf053f-3fb0-48ea-8785-b2dd04bbd399'")
print("ID | Status | VideoTaskID | VideoURL | AudioURL")
print("-" * 100)
for row in c.fetchall():
    print(f"{row[0][:12]}... | {row[1]} | {row[2]} | {row[3]} | {row[4]}")
conn.close()
