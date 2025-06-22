import logging
from flask import Flask, request, send_from_directory
import mysql.connector
import os

LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'server.log')

os.makedirs(LOG_DIR, exist_ok=True)

app = Flask(__name__)

handler = logging.FileHandler(LOG_FILE)
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
handler.setFormatter(formatter)
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
        cursor.execute("INSERT INTO users (dado) VALUES (%s)", (dado,))
        conn.commit()
        cursor.close()
        conn.close()
        return {'status': 'ok'}
    except mysql.connector.Error as err:
        app.logger.error(f"Database error: {err}")
        return {'status': 'error', 'message': str(err)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
