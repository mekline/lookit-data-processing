import os
import argparse
from dotenv import load_dotenv

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', type=str)
args, _ = parser.parse_known_args()

dotenv_path = os.path.join(os.path.dirname(__file__), args.config or '.env')
load_dotenv(dotenv_path)

OSF_ACCESS_TOKEN = os.environ.get('OSF_ACCESS_TOKEN')
JAM_NAMESPACE = os.environ.get('JAMDB_NAMESPACE')
JAM_HOST = os.environ.get('JAMDB_URL')
# Used for SENDGRID_CLIENT script. Some Jam scripts may not use this key.
SENDGRID_KEY = os.environ.get('SENDGRID_KEY')
