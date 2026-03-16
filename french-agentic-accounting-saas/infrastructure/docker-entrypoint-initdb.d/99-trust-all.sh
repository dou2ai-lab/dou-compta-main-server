#!/bin/bash
# Trust all connections for local dev (Windows host -> Postgres)
set -e
cp /tmp/pg_hba.conf "$PGDATA/pg_hba.conf"
