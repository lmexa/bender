import yaml


class ConfigBender():
    def __init__(self, values):
        super().__init__()
        self.read(values)

    @classmethod
    def load(cls, path):
        values = yaml.load(open(path), Loader=yaml.FullLoader)
        return cls(values)

    def read(self, values):
        self.log = ConfigLog(values['log'])
        self.token = values['token']
        self.proxy = values.get('proxy')
        self.scopes = values['scopes']
        self.credentials = values['credentials']
        self.token_file = values.get('token_file')
        self.job_interval = values.get('job_interval', 60)
        self.reset_state = values.get('reset_state')


class ConfigLog:
    def __init__(self, values):
        super().__init__()
        self.read(values)

    def read(self, values):
        self.filename = values['filename']
        self.format = values.get('format', '%(asctime)s (%(name)s/%(threadName)s) [%(levelname)s]: %(message)s')
        self.datefmt = values.get('datefmt', '%Y-%m-%d %H:%M:%S')
        self.level = values.get('level', 'INFO')

    def to_dict(self):
        res = {}
        for name, obj in self.__dict__.items():
            res[name] = obj
        return res
