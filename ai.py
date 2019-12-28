import os
from collections import deque
from itertools import chain
from random import sample

import numpy as np
import pandas as pd
import tensorflow as tf
import wandb
from tensorflow import keras
from tensorflow.keras import Model
from tensorflow.keras.layers import (Activation, BatchNormalization, Dense,
                                     Input, add)

def intergerify_cards(cards):
    suit_dict = {'s': 1, 'c': 2, 'h': 3, 'd': 4}
    rank_dict = {'2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6,
                    '8': 7, '9': 8, 'T': 9, 'J': 10, 'Q': 11, 'K': 12, 'A': 13}
    state = np.zeros((14), dtype=np.float32)
    for i, card in enumerate(cards):
        state[2*i] = rank_dict[card[0]]
        state[2*i+1] = suit_dict[card[1]]
    return list(state)

class Agent():
    def __init__(self, model_name, training, gpu=True):
        self.MODEL_NAME = model_name
        self.FILE_NAME = model_name + '.h5'
        if not gpu:
            os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
        if training:
            MEMORY_LENGTH = 5000
            wandb.init('poker')
            self.optimizer = keras.optimizers.Adam(0.0000001)
            self.loss_object = keras.losses.MeanSquaredError()

            self.index = np.zeros((1,))
            self.action_ratios = np.zeros((4,))

            self.memory = deque([], MEMORY_LENGTH)

            self.train_step = tf.function(
                self._train_step, experimental_relax_shapes=True)

        self.model = self.get_model(self.FILE_NAME)
        self.model.summary()
        

    def get_model(self, file):
        if os.path.isfile(file):
            print('loading')
            model = keras.models.load_model(file, compile=True)
            model.build((-1, 19))
        else:
            print('creating new nn')
            def residual_block(input_tensor):

                x = BatchNormalization()(input_tensor)
                x = Activation('elu')(x)
                x = Dense(100, use_bias=False)(x)

                x = BatchNormalization()(x)
                x = Activation('elu')(x)
                x = Dense(100, use_bias=False)(x)

                x = add([x, input_tensor])
                x = Activation('elu')(x)
                return x

            def QModel(input_shape):
                input_ = Input(shape=input_shape)
                x = Dense(1000, use_bias=False)(input_)
                x = BatchNormalization()(x)
                x = Activation('elu')(x)
                x = Dense(100, use_bias=False)(input_)
                x = BatchNormalization()(x)
                x = Activation('elu')(x)
                for _ in range(20):
                    x = residual_block(x)
                x = Dense(4)(x)
                model = Model(input_, x, name='dense_'+self.MODEL_NAME)
                return model
            model = QModel((19,))
            model.build((-1, 19))
            model.save(file)
        return model

    def action(self, info):
        # print(self.model.predict(self.prev), '\n')
        state = self.create_state(info)
        state = state.reshape(1, -1)
        # self.prev = state
        action_qs = self.model.predict(state)
        # print(action_qs)
        action = np.argmax(action_qs)
        return action

    def create_state(self, info):
        cards = chain(info['player_holes'], info['community'])
        state = intergerify_cards(cards)
        state.append(info['player_stack']/info['blind'])
        state.append(info['opponents_stack']/info['blind'])
        state.append(info['player_pot']+info['opponents_pot']/info['blind'])
        state.append(info['opponents_pot']- info['player_pot']/info['blind'])
        state.append(info['player_number'])
        return np.array(state)

    def memorise(self, state, action, reward):
        self.memory.append(
            {'state': state, 'action': action, 'reward': reward})

    def train(self, epoch=1, batch_size=128):
        if len(self.memory) < batch_size:
            return
        data = sample(self.memory, batch_size)
        data = pd.DataFrame(data)
        state = np.stack(data['state'])
        action = tf.constant(data['action'])
        one_hot_actions = tf.one_hot(action, 4)
        reward = tf.constant(np.array(data['reward']))
        
        
        
        loss = self.train_step(state, one_hot_actions, reward)
        assert np.isfinite(loss)

        for action in data['action']:
            self.action_ratios[action] += 1
            self.index[0] += 1

        wandb.log({'reward': np.array(data['reward']), 'action': np.array(data['action']), 'loss': loss.numpy(), 'fold': self.action_ratios[0]/self.index[0],
                   'call': self.action_ratios[1]/self.index[0],  'three bet': self.action_ratios[2]/self.index[0],  'raise': self.action_ratios[3]/self.index[0]})

    def _train_step(self, state, one_hot_actions, reward):
        with tf.GradientTape() as tape:
            state_predictions = self.model(state)
            action_q = tf.reduce_sum(
                state_predictions * one_hot_actions, axis=1)
            loss = self.loss_object(reward, action_q)
        gradients = tape.gradient(loss, self.model.trainable_variables)
        self.optimizer.apply_gradients(
            zip(gradients, self.model.trainable_variables))
        return loss

    def save(self):
        print(f'saving to: {self.FILE_NAME}')
        self.model.save(self.MODEL_NAME)
        
    def predict(self, state):
        return self.model.predict(state)
