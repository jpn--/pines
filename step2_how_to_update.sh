#!/bin/bash -x -e

python setup.py bdist_wheel upload

git push
git push --tags

conda build ./conda --output-folder conda_builds/ -c jpn --python 3.7

conda convert --platform win-64 conda_builds/osx-64/pines-2.94.0-*.tar.bz2 -o conda_builds/
anaconda upload conda_builds/win-64/pines-2.94.0-*.tar.bz2

conda convert --platform linux-64 conda_builds/osx-64/pines-2.94.0-*.tar.bz2 -o conda_builds/
anaconda upload conda_builds/linux-64/pines-2.94.0-*.tar.bz2

