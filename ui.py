from collections import deque
from itertools import chain
from tkinter import *

import numpy as np

from ai import Agent, intergerify_cards

class CardButton():
    def __init__(self, master, rank, suit):
        self.rank = rank
        self.suit = suit
        self.card = rank + suit
        self.colour = 'red' if suit in {'h', 'd'} else 'black'
        self.button = Button(master, text=f'{rank}{suit}', bg=self.colour, fg='white', width=3)
        self.button.bind('<Button-1>', self.cycle)
        self.button.bind('<Button-3>', self.cycle)
        
    def cycle(self, event):
        if event.num == 1:
            try:
                removeable = hole_cards[0]
            except IndexError:
                removeable = 'na'
            if self.card in community_cards:
                community_cards.remove(self.card)
                hole_cards.append(self.card)
            elif self.card not in hole_cards:
                hole_cards.append(self.card)
            else:
                hole_cards.remove(self.card)
            update_card(removeable)
            update_card(self.card)
            
        elif event.num == 3:
            try:
                removeable = community_cards[0]
            except IndexError:
                removeable = 'na'
            if self.card in hole_cards:
                hole_cards.remove(self.card)
                community_cards.append(self.card)
                self.colour = 'blue'
            elif self.card not in community_cards:
                community_cards.append(self.card)
                self.colour = 'blue'
            else:
                community_cards.remove(self.card)
                self.colour = 'red' if suit in {'h', 'd'} else 'black'
            update_card(removeable)
            update_card(self.card)
                    
    def pack(self):
        self.button.pack()
        
    def update(self):
        if self.card in hole_cards:
            self.colour = 'green'
        elif self.card  in community_cards:
            self.colour = 'blue'
        else:
            self.colour = 'red' if self.suit in {'h', 'd'} else 'black'
        self.button.configure(bg=self.colour)

root = Tk()
input_screen = Frame()
cards = Frame(input_screen)
suit_columns = {}
suits = ['s', 'c', 'd', 'h']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']

hole_cards = deque([], 2)
community_cards = deque([], 5)

card_objects = {}

def update_card(card):
    if card is not 'na':
        card_objects[card].update()

for suit in suits:
    suit_columns[suit] = Frame(cards)
    for rank in ranks:
        button = CardButton(suit_columns[suit], rank, suit)
        card_objects[rank+suit] = button
        button.pack()
    suit_columns[suit].pack(side='left')
cards.pack()

info = Label(input_screen, text='Green = Hole card (left click) \n Blue = Community (right click)')
info.pack()

player_stack = IntVar()
player_stack_frame = Frame(input_screen)
Label(player_stack_frame, text='Player stack to blind ratio').pack(side='left')
Spinbox(player_stack_frame, textvariable=player_stack, from_=0, to=200).pack(side='left')
Scale(player_stack_frame, variable=player_stack, orient='horizontal', to=200, length=200).pack(side='right')
player_stack_frame.pack(side='top')

opponents_stack = IntVar()
opponents_stack_frame = Frame(input_screen)
Label(opponents_stack_frame, text='Opponents stack to blind ratio').pack(side='left')
Spinbox(opponents_stack_frame, textvariable=opponents_stack, from_=0, to=200).pack(side='left')
Scale(opponents_stack_frame, variable=opponents_stack, orient='horizontal', to=200, length=200).pack(side='right')
opponents_stack_frame.pack(side='top')

pot = IntVar()
pot_frame = Frame(input_screen)
Label(pot_frame, text='pot to blind ratio').pack(side='left')
Spinbox(pot_frame, textvariable=pot, from_=0, to=200).pack(side='left')
Scale(pot_frame, variable=pot, orient='horizontal', to=200, length=200).pack(side='right')
pot_frame.pack(side='top')

bet = IntVar()
bet_frame = Frame(input_screen)
Label(pot_frame, text='current bet (opponent) to blind ratio').pack(side='left')
Spinbox(pot_frame, textvariable=bet, from_=0, to=200).pack(side='left')
Scale(pot_frame, variable=bet, orient='horizontal', to=200, length=200).pack(side='right')
bet_frame.pack(side='top')

is_dealer = IntVar()
dealer_frame = Frame(input_screen)
Label(dealer_frame, text='dealer').pack(side='left')
Checkbutton(dealer_frame, variable=is_dealer).pack()
dealer_frame.pack(side='top')

input_screen.pack(side='left')

agent = Agent('resnet20', False, False)

def compute():
    state = intergerify_cards(chain(hole_cards, community_cards))
    state.append(player_stack.get())
    state.append(opponents_stack.get())
    state.append(pot.get())
    state.append(bet.get())
    state.append(int(not(is_dealer.get())))
    state = np.array(state, dtype=np.float32)
    predictions = agent.predict(state.reshape(1, -1))[0]
    fold.set(predictions[0])
    call.set(predictions[1])
    three_bet.set(predictions[2])
    raise_.set(predictions[3])
    action = np.argmax(predictions)
    action_dict = {0: 'fold', 1:'call', 2:'three_bet', 3:'raise'}
    recommended.set(action_dict[action])
    root.after(32, compute)
    

output_screen = Frame(root)
results = Frame(output_screen)

fold = DoubleVar()
fold_frame = Frame(results)
Label(fold_frame, text='fold: ').pack(side='left')
Label(fold_frame, textvariable=fold).pack(side='left')
fold_frame.pack(side='top')

call = DoubleVar()
call_frame = Frame(results)
Label(call_frame, text='call: ').pack(side='left')
Label(call_frame, textvariable=call).pack(side='left')
call_frame.pack(side='top')

three_bet = DoubleVar()
three_bet_frame = Frame(results)
Label(three_bet_frame, text='three bet: ').pack(side='left')
Label(three_bet_frame, textvariable=three_bet).pack(side='left')
three_bet_frame.pack(side='top')

raise_ = DoubleVar()
raise_frame = Frame(results)
Label(fold_frame, text='raise: ').pack(side='left')
Label(fold_frame, textvariable= raise_).pack(side='left')
raise_frame.pack(side='top')

recommended = StringVar()
raise_frame = Frame(results)
Label(fold_frame, text='Recomend: ').pack(side='left')
Label(fold_frame, textvariable= recommended).pack()
raise_frame.pack(side='top')

# Button(output_screen, text='compute', width=10, height=3, command=compute).pack(side='bottom')

results.pack()
output_screen.pack(side='right')

root.after(32, compute)
root.mainloop()
