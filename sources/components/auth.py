import jwt
import logging

import psycopg2

from DB_connection import get_db_connection
from flask import Blueprint, jsonify, request, current_app, session
from sources.scripts import auth_script
from datetime import datetime, timedelta
from functools import wraps
from .globals import set_user_id, remove_user_id
from .threading import start_background_threads, stop_background_threads

# Configure logging
logging.basicConfig(level=logging.DEBUG)

auth = Blueprint('auth', __name__)


def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = None
        # Check for the token in the request headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'Alert!': 'Token is missing!'}), 403

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({'Alert!': 'Token has expired!'}), 403
        except jwt.InvalidTokenError:
            return jsonify({'Alert!': 'Invalid Token!'}), 403

        return func(*args, **kwargs)

    return decorated


@auth.route('/protected', methods=['GET'])
@token_required
def protected():
   return jsonify({'message': 'Token accessed'}), 200


@auth.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid input"}), 400

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Username and password required"}), 400

        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                logging.debug("Executing query to find user by username.")
                cursor.execute(auth_script.SELECT_USER_INFO_BY_USERNAME, (email,))
                user = cursor.fetchone()
                print(f"userdata: {user}")
                if user:
                    logging.debug("User found, checking password.")
                    user_id = user[0]
                    username = user[1]
                    db_password = user[2]

                    if password == db_password:
                        session['user_id'] = user_id
                        set_user_id(user_id)
                        token = jwt.encode({
                            'user': username,
                            'expiration': str(datetime.utcnow() + timedelta(seconds=120))
                        },
                            current_app.config['SECRET_KEY'])
                        return jsonify({'token': token, 'user': user})
                    else:
                        logging.debug("Invalid password.")
                        return jsonify({"error": "Invalid username or password"}), 401
                else:
                    logging.debug("User not found.")
                    return jsonify({"error": "Invalid username or password"}), 401
        except Exception as e:
            logging.error(f"Error during login: {e}")
            return jsonify({"error": str(e)}), 500


@auth.route('/logout')
def logout():
    remove_user_id(session.get('user_id'))
    session.pop('user_id', None)
    return print("logout successfully")


@auth.route('/sign-up', methods=['POST', 'GET'])
def sign_up():
    if request.method == 'GET':
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(auth_script.SELECT_USER_INFO)
                user_info = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                user_info_list = [
                    dict(zip(column_names, row)) for row in user_info
                ]
            return jsonify({"userInfo": user_info_list}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == 'POST':
        data = request.get_json()
        print("Received POST data:", data)
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")

        if not username or not password:
            return jsonify({"error": "userName and password are required"}), 400
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                try:
                    cursor.execute(auth_script.CREATE_USER_INFO_TABLE)
                    cursor.execute(auth_script.INSERT_USER_INFO, (username, password, email))
                    user_id = cursor.fetchone()[0]
                    conn.commit()
                except psycopg2.DatabaseError as e:
                    conn.rollback()
                    print(f"Database error: {e}")
                except Exception as e:
                    conn.rollback()
                    print(f"Error: {e}")

            return {"user_id": user_id, "message": f"User {username} created"}, 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
