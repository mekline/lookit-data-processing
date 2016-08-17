import os

from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

OSF_ACCESS_TOKEN = os.environ.get('OSF_ACCESS_TOKEN')
SENDGRID_KEY = os.environ.get('SENDGRID_KEY')
JAM_NAMESPACE = os.environ.get('JAM_NAMESPACE')
JAM_HOST = os.environ.get('JAM_URL')
