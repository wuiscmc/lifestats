import yaml
import os


def _config_file_path():
    main_base = os.path.dirname(__file__)
    return os.path.join(main_base, "..", "config.yml")

environment = os.getenv('ENV', 'development')
config = yaml.load(open(_config_file_path(), 'r'))[environment]