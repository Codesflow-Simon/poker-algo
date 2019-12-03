from itertools import chain
from collections import deque
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import Model
from tensorflow.keras.layers import Dense

memory_length = 5000

class Policy(Model):
    def __init__(self):
        super(Policy, self).__init__()
        self.dense_one = Dense(100)
        self.dense_two = Dense(50)
        self.dense_three = Dense(5)

    def call(self, x):
        x = self.dense_one(x)
        x = self.dense_two(x)
        x = self.dense_three(x)
        return x
    
model = Policy()
model.compile(loss='mse', optimizer='adam', metrics=['mse'])

memory = deque([], memory_length)

def create_state(holes, board, pot, player_idx, prev_moves, opp_prev_moves):
    momory.append(tuple(chain(holes, board, pot, player_idx, prev_moves, opp_prev_moves)))
