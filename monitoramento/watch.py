
import psutil
import logging
from logging.handlers import RotatingFileHandler
import time
import os

class SystemMonitor:
    """
    Uma classe para monitorar o estado do sistema.
    - Verifica CPU, RAM, portas e processos.
    - Verifica a atividade (tempo de modificação) de todos os outros logs.
    """

    def __init__(self, paths_to_monitor, interval_seconds=10):
        """
        Inicializa o monitor.
        """
        self.paths = paths_to_monitor
        self.interval = interval_seconds
        self.log_states = {}
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """Configura e retorna uma instância do logger."""
        logger = logging.getLogger("monitor_classe")
        
        if logger.hasHandlers():
            return logger
            
        logger.setLevel(logging.INFO)
        handler = RotatingFileHandler("monitor.log", maxBytes=5*1024*1024, backupCount=3)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        return logger

    def _clear_file_content(self, filepath):
        """Limpa o conteúdo de um arquivo."""
        try:
            dir_name = os.path.dirname(filepath)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            with open(filepath, 'w') as f:
                pass
            self.logger.info(f"Arquivo limpo com sucesso: {filepath}")
        except IOError as e:
            self.logger.error(f"Erro ao limpar o arquivo {filepath}: {e}")

    def _check_cpu_ram(self):
        """Verifica o uso de CPU e RAM."""
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        self.logger.info(f"Uso CPU: {cpu}%, Uso RAM: {ram}%")
        if cpu > 80: self.logger.warning(f"CPU alta: {cpu}%")
        if ram > 80: self.logger.warning(f"RAM alta: {ram}%")

    def _check_open_ports(self):
        """Verifica as portas de rede abertas."""
        try:
            conns = psutil.net_connections(kind='inet')
            ports = set(conn.laddr.port for conn in conns if conn.status == 'LISTEN')
            self.logger.info(f"Portas abertas (escutando): {sorted(ports)}")
        except psutil.AccessDenied:
            self.logger.warning("Acesso negado ao verificar portas. Tente como root/administrador.")

    def _check_processes(self):
        """Verifica se processos importantes estão em execução."""
        try:
            procs = [p.name().lower() for p in psutil.process_iter(['name'])]
            important = ['python']
            for imp in important:
                if any(imp in p for p in procs):
                    self.logger.info(f"Processo '{imp}' está rodando.")
                else:
                    self.logger.warning(f"Processo '{imp}' NÃO está rodando!")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    def _check_all_logs(self):
        """
        Verifica todos os logs: lê o conteúdo do server.log e a atividade dos outros.
        """
        for name, path in self.paths.items():
            try:
                if name == 'Web Error':
                    if not os.path.exists(path): continue

                    stats = os.stat(path)
                    current_inode = stats.st_ino
                    current_size = stats.st_size
                    last_pos, last_inode = self.log_states.get(path, (0, 0))

                    if current_inode != last_inode or current_size < last_pos:
                        self.logger.info(f"Log '{name}' foi rotacionado/truncado. Lendo do início.")
                        last_pos = 0

                    if current_size > last_pos:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            f.seek(last_pos)
                            new_lines = f.readlines()
                            if new_lines:
                                self.logger.error(f"--- Novas entradas detectadas em {name} ---")
                                for line in new_lines:
                                    self.logger.error(line.strip())
                            last_pos = f.tell()
                    
                    self.log_states[path] = (last_pos, current_inode)
                
                else:
                    stats = os.stat(path)
                    last_mod = stats.st_mtime
                    seconds_since_mod = time.time() - last_mod

                    if seconds_since_mod < self.interval + 2:
                        self.logger.info(f"Log de '{name}' está ATIVO (modificado há {int(seconds_since_mod)}s)")
                    else:
                        self.logger.warning(f"Log de '{name}' está INATIVO (última modificação há {int(seconds_since_mod)}s)")

            except FileNotFoundError:
                self.logger.error(f"Arquivo de log de '{name}' não encontrado em: {path}")
            except Exception as e:
                self.logger.error(f"Erro inesperado ao processar '{name}': {e}")

    def run(self):
        """Inicia o loop principal de monitoramento."""
        self.logger.info("--- Monitoramento iniciado. Pressione Ctrl+C para parar. ---")

        try:
            while True:
                self._check_cpu_ram()
                self._check_open_ports()
                self._check_processes()
                self._check_all_logs()
                self.logger.info("_"*70)
                time.sleep(self.interval)
        except KeyboardInterrupt:
            self.logger.info("\nMonitoramento interrompido pelo usuário. Encerrando.")


if __name__ == "__main__":
    log_paths_config = {
        'Web Error': './app/log/server.log',
        'Web Access': './app/log/access.log',
        'Snort Alerts': './var/log/snort/alert',
        'MySQL Queries': './var/lib/mysql/query.log',
        'Network Capture': './captures/traffic.pcap',
    }

    monitor_setup = SystemMonitor(log_paths_config)
    for path in log_paths_config.values():
        monitor_setup._clear_file_content(path)
    monitor = SystemMonitor(paths_to_monitor=log_paths_config, interval_seconds=10)
    time.sleep(5)
    monitor.run()
