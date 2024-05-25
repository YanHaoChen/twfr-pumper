from setuptools import setup, find_packages

setup(
    name='twfr-pumper',
    version='0.0.1',
    install_requires=[
        'requests',
        'beautifulsoup4',
        'pandas',
        'plotly'
    ],
    extras_require={
        'jupyter': ['jupyter'],
    },
    packages=find_packages(
        # All keyword arguments below are optional:
        where='.',  # '.' by default
        include=['twfrpumper*'],  # ['*'] by default
        exclude=['twfrpumper.tests'],  # empty by default
    )
)