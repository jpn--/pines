#!/bin/bash -x -e

bumpversion --config-file bumpversion.cfg minor

python setup.py bdist_wheel upload

git push

CONDAOUT=`conda build ./conda  --output-folder conda_builds/ --output`
conda build ./conda --output-folder conda_builds/

conda convert --platform all conda_builds/osx-64/pines-2.21.0-*.tar.bz2 -o conda_builds/
anaconda upload conda_builds/win-64/pines-2.21.0-*.tar.bz2

cd ${HOME}

pip install pines --no-cache-dir -U

