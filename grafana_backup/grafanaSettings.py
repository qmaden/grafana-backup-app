import base64
import json
import os
from datetime import datetime
from grafana_backup.commons import load_config


def main(config_path):
    # Load config from optional configuration file located at ~/.grafana-backup.json
    # or load defaults from example config stored in grafanaSettings.json
    # environment variables can override settings as well and are top of the hierarchy

    config_dict = {}

    config = load_config(config_path)

    grafana_url = config.get('grafana', {}).get('url', '')
    grafana_token = config.get('grafana', {}).get('token', '')
    grafana_search_api_limit = config.get('grafana', {}).get('search_api_limit', 5000)
    grafana_default_user_password = config.get('grafana', {}).get('default_user_password', '00000000')
    grafana_version = config.get('grafana', {}).get('version', None)

    debug = config.get('general', {}).get('debug', True)
    api_health_check = config.get('general', {}).get('api_health_check', True)
    api_auth_check = config.get('general', {}).get('api_auth_check', True)
    verify_ssl = config.get('general', {}).get('verify_ssl', False)
    client_cert = config.get('general', {}).get('client_cert', None)
    backup_dir = config.get('general', {}).get('backup_dir', '_OUTPUT_')
    backup_file_format = config.get('general', {}).get('backup_file_format', '%Y%m%d%H%M')
    uid_dashboard_slug_suffix = config.get('general', {}).get('uid_dashboard_slug_suffix', False)
    pretty_print = config.get('general', {}).get('pretty_print', False)

    # Cloud storage settings - Azure
    azure_config = config.get('azure', {})
    azure_storage_container_name = azure_config.get('container_name', '')
    azure_storage_connection_string = azure_config.get('connection_string', '')
    azure_storage_account_name = azure_config.get('storage_account_name', '')
    azure_managed_identity_client_id = azure_config.get('managed_identity_client_id', '')

    admin_account = config.get('grafana', {}).get('admin_account', '')
    admin_password = config.get('grafana', {}).get('admin_password', '')

    GRAFANA_URL = os.getenv('GRAFANA_URL', grafana_url)
    TOKEN = os.getenv('GRAFANA_TOKEN', grafana_token)
    SEARCH_API_LIMIT = os.getenv('SEARCH_API_LIMIT', grafana_search_api_limit)
    DEFAULT_USER_PASSWORD = os.getenv('DEFAULT_USER_PASSWORD', grafana_default_user_password)
    GRAFANA_VERSION = os.getenv('GRAFANA_VERSION', grafana_version)

    AZURE_STORAGE_CONTAINER_NAME = os.getenv('AZURE_STORAGE_CONTAINER_NAME', azure_storage_container_name)
    AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING', azure_storage_connection_string)
    AZURE_STORAGE_ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT_NAME', azure_storage_account_name)
    AZURE_MANAGED_IDENTITY_CLIENT_ID = os.getenv('AZURE_MANAGED_IDENTITY_CLIENT_ID', azure_managed_identity_client_id)

    ADMIN_ACCOUNT = os.getenv('GRAFANA_ADMIN_ACCOUNT', admin_account)
    ADMIN_PASSWORD = os.getenv('GRAFANA_ADMIN_PASSWORD', admin_password)
    GRAFANA_BASIC_AUTH = os.getenv('GRAFANA_BASIC_AUTH', None)

    DEBUG = os.getenv('DEBUG', debug)
    if isinstance(DEBUG, str):
        DEBUG = json.loads(DEBUG.lower())  # convert environment variable string to bool

    VERIFY_SSL = os.getenv('VERIFY_SSL', verify_ssl)
    if isinstance(VERIFY_SSL, str) and VERIFY_SSL.lower() in ['true', 'false']:
        VERIFY_SSL = json.loads(VERIFY_SSL.lower())  # convert environment variable string to bool

    API_HEALTH_CHECK = os.getenv('API_HEALTH_CHECK', api_health_check)
    if isinstance(API_HEALTH_CHECK, str):
        API_HEALTH_CHECK = json.loads(API_HEALTH_CHECK.lower())  # convert environment variable string to bool

    API_AUTH_CHECK = os.getenv('API_AUTH_CHECK', api_auth_check)
    if isinstance(API_AUTH_CHECK, str):
        API_AUTH_CHECK = json.loads(API_AUTH_CHECK.lower())  # convert environment variable string to bool

    CLIENT_CERT = os.getenv('CLIENT_CERT', client_cert)

    BACKUP_DIR = os.getenv('BACKUP_DIR', backup_dir)
    BACKUP_FILE_FORMAT = os.getenv('BACKUP_FILE_FORMAT', backup_file_format)

    UID_DASHBOARD_SLUG_SUFFIX = os.getenv('UID_DASHBOARD_SLUG_SUFFIX', uid_dashboard_slug_suffix)
    if isinstance(UID_DASHBOARD_SLUG_SUFFIX, str):
        UID_DASHBOARD_SLUG_SUFFIX = json.loads(UID_DASHBOARD_SLUG_SUFFIX.lower())  # convert environment variable string to bool

    PRETTY_PRINT = os.getenv('PRETTY_PRINT', pretty_print)
    if isinstance(PRETTY_PRINT, str):
        PRETTY_PRINT = json.loads(PRETTY_PRINT.lower())  # convert environment variable string to bool

    EXTRA_HEADERS = dict(
        h.split(':') for h in os.getenv('GRAFANA_HEADERS', '').split(',') if 'GRAFANA_HEADERS' in os.environ)

    if TOKEN:
        HTTP_GET_HEADERS = {'Authorization': 'Bearer ' + TOKEN}
        HTTP_POST_HEADERS = {'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json'}
    else:
        HTTP_GET_HEADERS = {}
        HTTP_POST_HEADERS = {'Content-Type': 'application/json'}

    for k, v in EXTRA_HEADERS.items():
        HTTP_GET_HEADERS.update({k: v})
        HTTP_POST_HEADERS.update({k: v})

    TIMESTAMP = datetime.today().strftime(BACKUP_FILE_FORMAT)

    config_dict['GRAFANA_URL'] = GRAFANA_URL
    config_dict['GRAFANA_VERSION'] = GRAFANA_VERSION
    config_dict['GRAFANA_ADMIN_ACCOUNT'] = ADMIN_ACCOUNT
    config_dict['GRAFANA_ADMIN_PASSWORD'] = ADMIN_PASSWORD

    if not GRAFANA_BASIC_AUTH and (ADMIN_ACCOUNT and ADMIN_PASSWORD):
        GRAFANA_BASIC_AUTH = base64.b64encode(
            "{0}:{1}".format(ADMIN_ACCOUNT, ADMIN_PASSWORD).encode('utf8')
        ).decode('utf8')

    if GRAFANA_BASIC_AUTH:
        HTTP_GET_HEADERS_BASIC_AUTH = HTTP_GET_HEADERS.copy()
        HTTP_GET_HEADERS_BASIC_AUTH.update({'Authorization': 'Basic {0}'.format(GRAFANA_BASIC_AUTH)})
        HTTP_POST_HEADERS_BASIC_AUTH = HTTP_POST_HEADERS.copy()
        HTTP_POST_HEADERS_BASIC_AUTH.update({'Authorization': 'Basic {0}'.format(GRAFANA_BASIC_AUTH)})
    else:
        HTTP_GET_HEADERS_BASIC_AUTH = None
        HTTP_POST_HEADERS_BASIC_AUTH = None

    config_dict['DEFAULT_USER_PASSWORD'] = DEFAULT_USER_PASSWORD
    config_dict['TOKEN'] = TOKEN
    config_dict['SEARCH_API_LIMIT'] = SEARCH_API_LIMIT
    config_dict['DEBUG'] = DEBUG
    config_dict['API_HEALTH_CHECK'] = API_HEALTH_CHECK
    config_dict['API_AUTH_CHECK'] = API_AUTH_CHECK
    config_dict['VERIFY_SSL'] = VERIFY_SSL
    config_dict['CLIENT_CERT'] = CLIENT_CERT
    config_dict['BACKUP_DIR'] = BACKUP_DIR
    config_dict['BACKUP_FILE_FORMAT'] = BACKUP_FILE_FORMAT
    config_dict['PRETTY_PRINT'] = PRETTY_PRINT
    config_dict['UID_DASHBOARD_SLUG_SUFFIX'] = UID_DASHBOARD_SLUG_SUFFIX
    config_dict['EXTRA_HEADERS'] = EXTRA_HEADERS
    config_dict['HTTP_GET_HEADERS'] = HTTP_GET_HEADERS
    config_dict['HTTP_POST_HEADERS'] = HTTP_POST_HEADERS
    config_dict['HTTP_GET_HEADERS_BASIC_AUTH'] = HTTP_GET_HEADERS_BASIC_AUTH
    config_dict['HTTP_POST_HEADERS_BASIC_AUTH'] = HTTP_POST_HEADERS_BASIC_AUTH
    config_dict['TIMESTAMP'] = TIMESTAMP
    config_dict['AZURE_STORAGE_CONTAINER_NAME'] = AZURE_STORAGE_CONTAINER_NAME
    config_dict['AZURE_STORAGE_CONNECTION_STRING'] = AZURE_STORAGE_CONNECTION_STRING
    config_dict['AZURE_STORAGE_ACCOUNT_NAME'] = AZURE_STORAGE_ACCOUNT_NAME
    config_dict['AZURE_MANAGED_IDENTITY_CLIENT_ID'] = AZURE_MANAGED_IDENTITY_CLIENT_ID

    return config_dict
