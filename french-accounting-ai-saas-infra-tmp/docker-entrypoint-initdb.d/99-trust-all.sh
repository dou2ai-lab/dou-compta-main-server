#!/bin/bash
# Trust all connections for local dev (Windows host -> Docker Postgres)
set -e
cp /tmp/pg_hba.conf "$PGDATA/pg_hba.conf"
