import io
import logging
from grafana_backup.azure_workload_identity import get_azure_storage_client, AzureAuthenticationError

logger = logging.getLogger(__name__)


def main(args, settings):
    """
    Download backup archive from Azure Storage using secure authentication
    Supports: Workload Identity, Managed Identity, DefaultAzureCredential chain
    """
    arg_archive_file = args.get('<archive_file>', None)
    
    if not arg_archive_file:
        logger.error("Archive file name not provided")
        return False

    azure_storage_container_name = settings.get('AZURE_STORAGE_CONTAINER_NAME')
    
    if not azure_storage_container_name:
        logger.error("AZURE_STORAGE_CONTAINER_NAME not configured") 
        return False

    # Extract storage account name from various sources
    storage_account_name = _get_storage_account_name(settings)
    if not storage_account_name:
        logger.error("Could not determine Azure Storage account name")
        return False

    try:
        # Use secure authentication methods
        blob_service_client = get_azure_storage_client(
            storage_account_name=storage_account_name,
            container_name=azure_storage_container_name,
            settings=settings
        )
        
        # Download the file
        blob_client = blob_service_client.get_blob_client(
            container=azure_storage_container_name, 
            blob=arg_archive_file
        )
        
        azure_storage_bytes = blob_client.download_blob().readall()
        azure_storage_data = io.BytesIO(azure_storage_bytes)
        
        logger.info(f"Successfully downloaded {arg_archive_file} from Azure Storage container {azure_storage_container_name}")
        print("Download from Azure Storage was successful")
        return azure_storage_data
        
    except AzureAuthenticationError as e:
        logger.error(f"Azure authentication failed: {e}")
        print(f"Azure authentication failed: {e}")
        return False
        
    except Exception as e:
        logger.error(f"Download from Azure Storage failed: {e}")
        print(f"Download failed: {str(e)}")
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
