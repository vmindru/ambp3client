import yaml

DefaultConfig = {"ip": "127.0.0.1", "port": 5403, "file": False}
DEFAULT_CONFIG_FILE = 'conf.yaml'


class Config:
    def __init__(self, config_file=DEFAULT_CONFIG_FILE):
        self.conf = DefaultConfig
        try:
            with open(config_file, 'rb') as config_file_handler:
                config_from_file = yaml.load(config_file_handler)
        except IOError:
            print("default config")
            config_from_file = {}
        if isinstance(config_from_file, dict):
            conf = {**DefaultConfig,  **config_from_file}
            self.ip = conf['ip']
            self.port = conf['port']
            self.file = conf['file']
