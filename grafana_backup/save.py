from grafana_backup.api_checks import main as api_checks
from grafana_backup.save_alert_rules import main as save_alert_rules
from grafana_backup.save_dashboards import main as save_dashboards
from grafana_backup.save_datasources import main as save_datasources
from grafana_backup.save_folders import main as save_folders
from grafana_backup.save_alert_channels import main as save_alert_channels
from grafana_backup.archive import main as archive
from grafana_backup.save_library_elements import main as save_library_elements
from grafana_backup.azure_storage_upload import main as azure_storage_upload
from grafana_backup.commons import print_horizontal_line
import sys


def main(args, settings):
    arg_components = args.get('--components', False)
    arg_no_archive = args.get('--no-archive', False)

    backup_functions = {'dashboards': save_dashboards,
                        'datasources': save_datasources,
                        'folders': save_folders,
                        'alert-channels': save_alert_channels,
                        'library-elements': save_library_elements,
                        'alert-rules': save_alert_rules,
                        }

    (status,
     json_resp,
     dashboard_uid_support,
     datasource_uid_support,
     paging_support,
     contact_point_support) = api_checks(settings)

    settings.update({'DASHBOARD_UID_SUPPORT': dashboard_uid_support})
    settings.update({'DATASOURCE_UID_SUPPORT': datasource_uid_support})
    settings.update({'PAGING_SUPPORT': paging_support})
    settings.update({'CONTACT_POINT_SUPPORT': contact_point_support})

    # Do not continue if API is unavailable or token is not valid
    if not status == 200:
        print("grafana server status is not ok: {0}".format(json_resp))
        sys.exit(1)

    if arg_components:
        arg_components_list = arg_components.replace("_", "-").split(',')

        # Backup only the components that provided via an argument
        for backup_function in arg_components_list:
            backup_functions[backup_function](args, settings)
    else:
        # Backup every component
        for backup_function in backup_functions.keys():
            backup_functions[backup_function](args, settings)

    azure_storage_container_name = settings.get('AZURE_STORAGE_CONTAINER_NAME')

    if not arg_no_archive:
        archive(args, settings)

    if azure_storage_container_name:
        print('Upload archives to Azure Storage:')
        azure_storage_upload(args, settings)
