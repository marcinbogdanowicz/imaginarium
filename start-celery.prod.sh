#!/bin/sh

set -o errexit
set -o nounset

celery -A imaginarium worker -l info