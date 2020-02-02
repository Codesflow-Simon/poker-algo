import itertools
from datetime import datetime

import numpy as np

from train import play_games

mem_lengths = [100, 200, 500, 1000, 2000, 5000]
lrs = [0.001, 0.0001, 0.00001, 0.000001,
       0.0000001, 0.00000001, 0.000000001]
activations = ['elu', 'relu', 'tanh']
hidden_layer_sizes = [10, 20, 50, 75, 100, 125, 200, 300, 500, 1000]
data_extraction_sizes = [10, 20, 50, 75, 100,
                         125, 200, 300, 500, 1000, 2000, 5000]
block_count = [1, 2, 5, 7, 10, 12, 15, 18, 20, 25, 30, 38, 50]

transfer_interval = [10, 50, 100, 200, 500, 1000, 2000]

product = set(itertools.product(mem_lengths, lrs, activations,
                                hidden_layer_sizes, data_extraction_sizes, block_count, transfer_interval))

for i in range(100):
    sample = product.pop()
    hyperparam = {'mem_length': sample[0], 'lr': sample[1], 'activation': sample[2],
                  'hidden_layer_size': sample[3], 'data_extraction_size': sample[4], 'block_count': sample[5]}
    transfer_int = sample[6]
    filename = datetime.now().strftime('%y%m%d%H%M%S')
    try:
        results = play_games(2000, 1000, transfer_int, hyperparam, f'./models/run{i}_{filename}', gpu=False)

    except (AssertionError,  RecursionError, TypeError) as e:
        print(e, hyperparam, transfer_int)
        continue
    with open('results.csv', 'a') as file:
        file.write(
            f'{i}, {sample[0]}, {sample[1]}, {sample[2]}, {sample[3]}, {sample[4]}, {sample[5]}, {results}, {np.inf}\n')
