from numpy.random import choice

class Player:
    def __init__(self, stack):
        self.stack = stack
        self.last_action = "none"  # last action taken (check, call etc).
        self.reset()

    def reset(self):
        self.prev_actions = []
        self.in_pot = 0

    def bet(self, amount):
        print(amount, self.stack)
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
    
    def show_cards(self, hole, cards):
        pass

class Random_bot(Player):
    def __init__(self, stack, dist=[0.1, 0.5, 0.2, 0.1, 0.1]):
        super(Random_bot, self).__init__(stack)
        self.dist = dist

    def action(self, table_info={}):
        a = ['fold', 'call', 'three-bet', 'pot raise', 'all in']
        action = choice(a, p=self.dist)
        self.prev_actions.append(action)
        return action

class Human(Player):
    def action(self, table_info={}):
        a = ['fold', 'call', 'three-bet', 'pot raise', 'all in']
        p = input('action: ')
        action = a[int(p)]
        self.prev_actions.append(action)
        return action
    
    def show_cards(self, hole, cards):
        print('Your hole cards: {}, table cards: {}'.format(hole, cards))