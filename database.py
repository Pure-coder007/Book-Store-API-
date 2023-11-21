import mysql.connector
from mysql.connector import Error


config = {
    'user' : 'root',
    'password' : 'language007',
    'host' : 'localhost',
    'port' : '3306',
    'database' : 'book_store_api'
}


def setup_database():
    config['database'] = None
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY, 
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,  
    password VARCHAR(255) NOT NULL,      
    is_admin BOOLEAN DEFAULT FALSE,      
    wallet_balance BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
    

    cursor.execute("""
    CREATE TABLE selected_books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    quantity INT NOT NULL,
    genre VARCHAR(100) NOT NULL,
    price BIGINT NOT NULL,
    time_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
    );
""")
    


    cursor.execute("""
    CREATE TABLE reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    book_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    review TEXT NOT NULL,
    stars INT NOT NULL,
    review_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
    );
""")