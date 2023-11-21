from flask import Flask, request, Blueprint, jsonify,abort
import mysql.connector
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from passlib.hash import pbkdf2_sha256 as sha256
from models import add_user, get_user, users_profile, add_books, get_book
from email_validator import validate_email, EmailNotValidError
from books import books
from database import config

app = Flask(__name__)
jwt = JWTManager()
auth = Blueprint('auth', __name__)
app.config.from_pyfile('config.py')

def create_app(test_config = None):
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = 'language007'
    app.register_blueprint(auth, url_prefix='/auth/v1')
    jwt.init_app(app)
    return app

def email_exists(email):
    user = get_user(email)
    return user is not None


@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    first_name = data['first_name']
    last_name = data['last_name']
    email = data['email']
    password = data['password']
    wallet_balance = data.get('wallet_balance', 0)

    if email_exists(email):
        print(f"Email already exists: {email}")
        return jsonify({
        'message': 'Email already exists',
        'status': 400
        }), 400
    try:
        v = validate_email(email)
        email = v["email"]
    except EmailNotValidError as e:
        return jsonify({
            'message': 'Invalid email address',
            'status': 400
        }), 400
    password_hash = sha256.hash(password)
    add_user(first_name, last_name, email, password_hash, wallet_balance, False)
    return jsonify({'message': 'You have been registered successfully!'}), 201


@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not data:
        return jsonify ({
            'message': 'Missing JSON in request', 
            'status': 400
        }), 400
    
    if not email or not password:
        return jsonify ({'message' : 'Missing email or password', 
                         'status': 400}), 400
    
    user = get_user(email)

    if user and sha256.verify(password, user.password):
        access_token = create_access_token(identity=user.id)
        print('Login successful for user:', user.id)
        print('Login successful')
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'status': 200
        }), 200
    else:
        return jsonify({'message': 'Invalid email or password', 'status': 401}), 401
    


@auth.route('/user_profile', methods=['GET', 'PUT'])
@jwt_required()
def user_profile():
    user_id = get_jwt_identity()
    if user_id is None:
        return jsonify({'message': 'User not found', 'status': 400}), 400

    try:
        connection = mysql.connector.connect(**config)
        with connection.cursor() as cursor:
            view_profile = """
                SELECT id, first_name, last_name, email, wallet_balance
                FROM users
                WHERE id = %s
            """
            cursor.execute(view_profile, (user_id,))
            person = cursor.fetchone()

            if not person:
                return jsonify({'message': 'No profile found', 'status': 400}), 400

        
        user_id, first_name, last_name, email, wallet_balance = person

        return jsonify({'message': 'Here is your profile', 
                        'profile': {'user_id': user_id, 'first_name': first_name, 'last_name': last_name, 'email': email, 'wallet_balance': wallet_balance},
                        'status': 200}), 200

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({'message': 'Internal Server Error', 'status': 500}), 500

    finally:
        if connection.is_connected():
            connection.close()





@auth.route('/update_profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    user_id = get_jwt_identity()
    if user_id is None:
        return jsonify({'message': 'User not found', 'status': 400}), 400

    try:
        connection = mysql.connector.connect(**config)
        with connection.cursor() as cursor:
            update_profile = """
                UPDATE users
                SET first_name = %s, last_name = %s, email = %s
                WHERE id = %s
            """

            data = request.get_json()
            cursor.execute(update_profile, (data['first_name'], data['last_name'], data['email'], user_id))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'message': 'No profile found to update', 'status': 400}), 400

        return jsonify({'message': 'Profile updated successfully', 'status': 200}), 200

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        connection.rollback()
        return jsonify({'message': 'Internal Server Error', 'status': 500}), 500

    finally:
        if connection.is_connected():
            connection.close()



# Showing available books
@auth.route('/get_books', methods=['GET'])
@jwt_required()
def get_books():
    print(books)
    return jsonify({'Available Books': books})


def book_exist(name):
    book = get_book(name)
    return book is not None



@auth.route('/add_book', methods=['POST'])
@jwt_required()
def add_book():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        print("Present user_id:", user_id)

        if user_id is None:
            return jsonify({'message': 'User not found', 'status': 400}), 400

        name = data.get('name')
        quantity = data.get('quantity')
        price = data.get('price')
        genre = data.get('genre')

        if not name or not quantity or not price or not genre:
            return jsonify({'message': 'All fields are required', 'status': 400}), 400

        connection = mysql.connector.connect(**config)
        try:
            with connection.cursor() as cursor:
                # Check if the book is already in the cart for the user
                select_query = "SELECT * FROM selected_books WHERE user_id = %s AND name = %s AND genre = %s AND price = %s"
                cursor.execute(select_query, (user_id, name, genre, price))
                existing_book = cursor.fetchone()

                if existing_book:
                    # If the book already exists for the user, update the quantity
                    update_query = "UPDATE selected_books SET quantity = quantity + %s WHERE user_id = %s AND name = %s"
                    cursor.execute(update_query, (quantity, user_id, name))
                    connection.commit()
                    print("user_id:", user_id)
                    return jsonify({'message': 'Quantity updated in the cart successfully', 'status': 200}), 200
                else:
                    
                    insert_query = "INSERT INTO selected_books (user_id, name, quantity, price, genre) VALUES (%s, %s, %s, %s, %s)"
                    cursor.execute(insert_query, (user_id, name, quantity, price, genre))
                    connection.commit()
                    print('name:', name, 'quantity:', quantity, 'price:', price, 'genre:', genre)
                    return jsonify({'message': 'Book added to the cart successfully', 'status': 200}), 200

        except mysql.connector.Error as e:
            return jsonify({'message': f'Database error: {e}', 'status': 500}), 500

        finally:
            connection.close()

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'message': 'Internal server error', 'status': 500}), 500
    


# View Cart
@auth.route('/view_cart', methods=['GET'])
@jwt_required()
def view_cart():
    user_id = get_jwt_identity()
    if user_id is None:
        return jsonify ({'message' : 'User not found', 'status': 400}), 400
    try:
        connection = mysql.connector.connect(**config)
        with connection.cursor() as cursor:
            # Retrieve selected products in the cart for the user
            view_cart_query = """
                SELECT name, quantity, price
                FROM selected_books
                WHERE user_id = %s
            """
            cursor.execute(view_cart_query, (user_id,))
            books = cursor.fetchall()

            if not books:
                return jsonify({'message': 'Your cart is empty', 'status': 200, 'cart': []}), 200

            # Convert the result to a list of dictionaries for JSON response
            cart_list = [{ 'name': book[0], 'quantity': book[1], 'price': book[2]} for book in books]

        return jsonify({'message': 'Cart retrieved successfully', 'status': 200, 'cart': cart_list}), 200

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({'message': 'Internal Server Error', 'status': 500}), 500

    finally:
        if connection.is_connected():
            connection.close()




# Delete a book from cart
@auth.route('/delete_book', methods=['DELETE'])
@jwt_required()
def delete_book():
    user_id = get_jwt_identity()
    data = request.get_json()

    if user_id is None:
        return jsonify({'message': 'User not found', 'status': 400}), 400

    name = data.get('name') 

    if name is None:
        return jsonify({'message': 'Item not found', 'status': 400}), 400

    try:
        connection = mysql.connector.connect(**config)
        with connection.cursor() as cursor:
            # Check if the product exists for the user before deleting
            check_query = "SELECT * FROM selected_books WHERE name = %s AND user_id = %s"
            cursor.execute(check_query, (name, user_id))
            product = cursor.fetchone()

            if product is None:
                return jsonify({'message': 'Book not found for the user', 'status': 404}), 404

            delete_query = "DELETE FROM selected_books WHERE name = %s AND user_id = %s"
            cursor.execute(delete_query, (name, user_id))
        
        connection.commit()
        return jsonify({'message': 'Book deleted successfully', 'status': 200}), 200

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({'message': 'Internal Server Error', 'status': 500}), 500

    finally:
        if connection.is_connected():
            connection.close()



# Filter by author
@auth.route('/author_filter/<author>', methods=['GET'])
@jwt_required()
def author_filter(author):
    try:
        user_id = get_jwt_identity()
        # data = request.get_json()
        # author = data.get('author')

        if user_id is None:
            return jsonify({'message': 'User not found', 'status': 400}), 400

        if not author:
            return jsonify({'message': 'Author name is required', 'status': 400}), 400

        filtered_books = [book for book in books if book['author'] == author]

        if not filtered_books:
            return jsonify({'message': 'Author not found in the book list', 'status': 404}), 404

        return jsonify({'message': 'Book(s) by this author', 'books': filtered_books, 'status': 200}), 200

    except Exception as e:
        return jsonify({'message': f'Internal server error: {e}', 'status': 500}), 500
    



# Filter by genre
@auth.route('/genre_filter/<genre>', methods=['GET'])
@jwt_required()
def genre_filter(genre):
    try:
        user_id = get_jwt_identity()
        # genre = data.get('genre')
        # genre = request.args.get('genre')
        print(genre, 'gnre')

        if user_id is None:
            return jsonify({'message': 'User not found', 'status': 400}), 400

        if not genre:
            return jsonify({'message': 'Genre name is required', 'status': 400}), 400

        filtered_books = [book for book in books if book['genre'] == genre]

        if not filtered_books:
            return jsonify({'message': 'Genre not found in the book list', 'status': 404}), 404

        return jsonify({'message': 'Book(s) by this genre', 'books': filtered_books, 'status': 200}), 200

    except Exception as e:
        return jsonify({'message': f'Internal server error: {e}', 'status': 500}), 500
    




@auth.route('/title_filter/<title>', methods=['GET'])
@jwt_required()
def title_filter(title):
    try:
        user_id = get_jwt_identity()
        # title = data.get('title')
        # title = request.args.get('title')

        if user_id is None:
            return jsonify({'message': 'User not found', 'status': 400}), 400

        if not title:
            return jsonify({'message': 'Title name is required', 'status': 400}), 400

        filtered_books = [book for book in books if book['title'] == title]
        print("Title:", filtered_books)

        if not filtered_books:
            return jsonify({'message': 'Title not found in the book list', 'status': 404}), 404

        return jsonify({'message': 'Book(s) by this title', 'books': filtered_books, 'status': 200}), 200

    except Exception as e:
        return jsonify({'message': f'Internal server error: {e}', 'status': 500}), 500
    





# Users wallet top-up
@auth.route('/top_up/<int:id>', methods=['PUT'])
@jwt_required()
def top_up(id):
    user_id = get_jwt_identity()
    if user_id is None:
        return jsonify({'message': 'User not found'}), 404
    
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()

    query = "SELECT id FROM users WHERE id = %s"
    cursor.execute(query, (id,))
    customer = cursor.fetchone()
    if customer and customer[0] == user_id:
        wallet_balance = request.json.get('wallet_balance')
        print('nnnnnnnnnn', wallet_balance)

        if wallet_balance is not None:
            query = "UPDATE users SET wallet_balance = %s WHERE id = %s"
            cursor.execute(query, (wallet_balance, id))
            connection.commit()
            cursor.close()
            connection.close()
            return jsonify({'message': 'Wallet updated successfully', 'status': 200}), 200
        else:
            cursor.close()
            connection.close()
            return jsonify({'message': 'Not successful'}), 401

    cursor.close()
    connection.close()
    return jsonify({'message': 'User is not authorized to update this wallet'}, 401)








@auth.route('/payment', methods=['PATCH'])
@jwt_required()
def payment():
    user_id = get_jwt_identity()
    # data = request.get_json()
    # check_out = data.get('check_out')


    if user_id is None:
        return jsonify ({'message' : 'User not found', 'status':400}), 400
    
    try:
        connection = mysql.connector.connect(**config)
        with connection.cursor() as cursor:
            check_cart = "SELECT COUNT(*) FROM selected_books WHERE user_id = %s"
            cursor.execute(check_cart, (user_id,))
            cart_count = cursor.fetchone()[0]

            if cart_count == 0:
                return jsonify ({'message' : 'Your cart is empty. Add books befor checking out', 'status': 400}), 400
            
            bal_query = "SELECT wallet_balance FROM users WHERE id = %s"
            cursor.execute(bal_query, (user_id,))
            wallet_balance = cursor.fetchone()[0]

            get_total = "SELECT SUM(quantity * price) FROM selected_books WHERE user_id = %s"
            cursor.execute(get_total, (user_id,))
            total_amount = cursor.fetchone()[0]

            if wallet_balance < total_amount:
                return jsonify ({'message' : 'Insufficient wallet balance', 'status': 400}), 400
            
            new_bal = wallet_balance - total_amount
            update_bal = "UPDATE users SET wallet_balance = %s WHERE id = %s"
            cursor.execute(update_bal, (new_bal, user_id)) 

            del_book = "DELETE FROM selected_books WHERE user_id = %s"
            cursor.execute(del_book, (user_id,))
        connection.commit()
        return jsonify ({'message': 'Payment successful', 'status': 200, "new_balance": new_bal}), 200
    
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify ({'message': 'Internal server error', 'status': 500}), 500
    
    finally:
        if connection.is_connected():
            connection.close()





def save_review(book_id, review, stars, name, user_id):
    try:
        print('i got here')
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        cursor.execute("INSERT INTO reviews (book_id, review, stars, name, user_id) VALUES (%s, %s, %s, %s, %s)",(book_id, review, stars, name, user_id))
        connection.commit()
        print('i am abouot to liv')
    except mysql.connector.Error as err:
        print("Error:", err)
    finally:
        cursor.close()
        connection.close()
        print('Left')



# Giving reviews about a book
@auth.route('/review', methods=['POST'])
@jwt_required()
def review():
    user_id = get_jwt_identity()
    data = request.get_json()

    if user_id is None:
        return jsonify ({'message' : 'User not found', 'status' : 400}), 400
    
    book_id = data.get('book_id')
    # name = data.get('name')
    review = data.get('review')
    stars = data.get('stars')

    if not book_id  or not review or not stars:
            return jsonify({'message': 'All fields are required', 'status': 400}), 400
    

    try:
        connection = mysql.connector.connect(**config)
        with connection.cursor() as cursor:
            view_profile = """
                SELECT id, first_name, last_name, email, wallet_balance
                FROM users
                WHERE id = %s
            """
            cursor.execute(view_profile, (user_id,))
            person = cursor.fetchone()
            print('ppppppppp', person)

            first_name = person[1]

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({'message': 'Internal Server Error', 'status': 500}), 500

    if stars > 5:
        return jsonify({'message': 'You cant rate higher than 5'})
    else:
        save_review(book_id, review, stars, first_name, user_id)
        return jsonify ({'message': 'Thank you for your review', 'status': 200}), 200
    
