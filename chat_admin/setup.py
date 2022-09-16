import sys
import re
from setuptools import setup, find_namespace_packages
from pathlib import Path


with open("requirements.txt") as f:
    reqs = f.readlines()
    reqs = [r.strip() for r in reqs]
    reqs = [r for r in reqs if r and not r.startswith("#")]

init_file = Path(__file__).parent / 'chat_admin/__init__.py'
init_txt = init_file.read_text()


version = re.search(
    r'''__version__ = ['"]([0-9.]+(-dev)?)['"]''', init_txt).group(1)
description = 'Darma Chat Admin'

assert version
assert description

packages = find_namespace_packages(include=["chat_admin*"])
print(f"packages:: {packages}", file=sys.stderr)

setup(name="chat-admin",
      version=version,
      description=description,
      author="Thamme Gowda",
      author_email="tgowdan@gmail.com",
      long_description=Path("README.md").read_text(),
      long_description_content_type="text/markdown",
      url="https://github.com/isi_nlp/isi_darma",
      python_requires=">=3.7",
      packages=packages,
      license="Apache",
      install_requires=reqs,
      include_package_data=True,
      zip_safe=False,
      entry_points={"console_scripts": "chat-admin=chat_admin.app:main"},
      classifiers=[
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.7",
          "Programming Language :: Python :: 3.8",
          "License :: OSI Approved :: MIT License",
          "Topic :: Scientific/Engineering :: Artificial Intelligence",
      ],
      )
