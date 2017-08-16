#!/bin/bash -x -e

bumpversion --config-file bumpversion.cfg minor

./step2_how_to_update.sh