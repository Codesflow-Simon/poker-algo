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
OUTPUT_SIZE = 6

def intergerify_cards(cards):
    suit_dict = {'s': 1, 'c': 2, 'h': 3, 'd': 4}
    rank_dict = {'2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6,
                    '8': 7, '9': 8, 'T': 9, 'J': 10, 'Q': 11, 'K': 12, 'A': 13}
    state = np.zeros(14)
    for i, card in enumerate(cards):
        state[2*i] = rank_dict[card[0]]
        state[2*i+1] = suit_dict[card[1]]
    return list(state)

class Agent():
    def __init__(self, model_name, training, n_players, hyperparam={}, gpu=True):
        self.MODEL_NAME = model_name
        self.FILE_NAME = model_name + '.h5'
        
        self.INPUT_SIZE = 15+2*n_players
        if not gpu:
            os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
        if training:
            MEMORY_LENGTH = hyperparam['mem_length']
            # wandb.init('poker')
            self.optimizer = keras.optimizers.Adam(hyperparam['lr'])
            self.loss_object = keras.losses.MeanSquaredError()

            self.index = np.zeros((1,))
            self.action_ratios = np.zeros((OUTPUT_SIZE,))+(1/6)

            self.memory = deque([], MEMORY_LENGTH)

            self.train_step = tf.function(
                self._train_step, experimental_relax_shapes=True)
        self.model = self.get_model(self.FILE_NAME, hyperparam)
        if training:
            self.save()
            self.target_model = self.get_model(self.FILE_NAME, hyperparam)
        
        self.loss_ave = 0
        

    def get_model(self, file, hyperparam):
        if os.path.isfile(file):
            print('loading')
            model = keras.models.load_model(file, compile=False)
            model.build((-1, self.INPUT_SIZE))
        else:
            print('creating new nn')
            def residual_block(input_tensor):

                x = BatchNormalization()(input_tensor)
                x = Activation(hyperparam['activation'])(x)
                x = Dense(hyperparam['hidden_layer_size'], use_bias=False)(x)

                x = BatchNormalization()(x)
                x = Activation(hyperparam['activation'])(x)
                x = Dense(hyperparam['hidden_layer_size'], use_bias=False)(x)

                x = add([x, input_tensor])
                x = Activation(hyperparam['activation'])(x)
                return x

            def QModel(input_shape):
                input_ = Input(shape=input_shape)
                x = Dense(hyperparam['data_extraction_size'], use_bias=False)(input_)
                x = BatchNormalization()(x)
                x = Activation(hyperparam['activation'])(x)
                x = Dense(hyperparam['hidden_layer_size'], use_bias=False)(input_)
                x = BatchNormalization()(x)
                x = Activation(hyperparam['activation'])(x)
                for _ in range(hyperparam['block_count']):
                    x = residual_block(x)
                x = Dense(OUTPUT_SIZE)(x)
                model = Model(input_, x, name='dense_'+self.MODEL_NAME)
                return model
            model = QModel((self.INPUT_SIZE,))
            model.build((-1, self.INPUT_SIZE))
        return model

    def action(self, info):
        state = self.create_state(info)
        state = state.reshape(1, -1)
        action_qs = self.model.predict(state)
        action = np.argmax(action_qs)
        return action

    def create_state(self, info):
        cards = chain(info['holes'], info['community'])
        state = intergerify_cards(cards)
        state = chain(state, [stack/info['blind'] for stack in info['stacks']])
        state = chain(state, [pot/info['blind'] for pot in info['pot']])
        state = chain(state, [info['player_number']])
        return np.array(tuple(state))

    def memorise(self, state, action, reward):
        self.memory.append(
            {'state': state, 'action': action, 'reward': reward})

    def train(self, epoch=1, batch_size=32):
        if len(self.memory) < batch_size:
            return
        data = sample(self.memory, batch_size)
        data = pd.DataFrame(data)
        state = np.stack(data['state'])
        action = tf.constant(data['action'])
        one_hot_actions = tf.one_hot(action, OUTPUT_SIZE)
        reward = tf.constant(np.array(data['reward']))
        
        
        
        loss = self.train_step(state, one_hot_actions, reward).numpy()
        assert np.isfinite(loss)
        
        self.loss_ma(loss)

        for action in data['action']:
            self.action_ratios *= 0.9999
            self.action_ratios[action] += 0.0001

        log = {'reward': np.array(data['reward']), 'action': np.array(data['action']), 'loss': loss, 'loss ma': loss}
        for i, label in enumerate(['fold', 'call', 'quarter pot', 'half pot', 'full pot', 'two pot']):
            log[label] = self.action_ratios[i]
        
        # wandb.log(log)

    def _train_step(self, state, one_hot_actions, reward):
        with tf.GradientTape() as tape:
            state_predictions = self.target_model(state)
            action_q = tf.reduce_sum(
                state_predictions * one_hot_actions, axis=1)
            loss = self.loss_object(reward, action_q)
        gradients = tape.gradient(loss, self.target_model.trainable_variables)
        self.optimizer.apply_gradients(
            zip(gradients, self.model.trainable_variables))
        return loss
    
    def loss_ma(self, loss):
        self.loss_ave = self.loss_ave * 0.99 + loss * 0.01
        return self.loss_ave

    def transfer_weights(self):
        self.target_model.set_weights(self.model.get_weights())
    
    def save(self):
        # print(f'saving to: {self.FILE_NAME}')
        self.model.save(self.FILE_NAME)
        
    def predict(self, state):
        print(state)
        return self.model.predict(state)
