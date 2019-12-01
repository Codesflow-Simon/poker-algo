from random import randint

suits = ['s', 'c', 'd', 'h']
ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']

def random_hand(size=7):
    hand = []
    for _ in range(size):
        suit_idx = randint(0,3)
        suit = suits[suit_idx]
        rank_idx = randint(0, 12)
        rank = ranks[rank_idx]
        hand.append((suit, rank))
    return hand