from grafana_backup.constants import (PKG_NAME, PKG_VERSION)
from setuptools import setup, find_packages

# Global variables
name = PKG_NAME
version = PKG_VERSION
requires = [
    'requests>=2.32.0',
    'docopt>=0.6.2',
    'azure-storage-blob>=12.26.0',  # Latest version with improved security and performance
    'azure-identity>=1.25.0',       # Latest version with enhanced authentication features
    'packaging>=24.0'
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
    python_requires='>=3.11',
    entry_points={
        'console_scripts': [
            'grafana-backup = grafana_backup.cli:main'
        ]
    },
    packages=find_packages(),
    install_requires=requires,
    package_data={'': ['conf/*']},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: System :: Archiving :: Backup',
    ],
)
