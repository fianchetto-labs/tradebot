from setuptools import setup, find_packages

setup(
    name='fianchetto-tradebot',
    version='0.1.5',
    author='Fianchetto Labs',
    author_email='aleks@fianchettolabs.com',
    description='Library for implementing API trading integrations with popular brokerages like ETrade, Schwab, and Interactive Brokers',
    url='https://github.com/fianchetto-labs/tradebot',
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Topic :: Office/Business :: Financial :: Investment',
    ],
    python_requires='>=3.6',
    include_package_data=True,
    install_requires=[
        'flask',
        'pandas',
        'pydantic',
        'pygments',
        'python-dateutil',
        'pytz',
        'rauth',
        'sortedcontainers'
    ],
    extras_require={
        'dev': ['pytest']
    },
    keywords='trading bot api brokerage finance automation',
)
