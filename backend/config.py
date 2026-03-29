import os

class Config:
    DEFAULT_WG_PATH = '/etc/wireguard/'
    WG_PATH = os.environ.get('WG_PATH', DEFAULT_WG_PATH)
    HOST = '0.0.0.0'
    PORT = 5001
    DEBUG = True
