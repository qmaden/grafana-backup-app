# Multi-stage Dockerfile for optimized production image
# Stage 1: Build stage with all build dependencies
FROM alpine:3.22.1 AS builder

# Build dependencies
RUN apk add --no-cache \
    python3>=3.13 \
    py3-pip \
    py3-cryptography \
    py3-cffi \
    py3-packaging \
    build-base \
    python3-dev \
    libffi-dev \
    curl \
    && rm -rf /var/cache/apk/*

# Install uv for faster builds
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set build environment
ENV UV_SYSTEM_PYTHON=1

# Create build directory
WORKDIR /build

# Copy source files
COPY setup.py ./
COPY grafana_backup/ ./grafana_backup/
COPY README.md CHANGELOG.md LICENSE ./

# Build and install the application
RUN uv pip install --system --break-system-packages --no-cache .

# Stage 2: Runtime stage - minimal production image
FROM alpine:3.22.1 AS runtime

LABEL version="1.5.0" \
      description="Azure-only Grafana Backup Tool with Workload Identity support (Multi-stage optimized)"

# Security: Create non-root user with proper shell and home directory
ARG UID=10001
ARG GID=10001
ARG USERNAME=grafana-backup

# Runtime environment variables
ENV RESTORE="false" \
    ARCHIVE_FILE="" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install only runtime dependencies (no build tools)
RUN apk add --no-cache \
    python3>=3.13 \
    py3-cryptography \
    py3-cffi \
    py3-packaging \
    ca-certificates \
    bash \
    && rm -rf /var/cache/apk/*

# Create non-root user and group
RUN addgroup -g ${GID} -S ${USERNAME} && \
    adduser -u ${UID} -S ${USERNAME} -G ${USERNAME} -h /home/${USERNAME} -s /bin/bash

# Copy Python packages from builder stage
COPY --from=builder /usr/lib/python3.13/site-packages/ /usr/lib/python3.13/site-packages/
COPY --from=builder /usr/bin/grafana-backup /usr/bin/grafana-backup

# Create application directory
WORKDIR /opt/grafana-backup-tool

# Create output directory with proper permissions
RUN mkdir -p /opt/grafana-backup-tool/_OUTPUT_ && \
    chown -R ${UID}:${GID} /opt/grafana-backup-tool && \
    chmod 755 /opt/grafana-backup-tool/_OUTPUT_

# Security: Switch to non-root user
USER ${UID}:${GID}

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import grafana_backup; print('OK')" || exit 1

# Use exec form for proper signal handling
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["if [ \"$RESTORE\" = \"true\" ]; then \
        if [ -n \"$AZURE_STORAGE_CONTAINER_NAME\" ]; then \
            exec grafana-backup restore \"$ARCHIVE_FILE\"; \
        else \
            exec grafana-backup restore \"_OUTPUT_/$ARCHIVE_FILE\"; \
        fi; \
    else \
        exec grafana-backup save; \
    fi"]