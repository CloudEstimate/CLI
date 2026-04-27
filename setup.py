from setuptools import setup, find_packages

setup(
    name='cloudestimate',
    version='1.0.0',
    description='Worked example of the Precomputed AI design pattern for sizing self-managed enterprise workloads across Google Cloud, AWS, and Azure.',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'cloudestimate': [
            'cloud_pricing/*.json',
            'config/software/*.yaml',
        ],
    },
    install_requires=[
        'click',
        'pyyaml',
        'rich',
    ],
    entry_points={
        'console_scripts': [
            'cloudestimate=cloudestimate.cli:cli',
        ],
    },
)
