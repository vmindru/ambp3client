import yaml
from argparse import ArgumentParser

DEFAULT_PORT = 5403
DEFAULT_IP = '127.0.0.1'
DEFAULT_CONFIG_FILE = 'conf.yaml'
DefaultConfig = {"ip": DEFAULT_IP, "port": DEFAULT_PORT, "file":
                 False, "debug_file": False, 'mysql_backend': False,
                 'mysql_host': '127.0.0.1', 'mysql_port': 3306}


class Config:
    def __init__(self, cli_args, config_file=DEFAULT_CONFIG_FILE):
        self.conf = DefaultConfig
        try:
            with open(cli_args.config_file, 'rb') as config_file_handler:
                config_from_file = yaml.safe_load(config_file_handler)
        except IOError:
            config_from_file = {}
        if isinstance(config_from_file, dict):
            cli_args_dict = cli_args.__dict__
            conf = {**DefaultConfig,  **config_from_file}
            conf = {**cli_args_dict, **conf}
            conf = {**conf, **cli_args_dict}
            print(f"args: {cli_args_dict}")
            print(f"CONF: {conf}")
            self.conf = conf
            self.ip = conf['ip']
            self.port = conf['port']
            self.file = conf['file']
            self.debug_file = conf['debug_file']


def get_args(PORT=DEFAULT_PORT, IP=DEFAULT_IP, config_file=DEFAULT_CONFIG_FILE):
    """ args that overwrite AmbP3.config """
    args = ArgumentParser()
    args.add_argument("-f", "--config", dest='config_file', default=config_file)
    args.add_argument("-i", "--ip", help="AMB decoder IP")
    args.add_argument("-p", "--port",  dest='port', type=int, help="AMB decoder PORT")
    args.add_argument("-l", "--log-file", dest='file', help="amb msgs log file")
    cli_args = args.parse_args()
    config = Config(cli_args)
    return config
