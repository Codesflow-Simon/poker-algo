from collections import deque
from itertools import chain
from random import sample

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.decomposition import PCA
from tensorflow import keras
from tensorflow.keras import Model
from tensorflow.keras.layers import Dense

memory_length = 5000
pca = PCA(n_compnents=5)

class QModel(Model):
    def __init__(self):
        super(QModel, self).__init__()
        self.dense_one = Dense(100)
        self.dense_two = Dense(50)
        self.dense_three = Dense(20)
        self.dense_four = Dense(5)

    def call(self, x):
        x = self.dense_one(x)
        x = self.dense_two(x)
        x = self.dense_three(x)
        x = self.dense_four(x)
        return x


q_values = QModel()

optimizer = keras.optimizers.Adam()
loss_object = keras.losses.MeanSquaredError()
train_loss = keras.metrics.MeanSquaredError()

memory = deque([], memory_length)


def intergerify_cards(cards):
    suit_dict = {'s': 0, 'c': 1, 'h': 2, 'd': 3}
    rank_dict = {'2': 0, '3': 1, '4': 2, '5': 3, '6': 4, '7': 5,
                 '8': 6, '9': 7, 'T': 8, 'J': 9, 'Q': 10, 'K': 11, 'A': 12}
    state = np.zeros((14), dtype=np.float32)-1
    for i, card in enumerate(cards):
        state[2*i] = rank_dict[card[0]]
        state[2*i+1] = suit_dict[card[1]]
    return state


def memorise(state, action, reward_sum):
    memory.append({'state': state, 'action': action, 'reward_sum': reward_sum})


def train(epoch=1, batch_size=3):
    if len(memory) < batch_size:
        return
    data = sample(memory, batch_size)
    data = pd.DataFrame(data)
    state = np.stack(data['state'])
	# compressed_state = tf.constant(pca.fit_transform(state))
    print(q_values(np.array([12, 3, 12, 1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]).reshape((1, -1))))
    action = tf.constant(data['action'])
    one_hot_actions = tf.one_hot(action, 5)
    reward = tf.constant(np.array(data['reward_sum']))
    train_step(state, one_hot_actions, reward)


def _train_step(state, one_hot_actions, reward_sum):
    with tf.GradientTape() as tape:
        state_predictions = q_values(state)
        action_q = tf.reduce_sum(state_predictions * one_hot_actions, axis=1)
        loss = loss_object(reward_sum, action_q)
    gradients = tape.gradient(loss, q_values.trainable_variables)
    optimizer.apply_gradients(zip(gradients, q_values.trainable_variables))


    # train_loss(loss, action_q)
train_step = tf.function(_train_step, experimental_relax_shapes=True)


def save():
    q_values.save_weights('test.h5')


def load():
    q_values.load_weights('test.h5')
