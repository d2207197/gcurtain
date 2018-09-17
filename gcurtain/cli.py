# coding: utf-8
import re
import time

import pendulum as pdl
import pp
from carriage import Optional, Row, Stream
from cleo import Application, Command

from . import calendar, db, http, trello


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
        self.calendar_id = self.argument('calendar_id')
        self.updated_min = pdl.parse(self.argument('updated_min'))

        self.assignee = (
            Optional
            .from_value(self.argument('assignee'))
            .map(lambda assignee: trello.agent.get_member(assignee))
            .get_or_none()
        )

        self.info(
            f'Calendar Id: {self.calendar_id}. '
            f'Events Updated after {self.updated_min}')
        result = calendar.client.list_recent_updated(self.calendar_id,
                                                     self.updated_min)
        pp(result)
        items = result.get('items', [])
        sess = db.Session()
        for event in items:
            if event['status'] == 'confirmed' and \
               event['summary'].startswith('量'):
                self.info(f'Handling event {pp.fmt(event)}')
                self.handle_measuring_event(sess, event)

        sess.commit()
        sess.close()

    def handle_measuring_event(self, sess, event):
        trello_mapping = (
            sess.query(db.TrelloCalendarMapping)
            .filter_by(calendar_event_id=event['id'])
            .one_or_none())

        self.info('Existing Event <-> Card Mappings:')
        pp(trello_mapping)
        if (event['summary'].startswith('量')):
            if trello_mapping is None:
                self.add_measuring_card(
                    sess, event)

            elif trello_mapping.calendar_id != self.calendar_id:
                self.info('Updating measuring card assignee')
                trello_mapping.calendar_id = self.calendar_id
                card = trello.client.get_card(trello_mapping.card_id)
                card.assign(self.assignee)
                card.change_pos('top')
            else:
                self.info(f'Nothing to do for event {event["summary"]}')

    def add_measuring_card(self, sess, event):
        self.info('Adding measuring card')
        measuring_tlist = trello.agent.tlist_of_name_opt('丈量').value
        card_name = re.match(r'量\W*(\w.*)', event['summary']).groups()[0]

        desc = f"丈量: {event['htmlLink']}"
        card = measuring_tlist.add_card(
            card_name,
            position='top',
            desc=desc,
            assign=[self.assignee]
        )
        mapping = db.TrelloCalendarMapping(
            card_id=card.id,
            calendar_id=self.calendar_id,
            calendar_event_type=db.EventType.measuring,
            calendar_event_id=event['id'])
        pp(card.__dict__)
        pp(mapping)
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


class HTTP_Serve(Command):
    """
    Serve HTTP API

    http:serve
        {bind=127.0.0.1 : bind IP address}
        {port=8000 : port }
        {--debugger : use debugger}
    """

    def handle(self):
        bind = self.argument('bind')
        port = int(self.argument('port'))
        use_debugger = self.option('debugger')
        print(use_debugger)
        http.app.serve(
            bind, port,
            use_debugger=use_debugger)


class Event_SyncContinuously(Command):
    """
    Sync event continuously

    event:sync-continuously
        {email_id_mappings* : email and trello ID mapping in '<email>:<id>' format}
        {--first-updated-min= : Min updated time for first sync}


    """

    def handle(self):
        self.email_id_mappings = (
            Stream(self.argument('email_id_mappings'))
            .map(
                lambda s: Row.from_values(
                    s.split(':', 1),
                    fields=('email', 'trello_id')))
            .to_list()
        )

        first_updated_min = (
            Optional
            .from_value(self.option('first-updated-min'))
            .map(pdl.parse)
            .get_or_none()
        )

        self.sync(first_updated_min)

        now = pdl.now(tz='Asia/Taipei')
        now = now.set(second=0, microsecond=0)
        last_minute = now.subtract(minutes=1)
        while True:
            last_minute = last_minute.add(minutes=1)
            self.sync(last_minute)
            time.sleep(60)

    def sync(self, updated_min):
        for email, trello_id in self.email_id_mappings:
            self.call('event:sync-recent-updated', [
                ('calendar_id', email),
                ('updated_min', updated_min.isoformat()),
                ('assignee', trello_id)
            ])


cli_app = Application()
cli_app.add(Event_ListRecentUpdated())
cli_app.add(DB_Init())
cli_app.add(Event_SyncRecentUpdated())
cli_app.add(Card_ListAll())
cli_app.add(List_ListAll())
cli_app.add(DB_recreate())
cli_app.add(HTTP_Serve())
cli_app.add(Event_SyncContinuously())
