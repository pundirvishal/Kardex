import sqlite3


class KardexDB:
    def __init__(self, db_name="kardex.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

        # Enable cascading deletes for project-task relationships.
        self.cursor.execute("PRAGMA foreign_keys = ON;")
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                status TEXT DEFAULT 'Ready',
                deadline TEXT,
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE
            )
        """)
        self.conn.commit()

    def get_projects(self):
        self.cursor.execute("SELECT * FROM projects")
        return self.cursor.fetchall()

    def add_project(self, name):
        sql_command = """
            INSERT INTO projects (name) VALUES (?)
        """
        self.cursor.execute(sql_command, (name,))
        self.conn.commit()
        project_id = int(self.cursor.lastrowid)
        print(f"Project '{name}' added successfully!")
        return project_id

    def add_task(self, title, deadline=None, project_id=None, task_status='Ready'):
        sql_command = """
            INSERT INTO tasks (title, status, deadline, project_id) VALUES (?, ?, ?, ?)
        """
        self.cursor.execute(sql_command, (title, task_status, deadline, project_id))
        self.conn.commit()
        task_id = int(self.cursor.lastrowid)
        print(f"Task '{title}' added to the '{task_status}' column!")
        return task_id
    
    def update_status(self, task_id, new_status):
        sql_command = """
            UPDATE tasks SET status = ? WHERE id = ?
        """
        self.cursor.execute(sql_command, (new_status, task_id))
        self.conn.commit()

    def update_task(self, task_id, title, deadline):
        sql_command = """
            UPDATE tasks
            SET title = ?, deadline = ?
            WHERE id = ?
        """
        self.cursor.execute(sql_command, (title, deadline, task_id))
        self.conn.commit()
    
    def delete_task(self, task_id):
        sql_command = """
            DELETE FROM tasks WHERE id = ?
        """
        self.cursor.execute(sql_command, (task_id,))
        self.conn.commit()

    def delete_project(self, project_id):
        sql_command = """
            DELETE FROM projects WHERE id = ?
        """
        self.cursor.execute(sql_command, (project_id,))
        self.conn.commit()

    def get_tasks(self):
        self.cursor.execute("SELECT * FROM tasks")
        return self.cursor.fetchall()

    def get_task(self, task_id):
        sql_command = """
            SELECT id, title, status, deadline, project_id
            FROM tasks
            WHERE id = ?
        """
        self.cursor.execute(sql_command, (task_id,))
        return self.cursor.fetchone()

    def get_tasks_by_project(self, project_id):
        sql_command = """
            SELECT id, title, status, deadline
            FROM tasks
            WHERE project_id = ?
            ORDER BY id
        """
        self.cursor.execute(sql_command, (project_id,))
        return self.cursor.fetchall()


if __name__ == "__main__":
    # Quick smoke test when running this file directly.
    db = KardexDB()
    print("Database and tasks table created successfully! 🎉")