# Built-in imports
from codecs import open
import re

# Package imports
from setuptools import find_packages, setup

# Get the requirements list
with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()

# Read the __version__.py file
with open('imagine-galmag/__version__.py', 'r') as f:
    vf = f.read()

# Obtain version from read-in __version__.py file
version = re.search(r"^_*version_* = ['\"]([^'\"]*)['\"]", vf, re.M).group(1)

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name="imagine-galmag",
      version=version,
      description="Integration between IMAGINE and GalMag",
      license="GPLv3",
      url="https://github.com/IMAGINE-Consortium/imagine-galmag/",
      author="Luiz Felippe S. Rodrigues, IMAGINE Consortium",
      author_email="luizfelippesr@alumniusp.br",
      maintainer="IMAGINE Consortium",
      packages=find_packages(),
      include_package_data=True,
      platforms=['Linux', 'Unix'],
      python_requires='>=3.5',
      install_requires=requirements)

