
import os
import logging
import re
from flask import Flask, request, send_from_directory, jsonify
import mysql.connector

class SqliApp:
    """
    Uma classe para encapsular a aplicação Flask, gerenciando rotas, 
    configuração de logging e interações com o banco de dados.
    """

    def __init__(self, host='0.0.0.0', port=5000, safe_mode=False):
        """Inicializa a aplicação Flask e suas configurações."""
        self.app = Flask(__name__)
        self.host = host
        self.port = port
        self.mode = os.getenv('APP_MODE', 'safe' if safe_mode else 'unsafe').lower()

        self.db_config = {
            "host": "db", 
            "user": "root", 
            "password": "root", 
            "database": "t2"
        }

        self._setup_logging()
        self._register_routes()
        self._register_error_handlers()

    def _setup_logging(self):
        """Configura os loggers da aplicação e do Werkzeug."""
        log_dir = os.path.join(os.path.dirname(__file__), 'log')
        os.makedirs(log_dir, exist_ok=True)

        app_log_file = os.path.join(log_dir, 'server.log')
        handler = logging.FileHandler(app_log_file)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [from %(remote_addr)s]')
        handler.setFormatter(formatter)
        self.app.logger.handlers.clear()
        self.app.logger.addHandler(handler)
        self.app.logger.setLevel(logging.INFO)

        # Logger de acesso (Werkzeug)
        access_log_file = os.path.join(log_dir, 'access.log')
        access_logger = logging.getLogger('werkzeug')
        access_handler = logging.FileHandler(access_log_file)
        access_logger.addHandler(access_handler)

    def _get_db_connection(self):
        """Cria e retorna uma nova conexão com o banco de dados."""
        return mysql.connector.connect(**self.db_config)

    def _register_routes(self):
        """Registra as rotas da aplicação."""
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/script.js', 'js', self.js)
        self.app.add_url_rule('/submit', 'submit', self.submit, methods=['POST'])
        self.app.add_url_rule('/dados', 'list_data', self.list_data, methods=['GET'])
        
    def _register_error_handlers(self):
        """Registra o manipulador de erros global."""
        self.app.errorhandler(Exception)(self.handle_exception)

    @staticmethod
    def _detectar_sqli(input_string):
        """Detecta padrões comuns de SQL Injection em uma string."""
        if not isinstance(input_string, str):
            return False
        
        if ';' in input_string:
            return True
            
        sqli_patterns = re.compile(
            r'\b(OR|AND)\b\s+[\'"]?\w+[\'"]?\s*=\s*[\'"]?\w+[\'"]?|'
            r'\b(DROP|DELETE|TRUNCATE|UPDATE|INSERT)\b|'
            r'--|\#',
            re.IGNORECASE
        )
        
        return bool(sqli_patterns.search(input_string))

    @staticmethod
    def _insert_unsafe(cursor, dado):
        """Executa uma inserção de forma insegura, vulnerável a SQLi."""
        full_query = f"INSERT INTO data_db (dado) VALUES ('{dado}')"
        commands = full_query.split(';')
        for command in commands:
            stripped_command = command.strip()
            if stripped_command and not stripped_command.startswith('--'):
                cursor.execute(stripped_command)
        return full_query

    @staticmethod
    def _insert_safe(cursor, dado):
        """Executa uma inserção de forma segura usando queries parametrizadas."""
        query = "INSERT INTO data_db (dado) VALUES (%s)"
        cursor.execute(query, (dado,))
        return cursor.statement

    def index(self):
        """Serve o arquivo index.html."""
        return send_from_directory('.', 'index.html')

    def js(self):
        """Serve o arquivo script.js."""
        return send_from_directory('.', 'script.js')

    def submit(self):
        """Recebe e insere dados no banco de dados."""
        data = request.get_json()
        dado = data.get('dado')
        executed_query = ""

        if self.mode == 'unsafe' and self._detectar_sqli(dado):
            self.app.logger.warning(
                f"Potencial tentativa de SQL Injection detectada. Payload: \"{dado}\"",
                extra={'remote_addr': request.remote_addr}
            )
        
        conn = None
        cursor = None
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            if self.mode == 'safe':
                executed_query = self._insert_safe(cursor, dado)
            else:
                executed_query = self._insert_unsafe(cursor, dado)

            conn.commit()
            return {'status': 'ok', 'mode': self.mode, 'executed_query': executed_query}
        except mysql.connector.Error as err:
            self.app.logger.error(
                f"Database error: {err} | Payload: \"{dado}\"",
                extra={'remote_addr': request.remote_addr},
                exc_info=True
            )
            return {'status': 'error', 'mode': self.mode, 'message': str(err)}, 500
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def list_data(self):
        """Lista os dados armazenados no banco de dados."""
        conn = None
        cursor = None
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, dado FROM data_db ORDER BY id DESC")
            dados = cursor.fetchall()
            return jsonify(dados)
        except mysql.connector.Error as err:
            self.app.logger.error(
                f"Database error: {err}", 
                extra={'remote_addr': request.remote_addr},
                exc_info=True
            )
            return jsonify([]), 500
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def handle_exception(self, e):
        """Manipulador de exceções não tratadas."""
        self.app.logger.error(
            f"Unhandled exception: {e}", 
            extra={'remote_addr': request.remote_addr},
            exc_info=True
        )
        return {'status': 'error', 'message': 'Internal server error'}, 500

    def run(self):
        """Inicia o servidor de desenvolvimento do Flask."""
        self.app.run(host=self.host, port=self.port)

if __name__ == '__main__':
    app_instance = SqliApp(safe_mode=False)
    app_instance.run()