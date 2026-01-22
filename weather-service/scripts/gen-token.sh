#!/usr/bin/env bash
set -eu

token="$(openssl rand -hex 32)"
echo "${token}"
echo "INTERNAL_TOKEN=${token}"
