import sys
from decouple import config

try:
    HOST_IPS = config("HOST_IPS").split(',')
    SSH_USER = config("SSH_USER")
    SSH_KEY_PATH = config("SSH_KEY_PATH")
    SQLITE_DB_PATH = config("SQLITE_DB_PATH")
except Exception as e:
    print(f"Error: Missing configuration in .env file. Please check your settings. Details: {e}")
    sys.exit(1)

LOG_SOURCES = {
    'syslog': '/var/log/syslog',
    'auth': '/var/log/auth.log'
}
