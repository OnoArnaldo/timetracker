import typing as _
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

if _.TYPE_CHECKING:
    from sqlalchemy import Engine


class Database:
    def __init__(self, url: str, **kwargs):
        self.engine: 'Engine' = create_engine(url, **kwargs)
        self._cur_session: Session | None = None

    @property
    def cur_session(self):
        return self._cur_session

    @contextmanager
    def session(self) -> Session:
        if self._cur_session is None:
            self._cur_session = Session(self.engine, autobegin=False)

        if self._cur_session.in_transaction():
            yield self._cur_session
        else:
            with self._cur_session.begin():
                yield self._cur_session


_db: Database | None = None


def get_db() -> Database:
    return _db


def init_db(url: str, **kwargs) -> Database:
    global _db
    _db = Database(url, **kwargs)
    return _db


def object_session(object: _.Any) -> Session:
    return Session.object_session(object)
