import mysql.connector
from datetime import datetime
from database import config

class User():
    def __init__(self, id, first_name, last_name, email, password, is_admin=False):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.is_admin = is_admin

        @classmethod
        def get(cls, user_id):
            pass

def add_user(first_name, last_name, email, password, wallet_balance, is_admin=False):
    try: 
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        cursor.execute("INSERT INTO users (first_name, last_name, email, password, wallet_balance, is_admin) VALUES (%s, %s, %s, %s, %s, %s)", (first_name, last_name, email, password, wallet_balance, is_admin))
        connection.commit()

    except mysql.connector.Error as err:
        print("Error:", err)
    finally:
        cursor.close()
        connection.close()



def get_user(email):
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute('SELECT * FROM users WHERE email=%s', (email,))

        user_record = cursor.fetchone()
        
        if user_record:
            return User(
                id=user_record['id'],
                first_name=user_record['first_name'],
                last_name=user_record['last_name'],
                email=user_record['email'],
                password=user_record['password'],
                is_admin=user_record['is_admin']
            )
        return None
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    finally:
        if cursor: cursor.close()
        if connection: connection.close()



def users_profile(email):
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute('SELECT * FROM users WHERE email=%s', (email,))

        user_record = cursor.fetchone()
        
        if user_record:
            return User(
                id=user_record['id'],
                first_name=user_record['first_name'],
                last_name=user_record['last_name'],
                email=user_record['email'],
                is_admin=user_record['is_admin']
            )
        return None
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    finally:
        if cursor: cursor.close()
        if connection: connection.close()


# def add_books(name, quantity, price, user_id, genre):
#     connection = mysql.connector.connect(**config)
#     try:
#         cursor = connection.cursor()
#         query = "INSERT INTO selected_products (name, quantity, price, user_id, genre) VALUES (%s, %s, %s, %s, %s)"
#         cursor.execute(query, (name, quantity, price, user_id, genre))
#         connection.commit()
#     except mysql.connector.Error as e:
#         connection.rollback()
#         raise  
#     finally:
#         if cursor:
#             cursor.close()
#         connection.close()


def add_books(name, genre, quantity, price, user_id):
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()
    insert_query = """
    INSERT INTO selected_books (name, genre, quantity, price, user_id) VALUES (%s, %s, %s, %s, %s)
"""
    cursor.execute(insert_query, (name, genre, quantity, price, user_id))
    connection.commit()
    cursor.close()
    connection.close()
    return True


def get_book(name):
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM selected_books WHERE name = %s"
    cursor.execute(query, (name,))
    result = cursor.fetchone()
    cursor.close
    connection.close()
    return result