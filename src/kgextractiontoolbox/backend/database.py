from os import environ

import json
import logging
import os
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy import exc
from sqlalchemy.dialects.postgresql.dml import OnConflictDoNothing
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import Insert

import kgextractiontoolbox.config as cnf
from kgextractiontoolbox import tools
from kgextractiontoolbox.backend.models import Base


@compiles(Insert, 'postgresql')
def prefix_inserts(insert, compiler, **kw):
    insert._post_values_clause = OnConflictDoNothing()
    return compiler.visit_insert(insert, **kw)


def add_engine_pidguard(engine):
    """Add multiprocessing guards.

    Forces a connection to be reconnected if it is detected
    as having been shared to a sub-process.

    """

    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        connection_record.info['pid'] = os.getpid()

    @event.listens_for(engine, "checkout")
    def checkout(dbapi_connection, connection_record, connection_proxy):
        pid = os.getpid()
        if connection_record.info['pid'] != pid:
            # substitute log.debug() or similar here as desired
            logging.debug(
                "Parent process %(orig)s forked (%(newproc)s) with an open "
                "database connection, "
                "which is being discarded and recreated."
                f'("newproc": {pid}, "orig": {connection_record.info["pid"]})')
            connection_record.connection = connection_proxy.connection = None
            raise exc.DisconnectionError(
                "Connection record belongs to pid %s, "
                "attempting to check out in pid %s" %
                (connection_record.info['pid'], pid)
            )


class Session:
    _instance = None
    is_sqlite = False
    is_postgres = False

    def _load_config(self, backend_config: str):
        with open(backend_config) as f:
            config = json.load(f)
        # TODO: why tf is there no wrapper?
        Session.is_sqlite = False or ("use_SQLite" in config and config["use_SQLite"])
        if Session.is_sqlite:
            self.sqlite_path = tools.proj_rel_path(config["SQLite_path"])
            # print(self.sqlite_path)
            if not self.sqlite_path:
                raise ValueError("use_SQLite is true, but SQLite_path is not set!")
        else:
            self.config = dict(
                POSTGRES_USER=environ.get("NI_POSTGRES_USER", config["POSTGRES_USER"]),
                POSTGRES_PW=environ.get("NI_POSTGRES_PW", config["POSTGRES_PW"]),
                POSTGRES_HOST=environ.get("NI_POSTGRES_HOST", config["POSTGRES_HOST"]),
                POSTGRES_PORT=environ.get("NI_POSTGRES_PORT", config["POSTGRES_PORT"]),
                POSTGRES_DB=environ.get("NI_POSTGRES_DB", config["POSTGRES_DB"]),
            )

    def __init__(self, connection_config, declarative_base):
        if not self._instance:
            self.sqlite_path = None
            self._load_config(connection_config)
            self.engine = create_engine(self.get_conn_uri())
            add_engine_pidguard(self.engine)
            session_cls = sessionmaker(bind=self.engine)  # python black magic: equip self with additional functions
            self.session = scoped_session(session_cls)  # session_cls()
            self.session.is_postgres = Session.is_postgres
            self.session.is_sqlite = Session.is_sqlite
            declarative_base.metadata.create_all(self.engine)
        else:
            raise ValueError("Instance already exists: Use get()")

    def get_conn_uri(self):
        if self.sqlite_path:
            return f"sqlite:///{self.sqlite_path}"
        else:
            Session.is_postgres = True
            return "postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}".format(
                user=self.config["POSTGRES_USER"],
                password=self.config["POSTGRES_PW"],
                host=self.config["POSTGRES_HOST"],
                port=self.config["POSTGRES_PORT"],
                db=self.config["POSTGRES_DB"],
            )

    @classmethod
    def get(cls, connection_config: str = cnf.BACKEND_CONFIG, declarative_base=Base):
        if not cls._instance:
            cls._instance = Session(connection_config, declarative_base)
        return cls._instance.session

    @classmethod
    def lock_tables(cls, *tables):
        for table in tables:
            cls.get().execute(f"LOCK TABLE {table} IN EXCLUSIVE MODE")
