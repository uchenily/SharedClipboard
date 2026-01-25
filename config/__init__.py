from . import default

class Config:
    def __init__(self):
        for key in dir(default):
            if key.isupper():
                setattr(self, key, getattr(default, key))

config = Config()
