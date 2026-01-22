#!/usr/bin/env bash
set -eu

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
else
  echo ".env already exists; no changes made"
fi
