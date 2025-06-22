import psutil
import logging
from logging.handlers import RotatingFileHandler
import time
import os

logger = logging.getLogger("monitor")
logger.setLevel(logging.INFO)

handler = RotatingFileHandler("monitor.log", maxBytes=5*1024*1024, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def check_cpu_ram():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    logger.info(f"Uso CPU: {cpu}%, Uso RAM: {ram}%")
    if cpu > 80:
        logger.warning(f"CPU alta: {cpu}%")
    if ram > 80:
        logger.warning(f"RAM alta: {ram}%")

def check_open_ports():
    conns = psutil.net_connections(kind='inet')
    ports = set(conn.laddr.port for conn in conns if conn.status == 'LISTEN')
    logger.info(f"Portas abertas (escutando): {sorted(ports)}")

def check_processes():
    # Exemplo simples: checar se processos importantes estão rodando
    procs = [p.name().lower() for p in psutil.process_iter()]
    important = ['python']
    for imp in important:
        if any(imp in p for p in procs):
            logger.info(f"Processo '{imp}' está rodando")
        else:
            logger.warning(f"Processo '{imp}' NÃO está rodando!")

def check_logs_activity():
    paths = {
        'Web (Flask)': '/app/app.log',
        'Snort': '/var/log/snort/alert'
    }

    for name, path in paths.items():
        try:
            last_mod = os.path.getmtime(path)
            seconds_since_mod = time.time() - last_mod

            if seconds_since_mod < 10:
                logger.info(f"Log de {name} está ativo (modificado há {int(seconds_since_mod)}s)")
            else:
                logger.warning(f"Log de {name} inativo (última modificação há {int(seconds_since_mod)}s)")
        except FileNotFoundError:
            logger.error(f"Arquivo de log de {name} não encontrado: {path}")


def main():
    while True:
        check_cpu_ram()
        check_open_ports()
        check_processes()
        check_logs_activity()
        logger.info("____________________________________________________________")
        time.sleep(10)

if __name__ == "__main__":
    main()
