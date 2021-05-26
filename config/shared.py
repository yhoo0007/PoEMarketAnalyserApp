import os


LEAGUE = 'ultimatum'
LEAGUE_CAP = 'Ultimatum'

DEFAULT_POE_HEADERS = {
    'accept': 'application/json',
    'Content-Type': 'application/json',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36'
}

DATA_DIR = f'./data/{LEAGUE}'

FIREBASE_CONFIG = {
        'apiKey': os.environ.get('apiKey'),
        'authDomain': os.environ.get('authDomain'),
        'databaseURL': os.environ.get('databaseURL'),
        'storageBucket': os.environ.get('storageBucket'),
        "serviceAccount": {
                "type": os.environ.get('type'),
                "project_id": os.environ.get('project_id'),
                "private_key_id": os.environ.get('private_key_id'),
                "private_key": os.environ.get('private_key'),
                "client_email": os.environ.get('client_email'),
                "client_id": os.environ.get('client_id'),
                "auth_uri": os.environ.get('auth_uri'),
                "token_uri": os.environ.get('token_uri'),
                "auth_provider_x509_cert_url": os.environ.get('auth_provider_x509_cert_url'),
                "client_x509_cert_url": os.environ.get('client_x509_cert_url'),
            }
    }
