
from carriage import Stream
from trello import TrelloClient

from .core import conf

with conf.declare_group('trello') as trello:
    trello.key = 'trello-key'
    trello.token = 'trello-token'
    trello.board_id = '29GNRTiD'


class TrelloAgent:
    def __init__(self, board):
        self.board = board
        self.update_tlists()

    def update_tlists(self):
        self.tlists = self.board.all_lists()

    def tlist_of_name_opt(self, name):
        return Stream(self.tlists).find_opt(lambda tlist: name in tlist.name)


client = TrelloClient(
    api_key=conf.trello.key,
    api_secret=conf.trello.token)

agent = TrelloAgent(client.get_board(conf.trello.board_id))

# if __name__ == '__main__':
#     all_boards = client.list_boards()
#     for board in all_boards:
#         print(board.id, board.name)

#     board = client.get_board(conf.trello.board)
#     cards = board.all_cards()
#     name_to_card_map = (Stream(cards)
#                         .map(lambda card: (card.name, card))
#                         .to_map())
#     print(name_to_card_map)
#     reservation_tlist = (
#         Stream(board.all_lists())
#         .find(lambda tlist: '預約' in tlist.name))
#     print(reservation_tlist.list_cards())
