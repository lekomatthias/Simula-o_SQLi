import os
import logging
from flask import Flask, request, send_from_directory, jsonify
import mysql.connector

LOG_DIR = os.path.join(os.path.dirname(__file__), 'log')
LOG_FILE = os.path.join(LOG_DIR, 'server.log')
os.makedirs(LOG_DIR, exist_ok=True)

app = Flask(__name__)

handler = logging.FileHandler(LOG_FILE)
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
handler.setFormatter(formatter)
app.logger.handlers.clear()
app.logger.addHandler(handler)
app.logger.setLevel(logging.ERROR)

ACCESS_LOG_FILE = os.path.join(LOG_DIR, 'access.log')
# Configura o logger de acesso
access_logger = logging.getLogger('werkzeug')
access_handler = logging.FileHandler(ACCESS_LOG_FILE)
access_logger.addHandler(access_handler)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/script.js')
def js():
    return send_from_directory('.', 'script.js')

def _insert_unsafe(cursor, dado):
    full_query = f"INSERT INTO data_db (dado) VALUES ('{dado}')"
    commands = full_query.split(';')
    for command in commands:
        stripped_command = command.strip()
        if stripped_command and not stripped_command.startswith('--'):
            cursor.execute(stripped_command)
    return full_query

def _insert_safe(cursor, dado):
    query = "INSERT INTO data_db (dado) VALUES (%s)"
    cursor.execute(query, (dado,))
    return cursor.statement

@app.route('/submit', methods=['POST'])
def submit():
    MODE = 'safe'
    
    data = request.get_json()
    dado = data.get('dado')
    executed_query = ""

    try:
        conn = mysql.connector.connect(
            host="db", 
            user="root", 
            password="root", 
            database="t2"
        )
        cursor = conn.cursor()

        if MODE == 'safe':
            executed_query = _insert_safe(cursor, dado)
        else:
            executed_query = _insert_unsafe(cursor, dado)

        conn.commit()
        cursor.close()
        conn.close()
        return {'status': 'ok', 'mode': MODE, 'executed_query': executed_query}

    except mysql.connector.Error as err:
        app.logger.error(f"Database error: {err}", exc_info=True)
        return {'status': 'error', 'mode': MODE, 'message': str(err)}, 500

@app.route('/dados', methods=['GET'])
def list_data():
    try:
        conn = mysql.connector.connect(
            host="db", user="root", password="root", database="t2"
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, dado FROM data_db ORDER BY id DESC")
        dados = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(dados)
    except mysql.connector.Error as err:
        app.logger.error(f"Database error: {err}", exc_info=True)
        return jsonify([]), 500

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {e}", exc_info=True)
    return {'status': 'error', 'message': 'Internal server error'}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
