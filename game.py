import itertools
import os
import random
import time
from collections import deque

import wandb

from ai import Agent
from players import Human, RandomBot, SmartBot
from valuation import check_seven_hand, compare_hand_values

# player_count = int(input("How many players? "))
player_count = 2

suits = ['s', 'c', 'd', 'h']
faces = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']

# Defining deck and drawing cards (5 + 2 per player):

deck = set(itertools.product(faces, suits))

def draw_next_card(drawn_cards):
    card = drawn_cards.pop(len(drawn_cards)-1)
    return card

class Table:

    def __init__(self, blind):
        self.blind = blind

    def holecards(self):
        card1 = draw_next_card(self.drawn_cards)
        card2 = draw_next_card(self.drawn_cards)
        return (card1, card2)

    def get_stacks(self):
        return [player.get_stack() for player in self.players]

    def game(self, players):
        self.phase = 'None'
        self.drawn_cards = random.sample(deck, (5 + 2 * player_count))

        self.players = players
        self.hole_cards = [self.holecards(), self.holecards()]
        self.community_cards = []

        self.total_pot = [0, 0]
        prev_stacks = self.get_stacks()

        completed = 0
        streets = [self.preflop, self.flop, self.turn, self.river]
        for street in streets:
            response = street()
            if response in {'none', 'fold'}:
                completed = 1
                break
            elif response == 'call':
                continue
            elif response == 'all in':
                break
        if not(completed):
            self.showdown()
        stacks = self.get_stacks()
        deltas = [stacks[i]-prev_stacks[i] for i, _ in enumerate(stacks)]
        assert sum(deltas) == 0
        [player.game_callback({'reward': deltas[i]})
         for i, player in enumerate(self.players)]
        return stacks, deltas

    def betting_round(self, depth=0, first_player=0):
        player_idx = (depth+first_player) % 2
        other_player_idx = -player_idx + 1
        player = self.players[player_idx]

        stacks = self.get_stacks()
        info = {'player_holes': self.hole_cards[player_idx],
                'opponents_holes': self.hole_cards[other_player_idx],
                'community': self.community_cards,
                'player_stack': stacks[player_idx],
                'opponents_stack': stacks[other_player_idx],
                'player_pot': self.total_pot[player_idx],
                'opponents_pot': self.total_pot[other_player_idx],
                'blind': self.blind,
                'player_number': player_idx,
                'depth': depth
                }
        
        action = player.action(info)

        if action == 'fold':
            response = self.fold(player_idx, depth)
        elif action == 'call':
            response = self.call(player_idx, depth)
        elif action == 'three-bet':
            response = self.three_bet(player_idx, depth)
        elif action == 'pot raise':
            response = self.pot_raise(player_idx, depth)
        else:
            raise KeyError(f'invalid action: {action}')
        
        info['action'] = action
        player.betting_callback(info)

        if response in {'fold', 'call'}:
            return response
        response = self.betting_round(depth+1, first_player)
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
        
        stack = player.get_stack()
        
        amount = self.total_pot[other_player_idx] - \
            self.total_pot[player_idx]
            
        if stack >= amount:
            self.bet(player_idx, amount)
            return 'call' if depth != 0 else 'raise'
        else:
            self.fold(player_idx, depth)
            return 'fold'

    def three_bet(self, player_idx, depth):
        player = self.players[player_idx]
        other_player_idx = -player_idx+1
        other_player = self.players[other_player_idx]
        
        stack = player.get_stack()
        other_stack = other_player.get_stack()
        
        in_pot = self.total_pot[player_idx]
        opp_in_pot = self.total_pot[other_player_idx]
        
        amount = 2*max(in_pot, opp_in_pot)
        
        max_bet = other_stack+self.total_pot[player_idx]-self.total_pot[other_player_idx]

        amount = max(min(amount, max_bet, stack), 0)

        if stack == amount or amount==0:
            return self.call(player_idx, depth)
        elif stack > amount:
            self.bet(player_idx, amount)
            return 'raise'
        elif stack < amount:
            self.fold(player_idx, depth)
            return 'fold'

    def pot_raise(self, player_idx, depth):
        player = self.players[player_idx]
        other_player_idx = -player_idx+1
        other_player = self.players[other_player_idx]
        
        stack = player.get_stack()
        other_stack = other_player.get_stack()
        
        bet_amount = sum(self.total_pot)
        max_bet = other_stack+self.total_pot[player_idx]-self.total_pot[other_player_idx]

        amount = max(min(bet_amount, max_bet, stack), 0)


        if stack == amount or amount==0:
            return self.call(player_idx, depth)
        elif stack > amount:
            self.bet(player_idx, amount)
            return 'raise'
        elif stack < amount:
            self.fold(player_idx, depth)
            return 'fold'

    def preflop(self):
        self.phase = 'preflop'
        self.bet(0, self.blind)
        return self.betting_round(first_player=1)

    def flop(self):
        self.phase = 'flop'
        (self.card1, self.card2, self.card3) = (draw_next_card(self.drawn_cards),
                                                draw_next_card(self.drawn_cards),
                                                draw_next_card(self.drawn_cards))
        self.flop_cards = (self.card1, self.card2, self.card3)
        self.community_cards = list(self.flop_cards)
        return self.betting_round()

    def turn(self):
        self.phase = 'turn'
        self.turn_cards = draw_next_card(self.drawn_cards)
        self.community_cards.append(self.turn_cards)
        return self.betting_round()

    def river(self):
        self.phase = 'river'
        self.river_cards = draw_next_card(self.drawn_cards)
        self.community_cards.append(self.river_cards)
        return self.betting_round()

    def showdown(self):
        values = []
        for player_idx in range(2):
            hand = list(itertools.chain(
                self.community_cards, self.hole_cards[player_idx]))
            best_hand, value = check_seven_hand(hand)
            values.append(value)
        winner = compare_hand_values(values[0], values[1])
        if winner == 'a':
            self.players[0].add_stack(sum(self.total_pot))
        elif winner == 'b':
            self.players[1].add_stack(sum(self.total_pot))
        elif winner == 'split':
            self.players[0].add_stack(sum(self.total_pot)/2)
            self.players[1].add_stack(sum(self.total_pot)/2)

# Add dealer to table:

def play_games(iterations=1, save_interval=1):
    winnings=[0,0]
    bots = (SmartBot(), SmartBot())
    for i in range(iterations):
        # print(i)
        dealer = Table(1)
        [bot.set_stack(random.randint(1, 200)) for bot in bots]
        stacks, deltas = dealer.game(bots)
        winnings = [winnings[i]+deltas[i] for i in range(2)]
        if i%save_interval == save_interval-1:
            bots[0].save()

if __name__=='__main__':
    play_games(1000000,1000)
