import logging
from grafana_backup.azure_workload_identity import get_azure_storage_client, AzureAuthenticationError

logger = logging.getLogger(__name__)


def main(args, settings):
    """
    Upload backup archive to Azure Storage using secure authentication
    Supports: Workload Identity, Managed Identity, DefaultAzureCredential chain
    """
    azure_storage_container_name = settings.get('AZURE_STORAGE_CONTAINER_NAME')
    
    if not azure_storage_container_name:
        logger.error("AZURE_STORAGE_CONTAINER_NAME not configured")
        return False

    backup_dir = settings.get('BACKUP_DIR')
    timestamp = settings.get('TIMESTAMP')
    
    # Extract storage account name from various sources
    storage_account_name = _get_storage_account_name(settings)
    if not storage_account_name:
        logger.error("Could not determine Azure Storage account name")
        return False

    azure_file_name = '{0}.tar.gz'.format(timestamp)
    archive_file = '{0}/{1}'.format(backup_dir, azure_file_name)

    try:
        # Use secure authentication methods
        blob_service_client = get_azure_storage_client(
            storage_account_name=storage_account_name,
            container_name=azure_storage_container_name,
            settings=settings
        )
        
        # Upload the file
        blob_client = blob_service_client.get_blob_client(
            container=azure_storage_container_name, 
            blob=azure_file_name
        )
        
        with open(archive_file, 'rb') as data:
            blob_client.upload_blob(data, overwrite=True)
            
        logger.info(f"Successfully uploaded {azure_file_name} to Azure Storage container {azure_storage_container_name}")
        print("Upload to Azure Storage was successful")
        return True
        
    except FileNotFoundError:
        logger.error(f"Archive file not found: {archive_file}")
        print("The file was not found")
        return False
        
    except AzureAuthenticationError as e:
        logger.error(f"Azure authentication failed: {e}")
        print(f"Azure authentication failed: {e}")
        return False
        
    except Exception as e:
        logger.error(f"Upload to Azure Storage failed: {e}")
        print(f"Upload failed: {str(e)}")
        return False


def _get_storage_account_name(settings):
    """Extract storage account name from various configuration sources"""
    
    # Try explicit setting first
    account_name = settings.get('AZURE_STORAGE_ACCOUNT_NAME')
    if account_name:
        return account_name
        
    # Try to extract from connection string (legacy)
    connection_string = settings.get('AZURE_STORAGE_CONNECTION_STRING')
    if connection_string:
        try:
            # Parse connection string to extract account name
            parts = dict(part.split('=', 1) for part in connection_string.split(';') if '=' in part)
            return parts.get('AccountName')
        except Exception:
            logger.warning("Could not parse storage account name from connection string")
    
    # Try environment variable
    import os
    return os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
