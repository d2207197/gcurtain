import enum

from sqlalchemy import Column, Enum, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .core import conf


class EventType(enum.Enum):
    measuring = 1
    selection = 2
    installation = 3


with conf.declare_group('db') as cg:
    cg.uri = 'sqlite:///:memory:'

engine = create_engine(conf.db.uri, echo=False)

Base = declarative_base()

Session = sessionmaker(bind=engine)


class TrelloCalendarMapping(Base):
    __tablename__ = 'trello_calendar_event_mapping'

    calendar_event_id = Column(String(128), primary_key=True)
    calendar_event_type = Column(Enum(EventType))
    calendar_id = Column(String(64))
    card_id = Column(String(32))

    def __repr__(self):
        return (f'<{__name__}.{type(self).__qualname__} '
                f'card_id={self.card_id!r} '
                f'calendar_event_type={self.calendar_event_type!r} '
                f'calendar_id={self.calendar_id!r} '
                f'calendar_event_id={self.calendar_event_id!r}>'
                )


def create_all():
    Base.metadata.create_all(engine)


def drop_all():
    Base.metadata.drop_all(engine)
