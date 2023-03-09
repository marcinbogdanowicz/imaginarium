#!/bin/sh

set -o errexit
set -o nounset

celery -A imaginarium beat -l info