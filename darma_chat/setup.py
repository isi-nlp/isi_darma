
import sys
import re
from setuptools import setup, find_namespace_packages
from pathlib import Path


with open("requirements.txt") as f:
    reqs = f.readlines()
    reqs = [r.strip() for r in reqs]
    reqs = [r for r in reqs if r and not r.startswith("#")]

_package_name = 'darma_chat'
init_file = Path(__file__).parent / _package_name / '__init__.py'
init_txt = init_file.read_text()


version = re.search(
    r'''__version__ = ['"]([0-9.]+(-dev)?)['"]''', init_txt).group(1)
description = re.search(
    r'''__description__ = ['"](.*)['"]''', init_txt).group(1)

assert version
assert description

packages = find_namespace_packages(include=["darma_chat*"],
    exclude=['darma_chat.frontend.*',
             'darma_chat.task_config.*'])
print(f"packages:: {packages}", file=sys.stderr)

setup(name=_package_name,
      version=version,
      description=description,
      author="Thamme Gowda, Justin Cho",
      author_email="tg@isi.edu, cho@isi.edu",
      long_description=Path("README.md").read_text(),
      long_description_content_type="text/markdown",
      url="https://github.com/isi-nlp/isi_darma",
      python_requires=">=3.7",
      packages=packages,
      license="MIT",
      install_requires=reqs,
      include_package_data=True,
      zip_safe=False,
      entry_points={"console_scripts": "darma-chat=darma_chat.__main__:main"},
      classifiers=[
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.7",
          "Programming Language :: Python :: 3.8",
          "License :: OSI Approved :: MIT License",
          "Topic :: Scientific/Engineering :: Artificial Intelligence",
          "Natural Language :: English",
      ],
      )
