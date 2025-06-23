import os
import logging
from flask import Flask, request, send_from_directory
import mysql.connector

LOG_DIR = os.path.join(os.path.dirname(__file__), 'log')
LOG_FILE = os.path.join(LOG_DIR, 'server.log')
os.makedirs(LOG_DIR, exist_ok=True)

app = Flask(__name__)

handler = logging.FileHandler(LOG_FILE)
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
handler.setFormatter(formatter)

for h in list(app.logger.handlers):
    app.logger.removeHandler(h)

app.logger.addHandler(handler)
app.logger.setLevel(logging.ERROR)


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/script.js')
def js():
    return send_from_directory('.', 'script.js')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    dado = data.get('dado')

    try:
        conn = mysql.connector.connect(
            host="db", user="root", password="root", database="t2"
        )
        cursor = conn.cursor()
        # Parte vulnerável a SQL Injection
        query = f"INSERT INTO users (dado) VALUES ('{dado}')"
        cursor.execute(query)
        conn.commit()
        cursor.close()
        conn.close()
        return {'status': 'ok'}

    except mysql.connector.Error as err:
        app.logger.error(f"Database error: {err}", exc_info=True)
        return {'status': 'error', 'message': str(err)}, 500

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {e}", exc_info=True)
    return {'status': 'error', 'message': 'Erro interno no servidor'}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
