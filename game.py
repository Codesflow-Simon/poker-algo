import itertools
import random
from valuation import check_seven_hand, comapre_hand_values
from players import Random_bot, Human

# player_count = int(input("How many players? "))
player_count = 2

suits = ['s', 'c', 'd', 'h']
faces = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']

# Defining deck and drawing cards (5 + 2 per player):


def draw_next_card(drawn_cards):
    card = drawn_cards.pop(len(drawn_cards)-1)
    return card


def readable_card_name(short_card_name):
    return (short_card_name[0]+"["+short_card_name[1]+"]")

# Storing a list with player object instances


action_dict = {0: 'error', 1: 'folds', 2: 'calls',
               3: '3-bets', 4: 'raises the pot', 5: 'goes all in'}


class Table:

    def __init__(self, blind):
        self.blind = blind

    def holecards(self):
        card1 = draw_next_card(drawn_cards)
        card2 = draw_next_card(drawn_cards)
        return (card1, card2)

    def get_stacks(self):
        return [player.get_stack() for player in self.players]

    def start(self, players):
        self.phase = 'preflop'
        self.players = players
        self.hole_cards = [self.holecards(), self.holecards()]
        self.total_pot = [0, 0]
        self.phase = 'None'
        self.table_cards = []

    def game(self, player_stacks=100):
        self.start(player_stacks)
        prev_stacks = self.get_stacks()
        streets = [self.preflop, self.flop, self.turn, self.river]
        print(self.get_stacks())
        for street in streets:
            [player.show_cards(self.hole_cards[i], self.table_cards)
                for i, player in enumerate(self.players)]
            response = street()
            print('betting over with response {}'.format(response))
            if response in {'none', 'fold'}:
                stacks = self.get_stacks()
                delta = [stacks[i]-prev_stacks[i]
                         for i, _ in enumerate(stacks)]
                print(stacks, delta)
                return stacks, delta
            elif response == 'call':
                continue
            elif response == 'all in':
                break
        self.showdown()
        stacks = self.get_stacks()
        delta = [stacks[i]-prev_stacks[i] for i, _ in enumerate(stacks)]
        print(stacks, delta)
        return stacks, delta

    def betting_round(self, depth=0):
        player_idx = depth % 2
        response = 'none'
        player = self.players[player_idx]
        action = player.action()
        print('player {} {}'.format(player_idx+1, action))
        other_player_idx = -player_idx+1
        if action == 'fold':
            response = self.fold(player_idx, depth)
        elif action == 'call':
            response = self.call(player_idx, depth)
        elif action == 'three-bet':
            response = self.three_bet(player_idx, depth)
        elif action == 'pot raise':
            response = self.pot_raise(player_idx, depth)
        elif action == 'all in':
            response = self.all_in(player_idx)

        print('has response {}'.format(response))
        print('the pot is {}'.format(self.total_pot), '\n')

        if response in {'none', 'fold', 'call'}:
            return response
        response = self.betting_round(depth+1)
        return response

    def bet(self, player_idx, amount):
        real_amount = self.players[player_idx].bet(amount)
        self.total_pot[player_idx] += real_amount

    def fold(self, player_idx, depth):
        if self.total_pot[0] == self.total_pot[1]:
            return self.call(player_idx, depth)
        other_player_idx = -player_idx+1
        other_player = self.players[other_player_idx]
        other_player.add_stack(sum(self.total_pot))
        return 'fold'

    def call(self, player_idx, depth):
        player = self.players[player_idx]
        other_player_idx = -player_idx+1
        amount = self.total_pot[other_player_idx] - \
            self.total_pot[player_idx]
        stack = player.get_stack()
        if stack >= amount:
            self.bet(player_idx, amount)
            return 'call' if depth != 0 else 'raise'
        else:
            self.fold(player_idx)
            return 'fold'

    def three_bet(self, player_idx, depth):
        player = self.players[player_idx]
        other_player_idx = -player_idx+1
        other_player = self.players[other_player_idx]
        stack = player.get_stack()
        other_stack = other_player.get_stack()
        to_call = self.total_pot[other_player_idx] - \
            self.total_pot[player_idx]
        amount = max(
            min(self.blind*3-self.total_pot[player_idx], other_stack, stack), 0)

        if to_call >= amount:
            return self.call(player_idx, depth)
        elif stack >= amount:
            self.bet(player_idx, amount)
            return 'raise'
        elif stack < amount:
            fold(player_idx)
            return 'fold'

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
            return 'raise'
        elif stack < amount:
            fold(player_idx)
            return 'fold'

    def all_in(self, player_idx):
        player = self.players[player_idx]
        other_player_idx = -player_idx+1
        other_player = self.players[other_player_idx]
        stack = player.get_stack()
        other_stack = other_player.get_stack()
        amount = min(stack, other_stack +
                     self.total_pot[other_player_idx]-self.total_pot[player_idx])
        self.bet(player_idx, amount)
        return 'all in'

    # Responses, {0: error, 1: folded, 2:called}(exit responses){3, bet/check(continue), 4, all in-one more turn}

    def preflop(self):
        self.phase = 'preflop'
        self.bet(1, self.blind)
        print('\n', self.phase)
        print('the pot is {}'.format(self.total_pot), '\n')
        return self.betting_round()

    def flop(self):
        self.phase = 'flop'
        (self.card1, self.card2, self.card3) = (draw_next_card(drawn_cards),
                                                draw_next_card(drawn_cards),
                                                draw_next_card(drawn_cards))
        self.flop_cards = (self.card1, self.card2, self.card3)
        self.table_cards = list(self.flop_cards)
        print(self.phase)
        print('the pot is {}'.format(self.total_pot), '\n')
        return self.betting_round()

    def turn(self):
        self.phase = 'turn'
        self.turn_cards = draw_next_card(drawn_cards)
        self.table_cards.append(self.turn_cards)
        print(self.phase)
        print('the pot is {}'.format(self.total_pot), '\n')
        return self.betting_round()

    def river(self):
        self.phase = 'river'
        self.river_cards = draw_next_card(drawn_cards)
        self.table_cards.append(self.river_cards)
        print(self.phase)
        print('the pot is {}'.format(self.total_pot), '\n')
        return self.betting_round()

    def showdown(self):
        values = []
        for player_idx, _ in enumerate(self.players):
            hand = list(itertools.chain(
                self.table_cards, self.hole_cards[player_idx]))
            print(hand)
            best_hand, value = check_seven_hand(hand)
            values.append(value)
            print(best_hand)
        winner = comapre_hand_values(values[0], values[1])
        print(values)
        print(winner)
        print('player {} wins'.format('1' if winner == 'a' else '2'))
        if winner == 'a':
            self.players[0].add_stack(sum(self.total_pot))
        elif winner == 'b':
            self.players[1].add_stack(sum(self.total_pot))


# Add dealer to table:

dealer = Table(2)
stacks = [random.randint(50, 500), random.randint(50, 500)]
for _ in range(10):
    deck = set(itertools.product(faces, suits))
    drawn_cards = random.sample(deck, (5 + 2 * player_count))
    stacks, deltas = dealer.game((Random_bot(stacks[0]),
                          Random_bot(stacks[1])))
    if 0 in stacks:
        break
