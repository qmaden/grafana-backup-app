# Grafana Backup Tool - Azure Edition

A Python-based application to backup Grafana settings using the [Grafana API](https://grafana.com/docs/grafana/latest/http_api/) with Azure Storage integration and Azure Workload Identity support.

## Features

✅ **Azure-Native**: Designed specifically for Azure environments  
✅ **Workload Identity**: Secure, keyless authentication  
✅ **Comprehensive Backup**: All Grafana components supported  
✅ **Container-Ready**: Secure Docker image with non-root user  
✅ **Kubernetes Integration**: CronJob examples with security best practices

## Supported Grafana Components

* **Dashboards** (with alerts)
* **Datasources** 
* **Folders & Permissions**
* **Library Elements**
* **Alert Channels & Rules**
* **Contact Points & Notification Policies**
* **Teams & Team Members**
* **Organizations & Users**
* **Snapshots & Annotations**
* **Dashboard Versions** (backup only)

## Requirements

* **Azure Storage Account** for backup storage
* **Azure Kubernetes Service (AKS)** with Workload Identity (recommended)
* **Grafana API Token** with Admin role
* **Python 3.11+** (if running locally)

## Quick Start

### 1. Azure Setup

```bash
# Create storage account
az storage account create \
    --name mystorageaccount \
    --resource-group myResourceGroup \
    --location eastus \
    --sku Standard_LRS

# Create container
az storage container create \
    --name grafana-backups \
    --account-name mystorageaccount
```

### 2. Workload Identity Setup

```bash
# Create managed identity
az identity create \
    --name grafana-backup-identity \
    --resource-group myResourceGroup

# Assign Storage permissions
az role assignment create \
    --role "Storage Blob Data Contributor" \
    --assignee $(az identity show --name grafana-backup-identity --resource-group myResourceGroup --query clientId -o tsv) \
    --scope $(az storage account show --name mystorageaccount --resource-group myResourceGroup --query id -o tsv)
```

### 3. Deploy to Kubernetes

```bash
# Apply the provided Kubernetes manifests
kubectl apply -f examples/kubernetes-workload-identity.yaml
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GRAFANA_URL` | Grafana instance URL | Yes |
| `GRAFANA_TOKEN` | API token with Admin role | Yes |
| `AZURE_STORAGE_ACCOUNT_NAME` | Storage account name | Yes |
| `AZURE_STORAGE_CONTAINER_NAME` | Container name | Yes |
| `AZURE_CLIENT_ID` | Managed Identity client ID | For Workload Identity |
| `AZURE_TENANT_ID` | Azure tenant ID | For Workload Identity |

### Configuration File

```json
{
  "grafana": {
    "url": "https://your-grafana.azurefd.net",
    "token": "your-grafana-api-token"
  },
  "general": {
    "verify_ssl": true,
    "backup_dir": "_OUTPUT_"
  },
  "azure": {
    "storage_account_name": "mystorageaccount",
    "container_name": "grafana-backups",
    "managed_identity_client_id": "your-client-id"
  }
}
```

## Usage

### Command Line

```bash
# Backup all components
grafana-backup save

# Restore from archive
grafana-backup restore backup_20241129_143022.tar.gz

# Backup specific components
grafana-backup save --components=dashboards,datasources

# Delete all components (be careful!)
grafana-backup delete --components=dashboards
```

### Docker

```bash
# Backup
docker run --rm \
    -e GRAFANA_URL="https://your-grafana.com" \
    -e GRAFANA_TOKEN="your-token" \
    -e AZURE_STORAGE_ACCOUNT_NAME="mystorageaccount" \
    -e AZURE_STORAGE_CONTAINER_NAME="grafana-backups" \
    -v $(pwd)/backups:/opt/grafana-backup-tool/_OUTPUT_ \
    grafana-backup:secure

# Restore
docker run --rm \
    -e RESTORE=true \
    -e ARCHIVE_FILE="backup_20241129_143022.tar.gz" \
    -e GRAFANA_URL="https://your-grafana.com" \
    -e GRAFANA_TOKEN="your-token" \
    -e AZURE_STORAGE_CONTAINER_NAME="grafana-backups" \
    grafana-backup:secure
```

### Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: grafana-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: grafana-backup-sa
          containers:
          - name: grafana-backup
            image: your-registry.azurecr.io/grafana-backup:secure
            env:
            - name: AZURE_STORAGE_CONTAINER_NAME
              value: "grafana-backups"
            - name: GRAFANA_TOKEN
              valueFrom:
                secretKeyRef:
                  name: grafana-credentials
                  key: api-token
```

## Authentication Methods (Priority Order)

1. **Azure Workload Identity** (Kubernetes with OIDC)
2. **User-assigned Managed Identity** 
3. **System-assigned Managed Identity**
4. **DefaultAzureCredential chain**
5. **Connection String** (legacy, deprecated)

## Security Features

### Container Security
- ✅ **Non-root user** (UID 10001)
- ✅ **Read-only root filesystem**
- ✅ **No privilege escalation** 
- ✅ **Dropped capabilities**
- ✅ **Security context constraints**

### Network Security  
- ✅ **TLS enforcement**
- ✅ **Certificate validation**
- ✅ **Network policies** (examples provided)

### Access Control
- ✅ **Minimal RBAC permissions**
- ✅ **Resource-scoped access**
- ✅ **Principle of least privilege**

## Installation

### From PyPI

```bash
pip install grafana-backup-azure
```

### From Source

```bash
git clone https://github.com/ysde/grafana-backup-tool.git
cd grafana-backup-tool

# Using pip
pip install .

# Using uv (faster, recommended)
uv pip install .
```

### Docker Image

```bash
# Build secure image with uv for faster builds
docker build -t grafana-backup:secure .

# Or pull from registry
docker pull your-registry.azurecr.io/grafana-backup:secure
```

## Examples

Complete examples are provided in the `examples/` directory:

- **`kubernetes-workload-identity.yaml`** - Full Kubernetes deployment with security
- **`grafanaSettings.workload-identity.json`** - Configuration template
- **Azure setup scripts** - Infrastructure as Code

## Monitoring & Troubleshooting

### Health Checks

The container includes health checks:

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' container_name
```

### Debug Mode

Enable debug logging:

```bash
export DEBUG=true
grafana-backup save
```

### Common Issues

1. **Authentication Failed**
   - Verify managed identity permissions
   - Check federated identity credentials
   - Validate audience in token projection

2. **Storage Access Denied**
   - Confirm Storage Blob Data Contributor role
   - Verify storage account name and container

3. **Grafana API Errors**  
   - Check API token permissions (must be Admin)
   - Verify Grafana URL accessibility
   - Ensure SSL certificate validation

## Migration Guide

### From Multi-Cloud Version

1. **Remove deprecated configs**: Remove AWS/GCP configurations
2. **Update dependencies**: Install azure-identity package  
3. **Configure Workload Identity**: Set up managed identity
4. **Test authentication**: Verify backup/restore operations
5. **Update automation**: Migrate to new container image

### From Connection Strings

1. **Set up Workload Identity**: Configure managed identity
2. **Test dual authentication**: Verify both methods work
3. **Remove connection string**: Delete legacy configuration
4. **Monitor operations**: Ensure successful authentication

## Support

For issues and questions:

1. **Check logs**: Enable debug mode for detailed output
2. **Review documentation**: See `docs/` directory for detailed guides
3. **Verify configuration**: Use provided examples as reference
4. **Security review**: Follow security best practices guide

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following security guidelines  
4. Test with Azure environment
5. Submit pull request with security review