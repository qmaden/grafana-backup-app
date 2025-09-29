# Grafana Backup Tool - Simplified Version

## Overview
This is a streamlined version of the Grafana Backup Tool focused exclusively on **save** and **restore** operations for essential Grafana components.

## What's Included ✅

### Core Operations
- **`grafana-backup save`** - Backup Grafana components to files
- **`grafana-backup restore`** - Restore Grafana components from backup files

### Supported Components
- **Folders** - Grafana folder structure  
- **Dashboards** - All dashboard configurations with embedded alerts
- **Datasources** - Data source configurations  
- **Alert Channels** - Legacy notification channels for alerts
- **Alert Rules** - Modern alert rule definitions
- **Library Elements** - Reusable dashboard panels

### Azure Integration
- **Azure Storage** - Automatic upload/download to Azure Storage
- **Workload Identity** - Secure keyless authentication
- **Managed Identity** - Azure-native authentication

## What's Removed ❌

### CLI Operations
- `grafana-backup delete` - Delete operations removed
- `grafana-backup tools` - Utility tools removed

### User/Organization Management
- Organizations backup/restore
- Users backup/restore
- Teams backup/restore  
- Team members backup/restore

### Utility Functions
- User permission management
- Alert pause/unpause functionality
- User viewer role assignments
- Complex administrative tools

## Usage Examples

### Basic Backup
```bash
# Backup all supported components
grafana-backup save

# Backup specific components only
grafana-backup save --components=dashboards,datasources,folders
```

### Basic Restore
```bash
# Restore from backup file
grafana-backup restore backup_20241001.tar.gz

# Restore specific components only  
grafana-backup restore backup_20241001.tar.gz --components=dashboards,folders
```

### Available Components
```
folders, dashboards, datasources, alert-channels, alert-rules, library_elements
```

## Benefits of Simplification

### 🚀 **Performance**
- Faster builds with UV package manager
- Smaller Docker images
- Reduced memory footprint

### 🔧 **Maintenance**  
- Cleaner codebase (removed 10+ files)
- Simplified dependencies
- Easier troubleshooting

### 🔒 **Security**
- Reduced attack surface
- Fewer external dependencies
- Azure-focused security model

### 📝 **Usability**
- Clear, focused functionality
- Simpler command interface
- Better error messages

## Migration Guide

If you're upgrading from the full version:

### ✅ **Still Works**
- All backup/restore operations for supported components
- Azure Storage integration
- Configuration files and environment variables
- Docker deployments

### ⚠️ **No Longer Available**
- User/organization management - Use Grafana UI or direct API calls
- Delete operations - Use Grafana UI for cleanup
- Administrative tools - Use Grafana native tools

### 🔄 **Alternatives**
- **User Management**: Use Grafana's native user management UI
- **Organization Management**: Use Grafana's admin interface
- **Cleanup Operations**: Use Grafana's native delete functions
- **Advanced Tools**: Use Grafana's API directly or other specialized tools

## File Size Comparison

**Before**: 40+ Python files  
**After**: 20 Python files  
**Reduction**: ~50% smaller codebase

## Use Cases

Perfect for:
- **Configuration Backup**: Dashboards, datasources, folders
- **Migration Projects**: Moving between Grafana instances  
- **Disaster Recovery**: Essential component restoration
- **Azure Environments**: Cloud-native deployments
- **CI/CD Pipelines**: Automated backup/restore workflows

Not suitable for:
- Complex user management workflows
- Organization administration tasks  
- Advanced administrative operations
- Multi-cloud deployments (Azure only)

## Support

This simplified version focuses on the core use case of backing up and restoring Grafana configurations. For advanced administrative tasks, use Grafana's native tools or the full version of this tool.