import sqlite3

conn = sqlite3.connect('example.db',check_same_thread=False);
c = conn.cursor();
#sc.execute('''CREATE TABLE  Projects(name text)''')
c.execute('''CREATE TABLE  ProjectServer(project text, server_id text)''')
conn.commit()
