from testing import random_hand
from collections import defaultdict
from itertools import combinations, chain


hand = random_hand


card_order_dict = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
                   "8": 8, "9": 9, "T": 10, "J": 11, "Q": 12, "K": 13, "A": 14}

def get_ranks(hand):
    return [card[0] for card in hand]

def get_rank_int(hand):
    ranks = get_ranks(hand)
    return [card_order_dict[card] for card in ranks]

def find_key(hand, value):
    return list(hand.keys())[list(hand.values()).index(value)]

def comapre_hand_values(a, b):
    for i in range(min(len(a), len(b))):
        if a[i] > b[i]:
            return 'a'
        elif a[i] < b[i]:
            return 'b'
    return 'split'
      
def check_seven_hand(seven_hand):
    hands = combinations(seven_hand, 5)
    highest_hand = None
    highest_values = (0,0,0,0,0,0)
    for hand in hands:
        values = check_five_hand(hand)
        result = comapre_hand_values(values, highest_values)
        if result == 'a':
            highest_hand = hand
            highest_values = values
            continue
        elif result == 'b':
            continue

    return highest_hand, highest_values,


def check_five_hand(hand):
    values = check_straight_flush(hand)
    if values:
        return values
    values = check_four_of_a_kind(hand)
    if values:
        return values
    values = check_full_house(hand)
    if values:
        return values
    values = check_flush(hand)
    if values:
        return values
    values = check_straight(hand)
    if values:
        return values
    values = check_three_of_a_kind(hand)
    if values:
        return values
    values = check_two_pairs(hand)
    if values:
        return values
    values = check_one_pair(hand)
    if values:
        return values
    
    ranks = get_rank_int(hand)
    return tuple(chain([0],reversed(sorted(ranks))))


def check_straight_flush(hand):
    if check_flush(hand) and check_straight(hand):
        ranks = get_rank_int(hand)
        return (9, max(ranks))
    else:
        return ()


def check_four_of_a_kind(hand):
    values = [i[0] for i in hand]
    value_counts = defaultdict(lambda:0)
    for v in values:
        value_counts[v] += 1
    if sorted(value_counts.values()) == [1, 4]:
        quad_rank = card_order_dict[find_key(value_counts, 4)]
        single_rank = card_order_dict[find_key(value_counts, 1)]
        return (8, quad_rank, single_rank)
    return ()


def check_full_house(hand):
    values = [i[0] for i in hand]
    value_counts = defaultdict(lambda: 0)
    for v in values:
        value_counts[v] += 1
    if sorted(value_counts.values()) == [2, 3]:
        trip_rank = card_order_dict[find_key(value_counts, 3)]
        pair_rank = card_order_dict[find_key(value_counts, 2)]
        return (7, trip_rank, pair_rank)
    return ()


def check_flush(hand):
    suits = [i[1] for i in hand]
    ranks = get_rank_int(hand)
    if len(set(suits)) == 1:
        return tuple(chain([6],reversed(sorted(ranks))))
    else:
        return ()


def check_straight(hand):
    values = [i[0] for i in hand]
    value_counts = defaultdict(lambda: 0)
    for v in values:
        value_counts[v] += 1
    rank_values = [card_order_dict[i] for i in values]
    value_range = max(rank_values) - min(rank_values)
    if len(set(value_counts.values())) == 1 and (value_range == 4):
        return (5, max(rank_values))
    else:
        # check straight with low Ace
        if set(values) == set(["A", "2", "3", "4", "5"]):
            return (5, 5)
        return ()


def check_three_of_a_kind(hand):
    values = [i[0] for i in hand]
    value_counts = defaultdict(lambda: 0)
    for v in values:
        value_counts[v] += 1
    if set(value_counts.values()) == set([3, 1]):
        trip_rank = find_key(value_counts, 3)
        del value_counts[trip_rank]
        trip_rank = card_order_dict[trip_rank]
        kickers = list(reversed(sorted([card_order_dict[value] for value in value_counts])))
        return tuple(chain([4], [trip_rank], kickers))
    else:
        return ()


def check_two_pairs(hand):
    values = [i[0] for i in hand]
    value_counts = defaultdict(lambda: 0)
    for v in values:
        value_counts[v] += 1
    if sorted(value_counts.values()) == [1, 2, 2]:
        first_pair_rank = find_key(value_counts, 2)
        del value_counts[first_pair_rank]
        first_pair_rank = card_order_dict[first_pair_rank]
        second_pair_rank = card_order_dict[find_key(value_counts, 2)]
        kicker_rank = card_order_dict[find_key(value_counts, 1)]
        pairs = reversed(sorted([first_pair_rank, second_pair_rank]))
        return tuple(chain([3], pairs, [kicker_rank]))
    else:
        return ()


def check_one_pair(hand):
    values = [i[0] for i in hand]
    value_counts = defaultdict(lambda: 0)
    for v in values:
        value_counts[v] += 1
    if 2 in value_counts.values():
        pair_rank = card_order_dict[find_key(value_counts, 2)]
        first_kicker_rank = find_key(value_counts, 1)
        del value_counts[first_kicker_rank]
        first_kicker_rank = card_order_dict[first_kicker_rank]
        second_kicker_rank = find_key(value_counts, 1)
        del value_counts[second_kicker_rank]
        second_kicker_rank = card_order_dict[second_kicker_rank]
        third_kicker_rank = find_key(value_counts, 1)
        del value_counts[third_kicker_rank]
        third_kicker_rank = card_order_dict[third_kicker_rank]
        kickers = reversed(sorted([first_kicker_rank, second_kicker_rank, third_kicker_rank]))
        return tuple(chain([2], [pair_rank], kickers))
    else:
        return ()

