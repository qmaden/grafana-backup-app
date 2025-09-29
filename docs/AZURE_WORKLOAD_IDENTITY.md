# Azure Workload Identity Integration Guide

This guide explains how to configure Azure Workload Identity authentication for the Grafana Backup Tool, providing secure, keyless authentication to Azure Storage.

## Overview

Azure Workload Identity allows your Kubernetes workloads to authenticate to Azure services using Kubernetes Service Account tokens, eliminating the need to store Azure credentials as secrets.

## Benefits

✅ **Keyless Authentication**: No connection strings or access keys
✅ **Automatic Token Rotation**: Azure handles token lifecycle
✅ **Principle of Least Privilege**: Fine-grained access control
✅ **Kubernetes Native**: Integrates seamlessly with RBAC
✅ **Audit Trail**: Full audit logging in Azure AD

## Prerequisites

1. **Azure Kubernetes Service (AKS)** with Workload Identity enabled
2. **Azure Storage Account** for backups
3. **User-assigned Managed Identity** 
4. **Federated Identity Credential** configured

## Setup Steps

### 1. Enable Workload Identity on AKS

```bash
# Create AKS cluster with Workload Identity
az aks create \
    --resource-group myResourceGroup \
    --name myAKSCluster \
    --enable-oidc-issuer \
    --enable-workload-identity \
    --node-count 1

# Get OIDC issuer URL
export AKS_OIDC_ISSUER="$(az aks show -n myAKSCluster -g myResourceGroup --query "oidcIssuerProfile.issuerUrl" -otsv)"
```

### 2. Create User-Assigned Managed Identity

```bash
# Create managed identity
az identity create \
    --name grafana-backup-identity \
    --resource-group myResourceGroup

# Get client ID
export USER_ASSIGNED_CLIENT_ID=$(az identity show \
    --resource-group myResourceGroup \
    --name grafana-backup-identity \
    --query 'clientId' \
    -otsv)
```

### 3. Configure Storage Account Permissions

```bash
# Get storage account resource ID
export STORAGE_ACCOUNT_ID=$(az storage account show \
    --name mystorageaccount \
    --resource-group myResourceGroup \
    --query 'id' \
    -otsv)

# Assign Storage Blob Data Contributor role
az role assignment create \
    --role "Storage Blob Data Contributor" \
    --assignee $USER_ASSIGNED_CLIENT_ID \
    --scope $STORAGE_ACCOUNT_ID
```

### 4. Create Federated Identity Credential

```bash
# Create federated credential
az identity federated-credential create \
    --name grafana-backup-federated-credential \
    --identity-name grafana-backup-identity \
    --resource-group myResourceGroup \
    --issuer $AKS_OIDC_ISSUER \
    --subject system:serviceaccount:default:grafana-backup-sa
```

### 5. Deploy Kubernetes Resources

Apply the Kubernetes manifests from `examples/kubernetes-workload-identity.yaml`:

```bash
kubectl apply -f examples/kubernetes-workload-identity.yaml
```

## Configuration Options

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_CLIENT_ID` | Managed Identity Client ID | Yes |
| `AZURE_TENANT_ID` | Azure Tenant ID | Yes |
| `AZURE_STORAGE_ACCOUNT_NAME` | Storage Account Name | Yes |
| `AZURE_STORAGE_CONTAINER_NAME` | Container Name | Yes |
| `AZURE_FEDERATED_TOKEN_FILE` | Token file path | Auto-set |

### Configuration File

```json
{
  "azure": {
    "storage_account_name": "mystorageaccount",
    "container_name": "grafana-backups",
    "managed_identity_client_id": "your-client-id"
  }
}
```

## Authentication Methods (Priority Order)

1. **Workload Identity** (if OIDC token file exists)
2. **User-assigned Managed Identity** (if client_id provided)
3. **System-assigned Managed Identity**
4. **DefaultAzureCredential chain**
5. **Connection String** (legacy, deprecated)

## Security Best Practices

### Container Security
- ✅ Non-root user (UID 10001)
- ✅ Read-only root filesystem
- ✅ No privilege escalation
- ✅ Dropped capabilities
- ✅ Security context constraints

### Network Security
- ✅ TLS/HTTPS enforcement
- ✅ Certificate validation
- ✅ Network policies (recommended)

### Access Control
- ✅ Minimal RBAC permissions
- ✅ Resource-scoped access
- ✅ Principle of least privilege

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   ```bash
   # Verify federated credential
   az identity federated-credential list \
       --identity-name grafana-backup-identity \
       --resource-group myResourceGroup
   ```

2. **Token File Not Found**
   ```bash
   # Check token volume mount
   kubectl describe pod <pod-name>
   ```

3. **Permission Denied**
   ```bash
   # Verify role assignments
   az role assignment list \
       --assignee $USER_ASSIGNED_CLIENT_ID \
       --output table
   ```

### Debug Mode

Enable debug logging:
```yaml
env:
- name: DEBUG
  value: "true"
```

## Migration from Connection Strings

### Phase 1: Dual Authentication (Transition)
Configure both workload identity and connection string:

```json
{
  "azure": {
    "storage_account_name": "mystorageaccount",
    "container_name": "grafana-backups",
    "managed_identity_client_id": "your-client-id",
    "connection_string": "your-connection-string"
  }
}
```

### Phase 2: Remove Connection String
After testing, remove the connection string:

```json
{
  "azure": {
    "storage_account_name": "mystorageaccount", 
    "container_name": "grafana-backups",
    "managed_identity_client_id": "your-client-id"
  }
}
```

## Monitoring and Alerting

### Health Checks
The container includes health checks for authentication:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s \
    CMD python3 -c "import grafana_backup; print('OK')" || exit 1
```

### Metrics
Monitor authentication metrics in Azure AD logs:
- Token requests
- Authentication failures
- Permission denials

## Examples

See the `examples/` directory for complete deployment templates:
- `kubernetes-workload-identity.yaml` - Full K8s deployment
- `grafanaSettings.workload-identity.json` - Configuration template