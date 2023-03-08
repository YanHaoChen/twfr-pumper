from setuptools import setup, find_packages

setup(
    name='twfr-pumper',
    version='0.0.1',
    install_requires=[
        'requests',
        'beautifulsoup4==4.9.3',
        'pandas==1.2.4',
        'plotly==5.2.1'
    ],
    extra_require={
        'jupyter': ['1.0.0']
    },
    packages=find_packages(
        # All keyword arguments below are optional:
        where='.',  # '.' by default
        include=['twfrpumper*'],  # ['*'] by default
        exclude=['twfrpumper.tests'],  # empty by default
    )
)