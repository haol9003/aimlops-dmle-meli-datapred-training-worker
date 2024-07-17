#!/bin/bash

# Check if the file exists and the variable does not (or it is empty)
if [ -f /run/secrets/artifactory_pypi_user ] && [ -z ${ARTIFACTORY_PYPI_USER+x} ]; then
    ARTIFACTORY_PYPI_USER=$(cat /run/secrets/artifactory_pypi_user)
    export ARTIFACTORY_PYPI_USER
fi
if [ -f /run/secrets/artifactory_pypi_pass ] && [ -z ${ARTIFACTORY_PYPI_PASS+x} ]; then
    ARTIFACTORY_PYPI_PASS=$(cat /run/secrets/artifactory_pypi_pass)
    export ARTIFACTORY_PYPI_PASS
fi

if [ "$1" == "sync" ]; then
    pdm sync "${@:2}"
else
    pdm "$@"
fi
