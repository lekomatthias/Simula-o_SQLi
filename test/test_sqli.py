
import requests
import time

class SQLiTester:
    """
    Classe para executar um teste de injeção de SQL (SQL Injection) em um endpoint.

    O teste consiste em três passos principais:
    1. Inserir um dado de controle (canary) para verificar a funcionalidade básica.
    2. Enviar um payload malicioso de SQL Injection que tenta apagar todos os dados.
    3. Verificar se o payload foi bem-sucedido ao checar se a tabela de dados está vazia.
    """

    def __init__(self, base_url):
        """
        Inicializa o testador de SQLi.
        """
        self.base_url = base_url
        self.session = requests.Session()

    def _get_data(self):
        """Busca os dados atuais no banco."""
        try:
            response = self.session.get(f"{self.base_url}/dados")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar dados: {e}")
            return None

    def _send_data(self, payload):
        """Envia um dado para o endpoint de inserção."""
        try:
            response = self.session.post(f"{self.base_url}/submit", json={'dado': payload})
            response.raise_for_status()
            print(f"Enviado payload: '{payload}' | Status: {response.status_code}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Erro ao enviar payload '{payload}': {e}")
            return False

    def run_test(self):
        """
        Executa o fluxo completo do teste de SQL Injection.
        """
        print("--- Iniciando teste de SQL Injection ---")

        # Passo 1: Inserir e verificar um dado de controle
        print("\nPasso 1: Inserindo um dado de controle ('canary')...")
        if not self._send_data('canary'):
            print("Falha ao inserir dado de controle. Teste abortado.")
            return

        time.sleep(1)
        initial_data = self._get_data()
        if initial_data is None or not any(item.get('dado') == 'canary' for item in initial_data):
            print("Falha: O dado de controle 'canary' não foi encontrado após a inserção.")
            print("--- Teste Falhou ---")
            return
        print("Sucesso: Dado de controle 'canary' inserido.")

        # Passo 2: Enviar o payload de SQL Injection
        print("\nPasso 2: Enviando payload de SQL Injection...")
        sqli_payload = "'); DELETE FROM data_db; --"
        if not self._send_data(sqli_payload):
            print("Falha ao enviar o payload de SQLi. Teste abortado.")
            return

        time.sleep(1)

        # Passo 3: Verificar o resultado do ataque
        print("\nPasso 3: Verificando se o ataque foi bem-sucedido...")
        final_data = self._get_data()

        if final_data is not None and not final_data:
            print("\nResultado: Sucesso! A tabela de dados foi esvaziada.")
            print("--- VULNERABILIDADE DE SQL INJECTION CONFIRMADA ---")
        else:
            print(f"\nResultado: Falha. A tabela ainda contém dados ou ocorreu um erro: {final_data}")
            print("--- APLICAÇÃO PARECE SEGURA CONTRA ESTE VETOR DE ATAQUE ---")

if __name__ == "__main__":
    time.sleep(10)
    tester = SQLiTester(base_url="http://firewall:80")
    tester.run_test()
    