import asyncio
from itertools import chain
from random import randint

import numpy as np
from numpy.random import choice

from ai import Agent

action_dict = {'fold': 0, 'call': 1,
               'qtr_pot': 2, 'half_pot': 3, 'full_pot': 4, 'two_pot': 5}
reverse_action_dict = {value: key for key, value in action_dict.items()}

class Player:
    def __init__(self):
        self.stack = 0
        self.pot = 0
        self.status = ''
        self.cards = ()
        

    def bet(self, amount):
        assert type(amount) in {int, np.int32}
        assert self.stack >= amount
        self.stack -= amount
        self.pot += amount
        return amount
    
    def set_cards(self, cards):
        assert type(cards) in {list, tuple}
        self.cards = tuple(cards)
        
    def get_cards(self):
        return self.cards
        
    def set_stack(self, value):
        assert type(value) in {int, np.int32}
        self.stack = value

    def get_stack(self):
        return self.stack

    def add_stack(self, x):
        assert type(x) in {int, np.int32}
        self.stack += x
        return self.stack
        
    def set_pot(self, x):
        assert type(x) in {int, np.int32}
        self.pot = x
        return self.pot

    def get_pot(self):
        return self.pot
    
    def set_status(self, x):
        assert x in {'', 'out', 'active', 'all_in'}
        self.status = x
        return self.status
        
    def get_status(self):
        return self.status
    
    def betting_callback(self, info):
        pass

    def game_callback(self, info):
        pass
    
    def save(self):
        pass

class RandomBot(Player):
    def __init__(self, stack=0, dist=[0.1, 0.5, 0.2, 0.2]):
        super().__init__(stack)
        self.dist = dist

    def action(self, info):
        a = list(action_dict.keys())
        action = choice(a, p=self.dist)
        return action

class Human(Player):      
    def __init__(self, stack=0):
        super().__init__(stack)

    def action(self, info):
        action = reverse_action_dict[int(input('What action? '))]
        return action

class SmartBot(Player):
    def __init__(self, agent, stack=0):
        super().__init__()
        self.state_action_que = []
        self.agent = agent

    def action(self, info):
        epsilon = 0.1
        greedy = choice([0,1], p=[epsilon, 1-epsilon])
        if greedy:
            action =  self.agent.action(info)
        else:
            action = randint(0,5)
        return reverse_action_dict[action]

    def betting_callback(self, info):
        state =  self.agent.create_state(info)
        action = action_dict[info['action']]
        self.state_action_que.append((state, action))

    def game_callback(self, info):
        reward = info['reward']
        for state, action in self.state_action_que:
             self.agent.memorise(state, action, reward)
        self.agent.train()
        
    def transfer_weights(self):
        self.agent.transfer_weights()
        
    def save(self):
        self.agent.save()
