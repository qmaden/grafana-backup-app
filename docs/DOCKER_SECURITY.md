# Docker Security Assessment and Hardening Guide

## Current Security Issues in Existing Dockerfiles

### 🚨 Critical Issues

#### 1. **Base Image Security**
```dockerfile
# ❌ VULNERABLE: Uses latest tag
FROM alpine:latest

# ✅ SECURE: Use specific version
FROM alpine:3.18
```

#### 2. **User Security** 
```dockerfile
# ❌ VULNERABLE: Runs as root by default, hardcoded UID
USER 1337

# ✅ SECURE: Proper user creation with non-root UID
ARG UID=10001
ARG GID=10001
RUN adduser -u ${UID} -S grafana-backup -G grafana-backup
USER ${UID}:${GID}
```

#### 3. **File Permissions**
```dockerfile
# ❌ VULNERABLE: World-readable files
RUN chmod -R a+r /opt/grafana-backup-tool

# ✅ SECURE: Restrictive permissions
RUN chmod -R 755 /opt/grafana-backup-tool && \
    chmod -R a-w /opt/grafana-backup-tool/grafana_backup
```

#### 4. **Build Context**
```dockerfile
# ❌ VULNERABLE: Copies everything including secrets
ADD . /opt/grafana-backup-tool

# ✅ SECURE: Copy only necessary files
COPY setup.py ./
COPY grafana_backup/ ./grafana_backup/
```

### ⚠️ Medium Issues

#### 5. **Package Management**
```dockerfile
# ❌ INSECURE: Build tools in production
RUN apk add gcc libc-dev libffi-dev python3-dev

# ✅ SECURE: Multi-stage build
FROM alpine:3.18 AS builder
RUN apk add --no-cache gcc libc-dev
# ... build steps ...

FROM alpine:3.18 AS runtime  
# Copy only built artifacts
```

#### 6. **Environment Variables**
```dockerfile
# ❌ INSECURE: No security defaults
ENV RESTORE false

# ✅ SECURE: Security-focused defaults  
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1
```

## Secure Dockerfile Implementation

The new `Dockerfile.secure` addresses these issues:

### Security Features

| Feature | Implementation | Security Benefit |
|---------|---------------|------------------|
| **Specific Base Image** | `FROM alpine:3.18` | Reproducible builds, known vulnerabilities |
| **Non-root User** | `USER 10001:10001` | Prevents privilege escalation |
| **Read-only Filesystem** | Runtime configuration | Prevents file tampering |
| **Minimal Packages** | Only runtime dependencies | Reduced attack surface |
| **Health Checks** | Application-level checks | Monitoring & alerting |
| **Signal Handling** | Exec form CMD | Proper shutdown handling |

### Build Commands

```bash
# Build secure image
docker build -f Dockerfile.secure -t grafana-backup:secure .

# Run with security options
docker run --rm \
  --read-only \
  --tmpfs /tmp:rw,size=100M \
  --tmpfs /opt/grafana-backup-tool/_OUTPUT_:rw,size=500M \
  --security-opt=no-new-privileges:true \
  --cap-drop=ALL \
  --user 10001:10001 \
  grafana-backup:secure
```

## Container Runtime Security

### Security Context (Kubernetes)

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  runAsGroup: 10001
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
  seccompProfile:
    type: RuntimeDefault
```

### Resource Limits

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "512Mi" 
    cpu: "500m"
```

## Network Security

### TLS Configuration
```json
{
  "general": {
    "verify_ssl": true,
    "client_cert": "/path/to/client.pem"
  }
}
```

### Network Policies (Kubernetes)
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: grafana-backup-policy
spec:
  podSelector:
    matchLabels:
      app: grafana-backup
  policyTypes:
  - Egress
  egress:
  # Allow Grafana API
  - to: []
    ports:
    - protocol: TCP
      port: 443
  # Allow Azure Storage
  - to: []
    ports:  
    - protocol: TCP
      port: 443
```

## Secrets Management

### ❌ Insecure Practices
```bash
# DON'T: Hardcode in Dockerfile
ENV GRAFANA_TOKEN="eyJrIjoiXVlQU..."

# DON'T: Plain text in ConfigMap
data:
  token: "eyJrIjoiXVlQU..."
```

### ✅ Secure Practices
```yaml
# Use Kubernetes Secrets
apiVersion: v1
kind: Secret
metadata:
  name: grafana-credentials
type: Opaque
data:
  api-token: <base64-encoded-token>

# Reference in deployment
env:
- name: GRAFANA_TOKEN
  valueFrom:
    secretKeyRef:
      name: grafana-credentials
      key: api-token
```

## Image Scanning

### Build-time Scanning
```bash
# Trivy scan
trivy image grafana-backup:secure

# Docker Scout
docker scout cves grafana-backup:secure
```

### Runtime Scanning
```bash
# Falco rules for runtime monitoring
rule: Unexpected process spawned
condition: spawned_process and container.image contains "grafana-backup"
```

## Supply Chain Security

### 1. **Image Signing**
```bash
# Sign with cosign
cosign sign --key cosign.key grafana-backup:secure
```

### 2. **SBOM Generation**
```bash
# Generate SBOM
syft packages grafana-backup:secure -o spdx-json
```

### 3. **Vulnerability Database**
```bash
# Update vulnerability database
grype db update
grype grafana-backup:secure
```

## Compliance Benchmarks

### CIS Kubernetes Benchmark
- ✅ 5.1.1 Non-root containers
- ✅ 5.1.3 Read-only root filesystems  
- ✅ 5.1.4 Image users should not be root
- ✅ 5.7.3 Apply security context to pods

### NIST Framework Alignment
- ✅ **Identify**: Asset inventory and vulnerability assessment
- ✅ **Protect**: Access controls and data protection
- ✅ **Detect**: Monitoring and logging
- ✅ **Respond**: Incident response procedures
- ✅ **Recover**: Backup and recovery processes

## Security Checklist

### Pre-deployment
- [ ] Image vulnerability scan passed
- [ ] Non-root user configured
- [ ] Secrets externalized
- [ ] Network policies defined
- [ ] Resource limits set

### Post-deployment
- [ ] Health checks passing
- [ ] Logs monitoring configured
- [ ] Access controls verified
- [ ] Backup integrity tested
- [ ] Incident response tested

## Monitoring and Alerting

### Security Events to Monitor
```yaml
# Falco rules
- rule: Unexpected file access in grafana-backup
  condition: >
    open_write and 
    container.image contains "grafana-backup" and
    not fd.name startswith "/opt/grafana-backup-tool/_OUTPUT_"
  
- rule: Unexpected network connections
  condition: >
    outbound and
    container.image contains "grafana-backup" and
    not fd.sip in (grafana_servers, azure_storage_ips)
```

### Metrics to Track
- Container restarts
- Authentication failures  
- Network policy violations
- File system modifications
- Privilege escalation attempts

## Incident Response

### Security Incident Playbook
1. **Detect**: Monitor for security alerts
2. **Isolate**: Network isolation if compromised
3. **Investigate**: Collect logs and forensics
4. **Remediate**: Apply patches/updates
5. **Recover**: Restore from clean backups
6. **Learn**: Update security controls