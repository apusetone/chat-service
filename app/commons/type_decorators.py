import os

from sqlalchemy import String, TypeDecorator, func, type_coerce
from sqlalchemy.dialects.postgresql import BYTEA


class PGPString(TypeDecorator):
    impl = BYTEA

    cache_ok = True

    def __init__(self):
        super(PGPString, self).__init__()
        self.passphrase = os.environ["SECRET"]

    def bind_expression(self, bindvalue):
        # convert the bind's type from PGPString to
        # String, so that it's passed to psycopg2 as is without
        # a dbapi.Binary wrapper
        bindvalue = type_coerce(bindvalue, String)
        # Cast the bind value to text type explicitly for pgp_sym_encrypt
        return func.pgp_sym_encrypt(bindvalue.cast(String), self.passphrase)

    def column_expression(self, col):
        return func.pgp_sym_decrypt(col, self.passphrase)
