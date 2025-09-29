from grafana_backup.api_checks import main as api_checks
from grafana_backup.create_folder import main as create_folder
from grafana_backup.create_datasource import main as create_datasource
from grafana_backup.create_dashboard import main as create_dashboard
from grafana_backup.create_alert_channel import main as create_alert_channel
from grafana_backup.create_alert_rule import main as create_alert_rule
from grafana_backup.create_library_element import main as create_library_element
from grafana_backup.azure_storage_download import main as azure_storage_download
from glob import glob
import sys
import tarfile
import tempfile
import os
import shutil
import fnmatch
import collections


def main(args, settings):
    def open_compressed_backup(compressed_backup):
        try:
            tar = tarfile.open(fileobj=compressed_backup, mode='r:gz')
            return tar
        except Exception as e:
            print(str(e))
            sys.exit(1)

    arg_archive_file = args.get('<archive_file>', None)
    azure_storage_container_name = settings.get('AZURE_STORAGE_CONTAINER_NAME')

    (status, json_resp, dashboard_uid_support, datasource_uid_support,
     paging_support, contact_point_support) = api_checks(settings)
    settings.update({'CONTACT_POINT_SUPPORT': contact_point_support})

    # Do not continue if API is unavailable or token is not valid
    if not status == 200:
        sys.exit(1)

    # Use tar data stream if Azure Storage container name is specified
    if azure_storage_container_name:
        print('Download archives from Azure:')
        azure_storage_data = azure_storage_download(args, settings)
        tar = open_compressed_backup(azure_storage_data)

    else:
        try:
            tarfile.is_tarfile(name=arg_archive_file)
        except IOError as e:
            print(str(e))
            sys.exit(1)
        try:
            tar = tarfile.open(name=arg_archive_file, mode='r:gz')
        except Exception as e:
            print(str(e))
            sys.exit(1)

    # TODO:
    # Shell game magic warning: restore_function keys require the 's'
    # to be removed in order to match file extension names...
    restore_functions = collections.OrderedDict()
    # Folders must be restored before Library-Elements
    restore_functions['folder'] = create_folder
    restore_functions['datasource'] = create_datasource
    # Library-Elements must be restored before dashboards
    restore_functions['library_element'] = create_library_element
    restore_functions['dashboard'] = create_dashboard
    restore_functions['alert_channel'] = create_alert_channel
    restore_functions['alert_rule'] = create_alert_rule

    if sys.version_info >= (3,):
        with tempfile.TemporaryDirectory() as tmpdir:
            tar.extractall(tmpdir)
            tar.close()
            restore_components(args, settings, restore_functions, tmpdir)
    else:
        tmpdir = tempfile.mkdtemp()
        tar.extractall(tmpdir)
        tar.close()
        restore_components(args, settings, restore_functions, tmpdir)
        try:
            shutil.rmtree(tmpdir)
        except OSError as e:
            print("Error: %s : %s" % (tmpdir, e.strerror))


def restore_components(args, settings, restore_functions, tmpdir):
    arg_components = args.get('--components', [])

    if arg_components:
        arg_components_list = arg_components.replace("-", "_").split(',')

        # Restore only the components that provided via an argument
        # but must also exist in extracted archive
        # NOTICE: ext[:-1] cuts the 's' off in order to match the file extension name to be restored...
        for ext in arg_components_list:
            if sys.version_info >= (3,):
                for file_path in glob('{0}/**/*.{1}'.format(tmpdir, ext[:-1]), recursive=True):
                    print('restoring {0}: {1}'.format(ext, file_path))
                    restore_functions[ext[:-1]](args, settings, file_path)
            else:
                for root, dirnames, filenames in os.walk('{0}'.format(tmpdir)):
                    for filename in fnmatch.filter(filenames, '*.{0}'.format(ext[:-1])):
                        file_path = os.path.join(root, filename)
                        print('restoring {0}: {1}'.format(ext, file_path))
                        restore_functions[ext[:-1]](args, settings, file_path)
    else:
        # Restore every component included in extracted archive
        for ext in restore_functions.keys():
            if sys.version_info >= (3,):
                for file_path in glob('{0}/**/*.{1}'.format(tmpdir, ext), recursive=True):
                    print('restoring {0}: {1}'.format(ext, file_path))
                    restore_functions[ext](args, settings, file_path)
            else:
                for root, dirnames, filenames in os.walk('{0}'.format(tmpdir)):
                    for filename in fnmatch.filter(filenames, '*.{0}'.format(ext)):
                        file_path = os.path.join(root, filename)
                        print('restoring {0}: {1}'.format(ext, file_path))
                        restore_functions[ext](args, settings, file_path)
