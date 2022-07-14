
import sys
import re
from setuptools import setup, find_packages, find_namespace_packages
from pathlib import Path


with open("README.md", encoding="utf8") as f:
    # strip the header and badges etc
    readme = f.read()

with open("requirements.txt") as f:
    reqs = f.readlines()
    reqs = [r.strip() for r in reqs]
    reqs = [r for r in reqs if r and not r.startswith("#")]
    # reqs = [r.split('==')[0] for r in reqs]

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
#packages = ['darma_chat', 'darma_chat.hydra_configs']
print(f"packages:: {packages}", file=sys.stderr)
#raise Exception(f'packages {packages}')

setup(name=_package_name,
      version=version,
      description=description,
      author="USC ISI",
      author_email="tg@isi.edu",
      long_description=readme,
      long_description_content_type="text/markdown",
      url="https://github.com/isi-nlp/darma-chat",
      python_requires=">=3.7",
      #packages=find_packages(include=["darma_chat.*", "hydra_plugins.*"]),
      packages=packages,
      license="MIT",
      install_requires=reqs,
      include_package_data=True,
      #package_data={'': ['*.txt', '*.md', '*.opt', "*.yaml",
      #                   "abstractions/**/*"]},
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
