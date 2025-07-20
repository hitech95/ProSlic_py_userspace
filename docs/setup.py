from setuptools import setup, find_packages

setup(
    name='proslic_decoder',
    version='1.0.0',
    description='A simple CSV Proslic SPI bus reader and decoder',
    author='Nicolò Veronese',
    author_email='nicveronese@gmail.com',
    packages=find_packages(),
    install_requires=[
        'prettytable',
    ],
    entry_points={
        'console_scripts': [
            'csv_reader = proslic_decoder.decoder:main',
        ],
    },
)