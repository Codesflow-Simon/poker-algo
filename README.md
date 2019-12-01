# poker-algo
Python version: 3.7.2
Download Python at www.python.org (less storage required) or use Anaconda for Python version control at www.anaconda.com (recommended)
to run the test script open a shell (search -> Windows PowerShell)
type `python` followed by the script name you want to run with .py appended name
i.e. `python game.py`

currently:
`game.py` shows one betting round between two bots making completely random choices
line 53 shows the choice distribution for both the bots.
`dist = [0.3, 0.2, 0.3, 0.15, 0.05]` 
means both the bosts have a 30% chance of folding,
have a 20% chance of calling/checking
have a 30% chance of 3-betting
have a 15% chance of pot-raising
have a 5% chance of going all in

`valuation.py` shows the best hand in a seven card hand
the hand is showen at line 190,
a card in in the form of `({suit}, {rank})`
where `{suit}` is the suit, either `s`, `c`, `h` or `d`
where `{rank}` is the rank, either `2`, `3`... `9`, `T`, `J`, `Q`, `K` or `A`

both programs are currently independant