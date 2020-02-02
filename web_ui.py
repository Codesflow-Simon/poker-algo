from flask import Flask, request
from flask_cors import CORS
from ai import Agent
import os
import ast
import numpy as np

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

class AgentManager:
    def __init__(self):
        self.agent = None
    def get_agent(self):
        return self.agent
    def set_agent(self, x):
        self.agent = x

agent = AgentManager()
        
app = Flask(__name__)
CORS(app)

@app.route('/initiate/<int:nPlayers>')
def initiate(nPlayers):
    agent.set_agent(Agent(f'./models/main_{nPlayers}', False, nPlayers))
    return {'status':200,'data':None, 'error':None}

@app.route('/predict')
def predict():
    data = np.array(ast.literal_eval(request.args.get('data'))).reshape(1, -1)
    a = agent.get_agent()
    if a:
        q_values = a.predict(data).tolist()
        return {'status':200, 'data':q_values, 'error':None}
    else:
        return {'status':400, 'data':None, 'error':'agent was not initiated'}

if __name__ == "__main__":
    app.run()