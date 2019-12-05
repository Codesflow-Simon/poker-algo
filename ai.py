from collections import deque
from itertools import chain
from random import sample

import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import Model
from tensorflow.keras.layers import Dense

memory_length = 5000


class QModel(Model):
	def __init__(self):
		super(QModel, self).__init__()
		self.dense_one = Dense(100)
		self.dense_two = Dense(50)
		self.dense_three = Dense(5)

	def call(self, x):
		x = self.dense_one(x)
		x = self.dense_two(x)
		x = self.dense_three(x)
		return x


q_values = QModel()

loss_object = keras.losses.MeanSquaredError()
optimizer = keras.optimizers.Adam()
train_loss = tf.keras.metrics.Mean(name='train_loss')

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


def train(epoch=1, batch_size=32):
	data = sample(memory, min(batch_size, len(memory)))
	data = pd.DataFrame(data)
	train_step(np.stack(data['state']), data['action'],  data['reward_sum'])


@tf.function
def train_step(state, action, reward_sum):
	with tf.GradientTape() as tape:
		q_hat = q_values(state)
		one_hot_actions = tf.one_hot(action, 5)
		q_actions = tf.math.reduce_sum(q_hat * one_hot_actions, axis=1)
		loss = loss_object(reward_sum, q_actions)
	gradients = tape.gradient(loss, q_values.trainable_variables)
	optimizer.apply_gradients(zip(gradients, q_values.trainable_variables))

	train_loss(loss)

def save():
	q_values.save_weights('test.h5')

def load():
	q_values.load_weights('test.h5')