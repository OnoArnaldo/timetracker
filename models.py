import typing as _
from datetime import datetime, timedelta, time
from enum import StrEnum
import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, mapped_column as column, Mapped, relationship
from db import get_db


def create_all() -> None:
    db = get_db()
    Base.metadata.create_all(db.engine)


class State(StrEnum):
    NEW = 'new'
    INPROGRESS = 'in-progress'
    CONCLUDED = 'concluded'
    DELETED = 'deleted'


class Base(DeclarativeBase):
    id: Mapped[int] = column(primary_key=True)
    created_at: Mapped[datetime] = column(default=datetime.now)
    updated_at: Mapped[datetime] = column(default=datetime.now, onupdate=datetime.now)


class Project(Base):
    __tablename__ = 'project'

    name: Mapped[str] = column(sa.String(200), index=True, nullable=False)
    state: Mapped[State] = column(sa.Enum(State), default=State.NEW)

    tasks: Mapped[_.List['Task']] = relationship(back_populates='project',
                                                 order_by='Task.name',
                                                 primaryjoin=f'and_(Project.id == Task.project_id, '
                                                             f'Task.state != "{State.DELETED!s}")')

    def __repr__(self) -> str:
        return (f'Project(id: {self.id!r}, '
                f'name: {self.name!r}, '
                f'state: {self.state!s}, '
                f'created_at: {self.created_at!s}, '
                f'updated_at: {self.updated_at!s})')

    @classmethod
    def find_all(cls) -> _.Generator['Project', None, None]:
        cmd = sa.select(cls).where(cls.state != State.DELETED).order_by(cls.name)
        session = get_db().cur_session
        for proj in session.execute(cmd).all():
            yield proj[0]

    @classmethod
    def find_name(cls, name: str) -> 'Project|None':
        cmd = sa.select(cls).where(cls.name == name, cls.state != State.DELETED).limit(1)
        session = get_db().cur_session
        for proj in session.execute(cmd).first() or []:
            return proj

    @property
    def elapsed_seconds(self) -> int:
        return sum(t.elapsed_seconds for t in self.tasks)

    @property
    def today_seconds(self) -> int:
        return sum(t.today_seconds for t in self.tasks)

    @property
    def start(self) -> datetime:
        if len(self.tasks) != 0:
            return min(t.start for t in self.tasks)
        return datetime.min

    @property
    def stop(self):
        if len(self.tasks) != 0:
            return max(t.start for t in self.tasks)
        return datetime.min

    @property
    def elapsed_time(self) -> str:
        elapsed = datetime(2000, 1, 1) + timedelta(seconds=self.elapsed_seconds)
        return elapsed.strftime('%H:%M:%S')


class Task(Base):
    __tablename__ = 'task'

    name: Mapped[str] = column(sa.String(200), index=True, nullable=False)
    state: Mapped[State] = column(sa.Enum(State), default=State.NEW)

    project_id: Mapped[int] = column(sa.ForeignKey('project.id'), nullable=False)
    project: Mapped['Project'] = relationship(back_populates='tasks')
    entries: Mapped[_.List['TaskEntry']] = relationship(back_populates='task')

    # __table_args__ = (sa.UniqueConstraint(project_id, name),)

    def __repr__(self) -> str:
        return (f'Task('
                f'id: {self.id!r}, '
                f'project_id: {self.project_id!r}, '
                f'name: {self.name!r}, '
                f'created_at: {self.created_at!s}, '
                f'updated_at: {self.updated_at!s})')

    @classmethod
    def find(cls, task_id: int) -> 'Task':
        cmd = (sa.select(cls)
               .where(cls.id == task_id, cls.state != State.DELETED)
               .limit(1))
        session = get_db().cur_session
        for task in session.execute(cmd).first() or []:
            return task

    @classmethod
    def find_name(cls, project_id: int, name: str) -> 'Task':
        cmd = (sa.select(cls)
               .where(cls.name == name, cls.project_id == project_id, cls.state != State.DELETED)
               .limit(1))
        session = get_db().cur_session
        for task in session.execute(cmd).first() or []:
            return task

    @property
    def elapsed_seconds(self) -> int:
        return sum(e.elapsed_seconds or 0 for e in self.entries)

    @property
    def today_seconds(self) -> int:
        return sum(e.today_seconds or 0 for e in self.entries)

    @property
    def start(self) -> datetime:
        if len(self.entries) != 0:
            return min(e.start for e in self.entries)
        return datetime.min

    @property
    def stop(self):
        if len(self.entries) != 0:
            return max(e.start for e in self.entries)
        return datetime.min

    @property
    def elapsed_time(self) -> str:
        elapsed = datetime(2000, 1, 1) + timedelta(seconds=self.elapsed_seconds)
        return elapsed.strftime('%H:%M:%S')


class TaskEntry(Base):
    __tablename__ = 'task_entry'

    start: Mapped[datetime] = column(sa.DateTime, default=datetime.now)
    stop: Mapped[datetime] = column(sa.DateTime, default=datetime.now)
    manual: Mapped[bool] = column(sa.Boolean, default=False)

    task_id: Mapped[int] = column(sa.ForeignKey('task.id'), nullable=False)
    task: Mapped['Task'] = relationship(back_populates='entries')

    def __repr__(self) -> str:
        return (f'TaskEntry('
                f'id: {self.id!r}, '
                f'task_id: {self.task_id!r}, '
                f'start: {self.start!s}, '
                f'stop: {self.stop!s}, '
                f'elapsed_seconds: {self.elapsed_seconds!r}, '
                f'created_at: {self.created_at!s}, '
                f'updated_at: {self.updated_at!s})')

    @classmethod
    def find(cls, entry_id: int) -> 'TaskEntry|None':
        cmd = sa.select(cls).where(cls.id == entry_id).limit(1)
        session = get_db().cur_session
        for entry in session.execute(cmd).first() or []:
            return entry

    @property
    def elapsed_seconds(self) -> int:
        return int((self.stop - self.start).total_seconds())

    @property
    def elapsed_time(self) -> str:
        elapsed = datetime(2000, 1, 1) + timedelta(seconds=self.elapsed_seconds or 0)
        return elapsed.strftime('%H:%M:%S')

    @property
    def today_seconds(self) -> int:
        today_start = datetime.combine(datetime.today(), time(0))
        today_end = datetime.combine(datetime.today(), time(23, 59, 59, 999999))

        start = stop = today_start

        if today_start <= self.start <= today_end:
            start = self.start

        if today_start <= self.stop <= today_end:
            stop = self.stop

        return int((stop - start).total_seconds())

    def set_stop(self) -> None:
        self.stop = datetime.now()

    def set_start(self) -> None:
        self.start = datetime.now()
