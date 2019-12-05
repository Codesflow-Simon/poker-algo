from numpy.random import choice
from random import randint
from ai import q_values, memorise, intergerify_cards, train
from itertools import chain
import numpy as np

action_dict = {'fold': 0, 'call': 1,
               'three-bet': 2, 'pot raise': 3, 'all in': 4}
reverse_action_dict = {value: key for key, value in action_dict.items()}


class Player:
    def __init__(self, stack):
        self.stack = stack
        self.last_action = "none"  # last action taken (check, call etc).
        self.reset()

    def reset(self):
        self.prev_actions = []
        self.in_pot = 0

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

    def betting_callback(self, info):
        pass

    def game_callback(self, info):
        pass


class RandomBot(Player):
    def __init__(self, stack, dist=[0.1, 0.5, 0.2, 0.1, 0.1]):
        super(RandomBot, self).__init__(stack)
        self.dist = dist

    def action(self, table_info={}):
        a = ['fold', 'call', 'three-bet', 'pot raise', 'all in']
        action = choice(a, p=self.dist)
        self.prev_actions.append(action)
        return action


class Human(Player):
    def action(self, info={}):
        a = ['fold', 'call', 'three-bet', 'pot raise', 'all in']
        p = input('action: ')
        action = a[int(p)]
        self.prev_actions.append(action)
        return action

    def betting_callback(self, info={}):
        print('Your hole cards: {}, table cards: {}'.format(
            info['holes'], info['community']))


class SmartBot(Player):
    def __init__(self, stack):
        super().__init__(stack)
        self.state_action_que = []

    def action(self, info={}):
        epsilon = 0.01
        greedy = choice([0,1], p=[epsilon, 1-epsilon])
        if greedy:
            cards = tuple(chain(info['holes'], info['community']))
            state = intergerify_cards(cards)
            state = state.reshape(1,-1)
            action_qs = q_values(state)
            action = np.argmax(action_qs)
        else:
            action = randint(0,4)
        return reverse_action_dict[action]

    def betting_callback(self, info={}):
        state = intergerify_cards(chain(info['holes'], info['community']))
        action = action_dict[info['action']]
        self.state_action_que.append((state, action))

    def game_callback(self, info):
        reward = info['reward_sum']
        for state, action in self.state_action_que:
            memorise(state, action, reward)
        train()
