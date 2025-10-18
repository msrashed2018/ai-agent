"""SQLAlchemy base configuration and metadata."""
import json
import os
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData, JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB as PostgreSQLJSONB, INET as PostgreSQLINET, ARRAY as PostgreSQLARRAY
from sqlalchemy.types import TypeDecorator

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)


class JSONB(TypeDecorator):
    """Platform-independent JSONB type.

    Uses PostgreSQL JSONB for PostgreSQL, falls back to JSON for SQLite and others.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQLJSONB())
        else:
            return dialect.type_descriptor(JSON())


class INET(TypeDecorator):
    """Platform-independent INET type.

    Uses PostgreSQL INET for PostgreSQL, falls back to String for SQLite and others.
    """
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQLINET())
        else:
            return dialect.type_descriptor(String(45))  # Max IPv6 address length


class ARRAY(TypeDecorator):
    """Platform-independent ARRAY type.

    Uses PostgreSQL ARRAY for PostgreSQL, falls back to JSON-encoded text for SQLite and others.
    """
    impl = Text
    cache_ok = True

    def __init__(self, item_type, *args, **kwargs):
        self.item_type = item_type
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQLARRAY(self.item_type))
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if dialect.name != 'postgresql' and value is not None:
            # For non-PostgreSQL databases, serialize to JSON
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if dialect.name != 'postgresql' and value is not None:
            # For non-PostgreSQL databases, deserialize from JSON
            return json.loads(value)
        return value

