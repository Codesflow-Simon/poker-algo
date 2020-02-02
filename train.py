import itertools
import os
import random
import time
from datetime import datetime

from ai import Agent
from players import Human, RandomBot, SmartBot
from valuation import check_seven_hand, compare_hand_values

PLAYER_COUNT = 6

suits = ['s', 'c', 'd', 'h']
faces = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']

# Defining deck and drawing cards (5 + 2 per player):

deck = set(itertools.product(faces, suits))


def draw_next_card(drawn_cards):
    card = drawn_cards.pop(len(drawn_cards)-1)
    return card


class PlayerManager:
    def __init__(self, players):
        self.players = players
        self.reset_pot()

        self.status = ['active' for _ in range(PLAYER_COUNT)]

        self.get_pot = lambda: [player.get_pot() for player in self.players]
        self.get_stacks = lambda: [player.get_stack()
                                   for player in self.players]
        self.get_statuses = lambda: [player.get_status()
                                     for player in self.players]

    def reset_pot(self):
        self.prev_bet = 1
        [player.set_pot(0) for player in self.players]

    def bet(self, player, amount):
        stack = player.get_stack()
        if stack < amount:
            self.bet(player, player.get_stack())
            player.set_status('all_in')
        else:
            player.bet(amount)

    def fold(self, player):
        largest_pot = max(self.get_pot())
        if player.get_pot() == largest_pot:
            self.call(player)
        else:
            player.set_status('out')

    def call(self, player):
        largest_pot = max(self.get_pot())
        amount = largest_pot - player.get_pot()
        self.bet(player, amount)

    def raise_(self, player, multiplier):
        pot = self.get_pot()
        index = self.players.index(player)
        other_stacks = self.get_stacks()
        del other_stacks[index]
        total_funds = list(map(lambda x, y: x+y, other_stacks, pot))
        # print(total_funds

        largest_funds = max(total_funds)
        largest_pot = max(self.get_pot())

        too_call = largest_pot - player.get_pot()

        bet_amount = int(multiplier * sum(pot))
        max_bet = largest_funds - player.get_pot()
        amount = min(max(bet_amount, self.prev_bet, too_call), max_bet)
        # print(f'raise: {amount} made up of {bet_amount}, {self.prev_bet}, {too_call}, {max_bet}')

        amount_raised = amount - too_call
        if amount_raised > 0:
            self.prev_bet = amount_raised

        self.bet(player, amount)


class Table:

    def __init__(self, players, blind=2):
        self.blind = blind
        self.players = players
        self.player_manager = PlayerManager(players)

    def holecards(self):
        card1 = draw_next_card(self.drawn_cards)
        card2 = draw_next_card(self.drawn_cards)
        return (card1, card2)

    def game(self):
        self.phase = 'None'
        self.drawn_cards = random.sample(deck, (5 + 2 * PLAYER_COUNT))

        [player.set_cards(self.holecards()) for player in self.players]
        [player.set_status('active') for player in self.players]
        self.community_cards = []

        prev_stacks = self.player_manager.get_stacks()

        streets = ['preflop', 'flop', 'turn', 'river']

        for street in streets:
            cards = {'preflop': 0, 'flop': 3, 'turn': 1, 'river': 1}[street]
            self.game_round(
                street, cards, first_player=2 if street == 'preflop' else 0)

        self.showdown()

        stacks = self.player_manager.get_stacks()
        change = [stacks[i]-prev_stacks[i] for i, _ in enumerate(stacks)]
        # print(f'change sum: {sum(change)}')
        assert sum(change) <= 0
        [player.game_callback({'reward': change[i]})
            for i, player in enumerate(self.players)]
        return change

    def betting_round(self, depth=0, first_player=0):

        player_index = (depth+first_player) % PLAYER_COUNT
        player = self.players[player_index]

        def check_end():
            end = True
            statuses = self.player_manager.get_statuses()

            eligible_player_count = statuses.count(
                'active')+statuses.count('all_in')
            if eligible_player_count < 2:
                return True

            largest_pot = max(self.player_manager.get_pot())
            for _player in self.players:
                if _player.get_status() == 'active':
                    total_pot = _player.get_pot()
                    if total_pot != largest_pot:
                        end = False

            return end

        # print(self.player_manager.get_statuses())
        # print(depth, check_end(), player_index, self.player_manager.get_stacks(), self.player_manager.get_pot())

        if check_end():
            return

        def rotate_infomation(iterable, length):
            spliced = iterable[:length]
            del iterable[:length]
            for i in spliced:
                iterable.append(i)
            return iterable

        if player.get_status() == 'active':
            stacks = self.player_manager.get_stacks()

            info = {'holes': player.get_cards(),
                    'community': self.community_cards,
                    'stacks': rotate_infomation(stacks, player_index),
                    'pot': rotate_infomation(self.player_manager.get_pot(), player_index),
                    'blind': self.blind,
                    'player_number': player_index,
                    'depth': depth
                    }

            action = player.action(info)

            # print(f'player {player_index+1} {action}s')

            if action == 'fold':
                self.player_manager.fold(player)
            elif action == 'call':
                self.player_manager.call(player)
            elif action == 'qtr_pot':
                self.player_manager.raise_(player, 0.25)
            elif action == 'half_pot':
                self.player_manager.raise_(player, 0.5)
            elif action == 'full_pot':
                self.player_manager.raise_(player, 1)
            elif action == 'two_pot':
                self.player_manager.raise_(player, 2)
            else:
                raise KeyError(f'invalid action: {action}')

            info['action'] = action

            player.betting_callback(info)

        self.betting_round(depth+1, first_player)
        return

    def game_round(self, phase, cards, first_player=0):
        assert phase in {'preflop', 'flop', 'turn', 'river'}

        self.phase = phase
        # print(f'round: {self.phase}')

        if self.phase == 'preflop':
            self.player_manager.bet(self.players[0], self.blind//2)
            self.player_manager.bet(self.players[1], self.blind)

        for _ in range(cards):
            card = draw_next_card(self.drawn_cards)
            self.community_cards.append(card)
        self.betting_round(first_player=first_player)

    def showdown(self):
        pot_caps = []
        for player in self.players:
            if player.get_status() in {'all_in', 'active'}:
                pot_caps.append(player.get_pot())
        pot_caps = list(set(pot_caps))
        pot_caps.sort()

        for i, _ in enumerate(pot_caps):
            pot_caps[i] = pot_caps[i] - sum(pot_caps[:i])

        # print(self.player_manager.get_statuses())
        required_pot = 0
        # print(self.player_manager.get_pot())
        for cap in pot_caps:
            required_pot += cap
            # print(required_pot)
            # print(self.player_manager.get_pot())
            eligible_players = [player for player in self.players if
                                player.get_status() == 'active'or
                                (player.get_status() == 'all_in' and player.get_pot() >= required_pot)]
            # print(cap, eligible_players)
            player_count = len(eligible_players)
            winners = []
            best_hand_value = [0]
            for player in eligible_players:
                hand = list(itertools.chain(
                    self.community_cards, player.get_cards()))
                _, value = check_seven_hand(hand)
                comparison = compare_hand_values(value, best_hand_value)
                if comparison == 'a':
                    winners = [player]
                elif comparison == 'split':
                    winners.append(player)

            [player.add_stack(player_count*cap//len(winners))
             for player in winners]

        self.player_manager.reset_pot()
        # print(self.player_manager.get_stacks())


def play_games(iterations, save_interval, transfer_interval, hyperparam, filename, gpu=True):
    agent = Agent(filename, True, PLAYER_COUNT, hyperparam, gpu=gpu)

    bots = [SmartBot(agent) for _ in range(PLAYER_COUNT)]
    dealer = Table(bots)
    for i in range(iterations):
        if i % 100 == 0:
            print(i)
        [bot.set_stack(random.randint(1, 100)) for bot in bots]
        try:
            dealer.game()
        except (RecursionError, TypeError, AssertionError):
            pass
        if i % transfer_interval == transfer_interval - 1:
            bots[0].transfer_weights()

        if i % save_interval == save_interval-1:
            bots[0].save()
    return agent.loss_ave


if __name__ == '__main__':
    hyperparam = {'mem_length': 100, 'lr': 1.0e-6, 'activation': 'elu',
                  'hidden_layer_size': 50, 'data_extraction_size': 100, 'block_count': 5}
    filename = f'./models/main_{PLAYER_COUNT}'
    play_games(100000, 1000, 100, hyperparam, filename, gpu=False)
