#!/bin/bash
set -e

# データベースが存在しない場合にのみ作成する
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE chat_service'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'chat_service');\\gexec
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE chat_service_test'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'chat_service_test');\\gexec
EOSQL

# 拡張機能を有効にする
psql -v ON_ERROR_STOP=0 --username "$POSTGRES_USER" -d chat_service <<-EOSQL
  CREATE EXTENSION pgcrypto;
EOSQL

psql -v ON_ERROR_STOP=0 --username "$POSTGRES_USER" -d chat_service_test <<-EOSQL
  CREATE EXTENSION pgcrypto;
EOSQL