# -*- coding: utf-8 -*-
"""
Created on Sun Sep 29 18:45:14 2019

@author: Ming Jin
"""

from nupic.frameworks.opf.model_factory import ModelFactory
from nupic.algorithms import anomaly_likelihood
import model_params

class HTM:
    '''
    The HTM class which packaging the methods that used to create 
    networks and do prediction.
    
    -- run: run a pre-defined HTM network once if network.run(1). You need to 
            loop this method for iterative prediction on records 
            (see my ipynb file for the usage)
    -- save_network: save the network structure and states after running
    '''
    
    def __init__(self, use_saved_model, checkpoint_path, likelihood_path):
        self.use_saved_model = use_saved_model
        if use_saved_model:
            self.model = ModelFactory.loadFromCheckpoint(checkpoint_path)
            self.model.enableInference({'predictedField': 'cpu'})
            self.model.enableInference({'predictedField': 'memory'})
            with open(likelihood_path, "rb") as f:
                self.anomalyLikelihood.readFromFile(f)
        else:
            self.model = ModelFactory.create(model_params.MODEL_PARAMS)
            self.model.enableInference({'predictedField': 'cpu'})
            self.model.enableInference({'predictedField': 'memory'})
            self.anomalyLikelihood = anomaly_likelihood.AnomalyLikelihood()

               
    def run(self, cpu, memory, timestamp):
        modelInput = {'cpu': float(cpu),
                      'memory': float(memory),
                      'timestamp': timestamp
                      }
        result = self.model.run(modelInput)
        anomalyScore = result.inferences['anomalyScore']
        likelihood1 = self.anomalyLikelihood.anomalyProbability(float(cpu), anomalyScore, timestamp)
        likelihood2 = self.anomalyLikelihood.anomalyProbability(float(memory), anomalyScore, timestamp)
        likelihood = (likelihood1 + likelihood2)/2
        return likelihood
    
    
    def save_model(self, model_path, likelihood_path):
        self.model.save(model_path)
        with open(likelihood_path, "wb") as f:
            self.anomalyLikelihood.writeToFile(f)