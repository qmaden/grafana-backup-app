from grafana_backup.constants import (PKG_NAME, PKG_VERSION)
from setuptools import setup, find_packages

# Global variables
name = PKG_NAME
version = PKG_VERSION
requires = [
    'requests',
    'docopt',
    'azure-storage-blob>=12.19.0',  # Updated for better authentication support
    'azure-identity>=1.15.0',        # Required for workload identity and modern auth
    'packaging'
]

setup(
    name=name,
    version=version,
    description='A Python-based application to backup Grafana settings using the Grafana API',
    long_description_content_type='text/markdown',
    long_description=open('README.md', 'r').read(),
    author="author",
    author_email="ysde108@gmail.com",
    url="https://github.com/ysde/grafana-backup-tool",
    entry_points={
        'console_scripts': [
            'grafana-backup = grafana_backup.cli:main'
        ]
    },
    packages=find_packages(),
    install_requires=requires,
    package_data={'': ['conf/*']},
)
