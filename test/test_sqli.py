
import requests
import time

URL = "http://firewall:80"

def get_data():
    """Busca os dados atuais no banco."""
    try:
        response = requests.get(f"{URL}/dados")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar dados: {e}")
        return None

def send_data(payload):
    """Envia um dado para o endpoint de inserção."""
    try:
        response = requests.post(f"{URL}/submit", json={'dado': payload})
        response.raise_for_status()
        print(f"Enviado payload: '{payload}' | Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar payload '{payload}': {e}")
        return False

def run_test():
    """Executa o teste de SQL Injection."""
    print("--- Iniciando teste de SQL Injection ---")

    # 1. Inserir um dado de controle para garantir que o banco não está vazio
    print("\nPasso 1: Inserindo um dado de controle ('canary')...")
    if not send_data('canary'):
        print("Falha ao inserir dado de controle. Teste abortado.")
        return
    time.sleep(1)

    # 2. Verificar se o dado de controle foi inserido
    initial_data = get_data()
    if not any(item['dado'] == 'canary' for item in initial_data):
        print("Falha: O dado de controle 'canary' não foi encontrado após a inserção.")
        print("--- Teste Falhou ---")
        return
    print("Sucesso: Dado de controle 'canary' inserido.")

    # 3. Enviar o payload de SQL Injection
    print("\nPasso 2: Enviando payload de SQL Injection...")
    sqli_payload = "'); DELETE FROM data_db; --"
    if not send_data(sqli_payload):
        print("Falha ao enviar o payload de SQLi. Teste abortado.")
        return
    time.sleep(1)

    # 4. Verificar o resultado
    print("\nPasso 3: Verificando se o ataque foi bem-sucedido...")
    final_data = get_data()

    if final_data is not None and not final_data:
        print("Resultado: Sucesso! A tabela foi esvaziada.")
        print("--- VULNERABILIDADE CONFIRMADA ---")
    else:
        print(f"Resultado: Falha. A tabela ainda contém dados: {final_data}")
        print("--- APLICAÇÃO PARECE SEGURA ---")


if __name__ == "__main__":
    """Espera 10 segundos e executa o teste."""
    time.sleep(10)
    run_test()
