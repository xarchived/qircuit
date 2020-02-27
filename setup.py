import re

from setuptools import setup

with open('qircuit/__init__.py') as f:
    version = re.search(r'([0-9]+(\.dev|\.|)){3}', f.read()).group(0)

setup(
    name='qircuit',
    version=version,
    description='Distributed Quantum Circuit',
    author='Xurvan',
    packages=['qircuit'],
    install_requires=['numpy'],
    python_requires='>=3.6',
    zip_safe=False)
