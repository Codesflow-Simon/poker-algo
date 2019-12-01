import itertools
import random
from numpy.random import choice

# player_count = int(input("How many players? "))
player_count = 2

suits = ['s', 'c', 'd', 'h']
faces = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']

# Defining deck and drawing cards (5 + 2 per player):

deck = set(itertools.product(faces, suits))


def draw_next_card(drawn_cards):
    card = drawn_cards.pop(len(drawn_cards)-1)
    return card


def readable_card_name(short_card_name):
    return (short_card_name[0]+"["+short_card_name[1]+"]")


drawn_cards = random.sample(deck, (5 + 2 * player_count))

# Storing a list with player object instances

players = []
response_dict = {0: 'error', 1:'folds', 2: 'calls/checks', 3: 'raises', 4:'goes all in'}
action_dict = {0: 'error', 1:'folds', 2: 'calls', 3: '3-bets', 4:'raises the pot', 5: 'goes all in'}
phase_dict = {'pregame': 0, 'preflop': 1}


class Players:

    def __init__(self, stack):
        self.stack = stack
        self.last_action = "none"  # last action taken (check, call etc).
        self.reset()

    def reset(self):
        self.cards = ()
        self.prev_actions = []
        self.in_pot = 0

    def holecards(self):
        card1 = draw_next_card(drawn_cards)
        card2 = draw_next_card(drawn_cards)
        self.cards = (self.card1, self.card2)

    def action(self, table_info={}):
        dist = [0.3, 0.2, 0.3, 0.15, 0.05]
        a = [i+1 for i in list(range(0,5))]
        action = choice(a, p=dist)
        self.prev_actions.append(action)
        return action

    def bet(self, amount):
        if amount <= self.stack:
            self.in_pot += amount
            self.stack -= amount
            return amount
        elif amount > self.stack:
            self.in_pot += self.stack
            self.stack = 0
            return self.stack

    def get_stack(self):
        return self.stack

    def get_in_pot(self):
        return self.in_pot

    def add_stack(self, amount):
        self.stack += amount


class Table:

    def __init__(self, blind):
        self.blind = blind

    def start(self):
        self.phase = 'preflop'
        self.players = (Players(100), Players(100))
        self.total_pot = [0, 0]
        self.phase = 'None'

    def bet(self, player_idx, amount):
        real_amount = self.players[player_idx].bet(amount)
        self.total_pot[player_idx] += real_amount


    def fold(self, player_idx, depth):
        print(self.total_pot[0], self.total_pot[1])
        if self.total_pot[0] == self.total_pot[1]:
            return self.call(player_idx, depth)
        other_player_idx = -player_idx+1
        other_player = self.players[other_player_idx]
        other_player.add_stack(sum(self.total_pot))
        return 1

    def call(self, player_idx, depth):
        player = self.players[player_idx]
        other_player_idx = -player_idx+1
        amount = self.total_pot[other_player_idx] - \
            self.total_pot[player_idx]
        stack = player.get_stack()
        if stack >= amount:
            self.bet(player_idx, amount)
            return 2 if depth != 0 else 3
        else:
            fold(player_idx)
            return 1


    def three_bet(self, player_idx, depth):
        player = self.players[player_idx]
        other_player_idx = -player_idx+1
        other_player = self.players[other_player_idx]
        stack = player.get_stack()
        other_stack = other_player.get_stack()
        to_call = self.total_pot[other_player_idx] - \
            self.total_pot[player_idx]
        amount = max(min(self.blind * 3 - self.total_pot[player_idx], other_stack, stack), 0)

        if to_call >= amount:
            return self.call(player_idx, depth)
        elif stack >= amount:
            self.bet(player_idx, amount)
            return 3
        elif stack < amount:
            fold(player_idx)
            return 1


    def pot_raise(self, player_idx, depth):
        player = self.players[player_idx]
        other_player_idx = -player_idx+1
        other_player = self.players[other_player_idx]
        stack = player.get_stack()
        other_stack = other_player.get_stack()
        to_call = self.total_pot[other_player_idx] - \
            self.total_pot[player_idx]
        amount = min(sum(self.total_pot), other_stack, stack)

        if to_call >= amount:
            return self.call(player_idx, depth)
        elif stack >= amount:
            self.bet(player_idx, amount)
            return 3
        elif stack < amount:
            fold(player_idx)
            return 1

    def all_in(self, player_idx):
        player = self.players[player_idx]
        other_player_idx = -player_idx+1
        other_player = self.players[other_player_idx]
        stack = player.get_stack()
        other_stack = other_player.get_stack()

        amount = min(stack, other_stack+self.total_pot[other_player_idx]-self.total_pot[player_idx])
        self.bet(player_idx, amount)
        return 4

    # Responses, {0: error, 1: folded, 2:called}(exit responses){3, bet/check(continue), 4, all in-one more turn}
    def betting_round(self, depth=0, all_in_state=0):
        player_idx = depth % 2
        response = 0
        player = self.players[player_idx]
        action = player.action()
        print('player {} {}'.format(player_idx+1,action_dict[action]))
        other_player_idx = -player_idx+1
        all_in_state = 2 if all_in_state == 1 else 0
        if action == 1:
            response = self.fold(player_idx, depth)
        elif action == 2:
            response = self.call(player_idx, depth)
        elif action == 3:
            response = self.three_bet(player_idx, depth)
        elif action == 4:
            response = self.pot_raise(player_idx, depth)
        elif action == 5:
            response = self.all_in(player_idx)
            all_in_state = 1 if all_in_state == 0 else all_in_state

        print('has response {}'.format(response_dict[response]))
        print('the pot is {}'.format(self.total_pot), '\n')
        
        if all_in_state == 2:
            print('betting round over')
            return 2
        elif response in {0,1,2}:
            print('betting round over')
            return response
        self.betting_round(depth+1, all_in_state)

    def preflop(self):
        self.street_pot = 0
        self.phase = 'preflop'
        self.bet(0, self.blind//2)
        self.bet(1, self.blind)
        print('the pot is {}'.format(self.total_pot), '\n')
        self.betting_round()

    def flop(self):
        (self.card1, self.card2, self.card3) = (draw_next_card(drawn_cards),
                                                draw_next_card(drawn_cards),
                                                draw_next_card(drawn_cards))
        self.flop = (self.card1, self.card2, self.card3)
        # print(self.flop)

    def turn(self):
        self.card = draw_next_card(drawn_cards)
        self.turn = self.card
        # print(self.turn)

    def river(self):
        self.card = draw_next_card(drawn_cards)
        self.river = self.card
        # print(self.river)

# Add dealer to table:


dealer = Table(2)
dealer.start()
dealer.preflop()

dealer.flop()
dealer.turn()
dealer.river()
