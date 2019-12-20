from setuptools import setup, find_packages


with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name="imagine-galmag",
      version="0.1.0",
      description="Integration between IMAGINE and GalMag",
      license="GPLv3",
      url="",
      author="Luiz Felippe S. Rodrigues, IMAGINE Consortium",
      author_email="luizfelippesr@usp.br",
      maintainer="IMAGINE Consortium",
      packages=find_packages(),
      include_package_data=True,
      platforms="any",
      python_requires='>=3.5',
      install_requires=requirements)
