# coding: utf-8
import re

import pendulum as pdl
import pp
from cleo import Application, Command

from . import calendar, db, trello


class Event_ListRecentUpdated(Command):
    """
    List recently updated events

    event:list-recent-updated
        {calendar_id : calendar Id.}
        {updated_min : Min updated time}
    """

    def handle(self):
        calendar_id = self.argument('calendar_id')
        updated_min = self.argument('updated_min')

        updated_min = pdl.parse(updated_min)

        self.info(
            f'Calendar Id: {calendar_id}. Events Updated after {updated_min}')
        result = calendar.client.list_recent_updated(calendar_id, updated_min)
        pp(result)


class Event_SyncRecentUpdated(Command):
    """
    Sync recently updated events to Trello

    event:sync-recent-updated
        {calendar_id : calendar Id.}
        {updated_min : Min updated time}
        {assignee? : trello user ID to assign}
    """

    def handle(self):
        calendar_id = self.argument('calendar_id')
        updated_min = self.argument('updated_min')
        assignee = self.argument('assignee')
        if assignee is not None:
            assignee = trello.client.get_member('may21282655')

        updated_min = pdl.parse(updated_min)
        self.info(
            f'Calendar Id: {calendar_id}. Events Updated after {updated_min}')
        self.sync(calendar_id, updated_min, assignee)

    def sync(self, calendar_id, updated_min, assignee):
        result = calendar.client.list_recent_updated(calendar_id, updated_min)
        self.info('Calendar ')
        pp.fmt(result)
        items = result.get('items', [])

        sess = db.Session()

        for event in items:
            event_id = event['id']
            if event['status'] == 'confirmed':
                trello_mapping = (
                    sess.query(db.TrelloCalendarMapping)
                    .filter_by(calendar_event_id=event_id)
                    .one_or_none())

                self.info(pp.fmt(trello_mapping))
                if (trello_mapping is None and
                        event['summary'].startswith('量')):

                    self.add_measuring_card(sess, calendar_id, event, assignee)

        sess.commit()
        sess.close()

    def add_measuring_card(self, sess, calendar_id, event, assignee):
        self.info('adding measuring card')
        measuring_tlist = trello.agent.tlist_of_name_opt('丈量').value
        card_name = re.match(r'量\W*(\w.*)', event['summary']).groups()[0]

        desc = f"丈量: {event['htmlLink']}"
        card = measuring_tlist.add_card(
            card_name,
            position='top',
            desc=desc,
            assign=[assignee]
        )
        mapping = db.TrelloCalendarMapping(
            card_id=card.id,
            calendar_id=calendar_id,
            calendar_event_type=db.EventType.measuring,
            calendar_event_id=event['id'])
        self.info(pp.fmt(card.__dict__))
        self.info(pp.fmt(mapping))
        sess.add(mapping)


class DB_Init(Command):
    """
    Initialize Database

    db:init
    """

    def handle(self):
        db.create_all()


class DB_recreate(Command):
    '''
    Truncate Database

    db:recreate
    '''

    def handle(self):
        db.drop_all()
        db.create_all()


class Card_ListAll(Command):
    """
    List all Cards

    card:list-all
    """

    def handle(self):
        for card in trello.board.all_cards():
            pp(card.__dict__)


class List_ListAll(Command):
    """
    List all Lists

    list:list-all
    """

    def handle(self):
        trello.board.all_lists()
        for tlist in trello.board.list_lists():
            pp(tlist.__dict__)


cli_app = Application()
cli_app.add(Event_ListRecentUpdated())
cli_app.add(DB_Init())
cli_app.add(Event_SyncRecentUpdated())
cli_app.add(Card_ListAll())
cli_app.add(List_ListAll())
cli_app.add(DB_recreate())
