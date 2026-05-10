import os
import mysql.connector

def get_db():
    return mysql.connector.connect(
        host=os.environ.get("mysql-21048be6-kumaraman27174-6f67.b.aivencloud.com"),
        user=os.environ.get("avnadmin"),
        password=os.environ.get("0987654321"),
        database=os.environ.get("job_ai")
    )