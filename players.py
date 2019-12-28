import asyncio
from itertools import chain
from random import randint

import numpy as np
from numpy.random import choice

from ai import Agent

action_dict = {'fold': 0, 'call': 1,
               'three-bet': 2, 'pot raise': 3}
reverse_action_dict = {value: key for key, value in action_dict.items()}


class Player:
    def __init__(self, stack):
        self.stack = stack
        self.last_action = "none"  # last action taken (check, call etc).

    def bet(self, amount):
        if amount <= self.stack:
            self.stack -= amount
            return amount
        elif amount > self.stack:
            self.stack = 0
            return self.stack
        
    def set_stack(self, value):
        assert type(value) in {int, float}
        self.stack = value

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
    
    def save(self):
        pass

class RandomBot(Player):
    def __init__(self, stack=0, dist=[0.1, 0.5, 0.2, 0.2]):
        super().__init__(stack)
        self.dist = dist

    def action(self, info):
        a = ['fold', 'call', 'three-bet', 'pot raise']
        action = choice(a, p=self.dist)
        return action

class Human(Player):      
    def __init__(self, stack=0):
        super().__init__(stack)

    def action(self, info):
        a = ['fold', 'call', 'three-bet', 'pot raise']
        action = a[int(input('What action? '))]
        return action


agent = Agent('resnet20', True)
class SmartBot(Player):
    def __init__(self, stack=0, model=None):
        super().__init__(stack)
        self.state_action_que = []
        if model:
            self.agent = Agent(model, True)
        else:
            self.agent = agent

    def action(self, info):
        epsilon = 0.1
        greedy = choice([0,1], p=[epsilon, 1-epsilon])
        if greedy:
            action =  self.agent.action(info)
        else:
            action = randint(0,3)
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
        
    def save(self):
        self.agent.save()
