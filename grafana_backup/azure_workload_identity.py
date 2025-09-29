"""
Azure Workload Identity Authentication Module

Implements secure authentication using:
1. Azure Workload Identity (OIDC)
2. Managed Identity
3. DefaultAzureCredential chain
"""
import os
import logging
from typing import Optional, Union
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential, WorkloadIdentityCredential
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ClientAuthenticationError, ServiceRequestError
import time
import random
from functools import wraps

logger = logging.getLogger(__name__)


class AzureAuthenticationError(Exception):
    """Custom exception for Azure authentication failures"""
    pass


def retry_with_exponential_backoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """Decorator for exponential backoff retry logic"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (ServiceRequestError, ClientAuthenticationError) as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Max retries exceeded. Last error: {e}")
                        raise
                    
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay:.2f}s. Error: {e}")
                    time.sleep(delay)
            return func(*args, **kwargs)
        return wrapper
    return decorator


class AzureStorageAuthenticator:
    """
    Handles Azure Storage authentication using multiple methods:
    1. Workload Identity (preferred for K8s)
    2. Managed Identity
    3. DefaultAzureCredential chain
    4. Connection string (fallback, deprecated)
    """
    
    def __init__(self, storage_account_name: str, container_name: str, settings: dict):
        self.storage_account_name = storage_account_name
        self.container_name = container_name
        self.settings = settings
        self._credential = None
        self._client = None
        
    def _get_credential(self) -> Union[DefaultAzureCredential, ManagedIdentityCredential, WorkloadIdentityCredential]:
        """
        Get Azure credential using authentication hierarchy:
        1. Workload Identity (if in K8s with OIDC token)
        2. User-assigned Managed Identity (if client_id provided)
        3. System-assigned Managed Identity 
        4. DefaultAzureCredential chain
        """
        if self._credential:
            return self._credential
            
        # Check for Workload Identity environment
        if self._is_workload_identity_available():
            logger.info("Using Azure Workload Identity authentication")
            self._credential = WorkloadIdentityCredential(
                tenant_id=os.getenv('AZURE_TENANT_ID'),
                client_id=os.getenv('AZURE_CLIENT_ID'),
                token_file_path=os.getenv('AZURE_FEDERATED_TOKEN_FILE', 
                                        '/var/run/secrets/azure/tokens/azure-identity-token')
            )
            return self._credential
            
        # Check for user-assigned managed identity
        managed_identity_client_id = (
            self.settings.get('AZURE_MANAGED_IDENTITY_CLIENT_ID') or 
            os.getenv('AZURE_CLIENT_ID')
        )
        
        if managed_identity_client_id:
            logger.info(f"Using user-assigned Managed Identity: {managed_identity_client_id}")
            self._credential = ManagedIdentityCredential(client_id=managed_identity_client_id)
            return self._credential
            
        # Use DefaultAzureCredential (tries system-assigned MI, then other methods)
        logger.info("Using DefaultAzureCredential authentication chain")
        self._credential = DefaultAzureCredential(
            exclude_interactive_browser_credential=True,  # Disable for server environments
            exclude_visual_studio_code_credential=True,   # Disable for server environments  
            exclude_visual_studio_credential=True,        # Disable for server environments
            exclude_azure_cli_credential=False,           # Allow for local development
            exclude_managed_identity_credential=False,    # Allow managed identity
            exclude_environment_credential=False          # Allow service principal via env vars
        )
        return self._credential
        
    def _is_workload_identity_available(self) -> bool:
        """Check if running in workload identity enabled environment"""
        required_env_vars = ['AZURE_TENANT_ID', 'AZURE_CLIENT_ID']
        token_file = os.getenv('AZURE_FEDERATED_TOKEN_FILE', 
                              '/var/run/secrets/azure/tokens/azure-identity-token')
        
        return (
            all(os.getenv(var) for var in required_env_vars) and
            os.path.exists(token_file)
        )
    
    @retry_with_exponential_backoff(max_retries=3)
    def get_blob_service_client(self) -> BlobServiceClient:
        """Get authenticated BlobServiceClient with retry logic"""
        if self._client:
            return self._client
            
        # Try modern authentication first
        try:
            credential = self._get_credential()
            account_url = f"https://{self.storage_account_name}.blob.core.windows.net"
            self._client = BlobServiceClient(account_url=account_url, credential=credential)
            
            # Test the connection
            self._test_authentication()
            logger.info("Successfully authenticated with Azure Storage using modern authentication")
            return self._client
            
        except Exception as e:
            logger.warning(f"Modern authentication failed: {e}")
            
            # Fallback to connection string (deprecated)
            connection_string = self.settings.get('AZURE_STORAGE_CONNECTION_STRING')
            if connection_string:
                logger.warning("Falling back to connection string authentication (deprecated)")
                self._client = BlobServiceClient.from_connection_string(connection_string)
                self._test_authentication()
                return self._client
            
            raise AzureAuthenticationError(
                "All authentication methods failed. Ensure proper Azure credentials are configured."
            )
    
    def _test_authentication(self) -> None:
        """Test authentication by listing containers"""
        try:
            # Test authentication by checking if container exists or can be accessed
            container_client = self._client.get_container_client(self.container_name)
            container_client.get_container_properties()
            logger.info(f"Successfully verified access to container: {self.container_name}")
        except Exception as e:
            logger.error(f"Authentication test failed: {e}")
            raise AzureAuthenticationError(f"Cannot access container {self.container_name}: {e}")


def get_azure_storage_client(storage_account_name: str, container_name: str, settings: dict) -> BlobServiceClient:
    """
    Factory function to get authenticated Azure Storage client
    
    Args:
        storage_account_name: Azure Storage account name
        container_name: Blob container name
        settings: Application settings dictionary
        
    Returns:
        Authenticated BlobServiceClient instance
        
    Raises:
        AzureAuthenticationError: If authentication fails
    """
    authenticator = AzureStorageAuthenticator(storage_account_name, container_name, settings)
    return authenticator.get_blob_service_client()