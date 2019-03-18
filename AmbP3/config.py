import yaml

DEFAULT_PORT = 5403
DEFAULT_IP = '127.0.0.1'
DEFAULT_CONFIG_FILE = 'conf.yaml'
DefaultConfig = {"ip": DEFAULT_IP, "port": DEFAULT_PORT, "file": False, "debug_file": False, 'mysql_backend': False}


class Config:
    def __init__(self, config_file=DEFAULT_CONFIG_FILE):
        self.conf = DefaultConfig
        try:
            with open(config_file, 'rb') as config_file_handler:
                config_from_file = yaml.safe_load(config_file_handler)
        except IOError:
            print("default config")
            config_from_file = {}
        if isinstance(config_from_file, dict):
            conf = {**DefaultConfig,  **config_from_file}
            self.conf = conf
            self.ip = conf['ip']
            self.port = conf['port']
            self.file = conf['file']
            self.debug_file = conf['debug_file']
