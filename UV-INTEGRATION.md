# UV Integration

This project now uses [uv](https://astral.sh/uv) for faster and more reliable Python package management.

## Benefits of UV

- **Faster installation**: Up to 10-100x faster than pip
- **Better dependency resolution**: More reliable and consistent
- **Smaller Docker layers**: More efficient caching
- **Cross-platform**: Works consistently across environments

## Usage

### Local Development

Install uv first:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then install the project:
```bash
# Instead of: pip install .
uv pip install .

# Or for development
uv pip install -e .
```

### Docker

The Dockerfile automatically uses uv for package installation:
```dockerfile
# Fast package installation with uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    export PATH="/root/.local/bin:$PATH" && \
    uv pip install --system --break-system-packages --no-cache .
```

### Docker Build

Build times are significantly reduced:
```bash
docker build -t grafana-backup:latest .
```

## Migration from pip

If you're upgrading from a pip-based installation:

1. **No code changes required** - uv is compatible with pip
2. **Same commands work** - All existing pip install commands work with uv
3. **Faster builds** - Docker builds will be noticeably faster
4. **Better caching** - More efficient Docker layer caching

## Troubleshooting

### Alpine Linux Issues

On Alpine Linux (used in Docker), uv requires the `--break-system-packages` flag due to externally managed Python environments.

### Virtual Environments

For isolated environments, use:
```bash
uv venv
source .venv/bin/activate
uv pip install .
```

## Performance Comparison

Typical installation time improvements:
- **Local installation**: 2-5x faster than pip
- **Docker builds**: 3-10x faster than pip
- **Cold starts**: Significantly improved due to better caching

## Documentation

- [uv Documentation](https://docs.astral.sh/uv/)
- [Installation Guide](https://astral.sh/uv/getting-started/)
- [Migration Guide](https://docs.astral.sh/uv/pip/compatibility/)