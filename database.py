import pymysql


def get_db_connection():
    connection = pymysql.connect(
        host="localhost",
        user="root",
        password="jack",
        database="ai_interview",
        cursorclass=pymysql.cursors.DictCursor
    )

    return connection


try:
    connection = get_db_connection()
    print("Database connected successfully!")

    connection.close()

except Exception as e:
    print("Database connection failed!")
    print(e)