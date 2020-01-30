# -*- coding: utf-8 -*-
"""
Created on Sun Sep 29 18:45:14 2019

@author: Ming Jin
"""

from nupic.frameworks.opf.model_factory import ModelFactory
from nupic.algorithms import anomaly_likelihood
import model_params_salt_acc
import model_params_salt_qua
import model_params_pepa_acc
import model_params_pepa_qua

class HTM:
    '''
    The HTM class which packaging the methods that used to create 
    networks and do prediction.
    
    -- run: run a pre-defined HTM network once if network.run(1). You need to 
            loop this method for iterative prediction on records 
            (see my "launchdemo.py" file for the usage)
    -- save_model: save the model and states after running
    '''
    
    def __init__(self, use_saved_model, checkpoint_path, likelihood_path):
        self.use_saved_model = use_saved_model
        
        if use_saved_model:
            self.salt_acc_model = ModelFactory.loadFromCheckpoint(checkpoint_path + '_SALT_ACC')
            self.salt_qua_model = ModelFactory.loadFromCheckpoint(checkpoint_path + '_SALT_QUA')
            self.pepa_acc_model = ModelFactory.loadFromCheckpoint(checkpoint_path + '_PEPA_ACC')
            self.pepa_qua_model = ModelFactory.loadFromCheckpoint(checkpoint_path + '_PEPA_QUA')
            
            self.salt_acc_model.enableInference({'predictedField': 'x'})
            self.salt_acc_model.enableInference({'predictedField': 'y'})
            self.salt_acc_model.enableInference({'predictedField': 'z'})
            
            self.salt_qua_model.enableInference({'predictedField': 'w'})
            self.salt_qua_model.enableInference({'predictedField': 'x'})
            self.salt_qua_model.enableInference({'predictedField': 'y'})
            self.salt_qua_model.enableInference({'predictedField': 'z'})
            
            self.pepa_acc_model.enableInference({'predictedField': 'x'})
            self.pepa_acc_model.enableInference({'predictedField': 'y'})
            self.pepa_acc_model.enableInference({'predictedField': 'z'})
            
            self.pepa_qua_model.enableInference({'predictedField': 'w'})
            self.pepa_qua_model.enableInference({'predictedField': 'x'})
            self.pepa_qua_model.enableInference({'predictedField': 'y'})
            self.pepa_qua_model.enableInference({'predictedField': 'z'})
            
            with open(likelihood_path, "rb") as f:
                self.anomalyLikelihood = anomaly_likelihood.AnomalyLikelihood().readFromFile(f)
                
        else:
            self.salt_acc_model = ModelFactory.create(model_params_salt_acc.MODEL_PARAMS)
            self.salt_qua_model = ModelFactory.create(model_params_salt_qua.MODEL_PARAMS)
            self.pepa_acc_model = ModelFactory.create(model_params_pepa_acc.MODEL_PARAMS)
            self.pepa_qua_model = ModelFactory.create(model_params_pepa_qua.MODEL_PARAMS)
            
            self.salt_acc_model.enableInference({'predictedField': 'x'})
            self.salt_acc_model.enableInference({'predictedField': 'y'})
            self.salt_acc_model.enableInference({'predictedField': 'z'})
            
            self.salt_qua_model.enableInference({'predictedField': 'w'})
            self.salt_qua_model.enableInference({'predictedField': 'x'})
            self.salt_qua_model.enableInference({'predictedField': 'y'})
            self.salt_qua_model.enableInference({'predictedField': 'z'})
            
            self.pepa_acc_model.enableInference({'predictedField': 'x'})
            self.pepa_acc_model.enableInference({'predictedField': 'y'})
            self.pepa_acc_model.enableInference({'predictedField': 'z'})
            
            self.pepa_qua_model.enableInference({'predictedField': 'w'})
            self.pepa_qua_model.enableInference({'predictedField': 'x'})
            self.pepa_qua_model.enableInference({'predictedField': 'y'})
            self.pepa_qua_model.enableInference({'predictedField': 'z'})
            
            self.anomalyLikelihood = anomaly_likelihood.AnomalyLikelihood()

               
    def run(self, 
            salt_acc_x, 
            salt_acc_y,
            salt_acc_z,
            salt_qua_w,
            salt_qua_x,
            salt_qua_y,
            salt_qua_z,
            pepa_acc_x, 
            pepa_acc_y,
            pepa_acc_z,
            pepa_qua_w,
            pepa_qua_x,
            pepa_qua_y,
            pepa_qua_z,
            timestamp):
        
	# bond those input variables together as modelInput
        salt_acc_modelInput = {'x': float(salt_acc_x),
                               'y': float(salt_acc_y),
                               'z': float(salt_acc_z),
                               'timestamp': timestamp
                               }
        
        salt_qua_modelInput = {'w': float(salt_qua_w),
                               'x': float(salt_qua_x),
                               'y': float(salt_qua_y),
                               'z': float(salt_qua_z),
                               'timestamp': timestamp
                               }
        
        pepa_acc_modelInput = {'x': float(pepa_acc_x),
                               'y': float(pepa_acc_y),
                               'z': float(pepa_acc_z),
                               'timestamp': timestamp
                               }
        
        pepa_qua_modelInput = {'w': float(pepa_qua_w),
                               'x': float(pepa_qua_x),
                               'y': float(pepa_qua_y),
                               'z': float(pepa_qua_z),
                               'timestamp': timestamp
                               }
        
        salt_acc_result = self.salt_acc_model.run(salt_acc_modelInput)
        salt_qua_result = self.salt_qua_model.run(salt_qua_modelInput)
        pepa_acc_result = self.pepa_acc_model.run(pepa_acc_modelInput)
        pepa_qua_result = self.pepa_qua_model.run(pepa_qua_modelInput)
        
        salt_acc_anomalyScore = salt_acc_result.inferences['anomalyScore']
        salt_acc_likelihood1 = self.anomalyLikelihood.anomalyProbability(float(salt_acc_x), salt_acc_anomalyScore, timestamp)
        salt_acc_likelihood2 = self.anomalyLikelihood.anomalyProbability(float(salt_acc_y), salt_acc_anomalyScore, timestamp)
        salt_acc_likelihood3 = self.anomalyLikelihood.anomalyProbability(float(salt_acc_z), salt_acc_anomalyScore, timestamp)
        salt_acc_likelihood = (salt_acc_likelihood1 + salt_acc_likelihood2 + salt_acc_likelihood3)/3
        
        salt_qua_anomalyScore = salt_qua_result.inferences['anomalyScore']
        salt_qua_likelihood1 = self.anomalyLikelihood.anomalyProbability(float(salt_qua_w), salt_qua_anomalyScore, timestamp)
        salt_qua_likelihood2 = self.anomalyLikelihood.anomalyProbability(float(salt_qua_x), salt_qua_anomalyScore, timestamp)
        salt_qua_likelihood3 = self.anomalyLikelihood.anomalyProbability(float(salt_qua_y), salt_qua_anomalyScore, timestamp)
        salt_qua_likelihood4 = self.anomalyLikelihood.anomalyProbability(float(salt_qua_z), salt_qua_anomalyScore, timestamp)
        salt_qua_likelihood = (salt_qua_likelihood1 + salt_qua_likelihood2 + salt_qua_likelihood3 + salt_qua_likelihood4)/4
        
        pepa_acc_anomalyScore = pepa_acc_result.inferences['anomalyScore']
        pepa_acc_likelihood1 = self.anomalyLikelihood.anomalyProbability(float(pepa_acc_x), pepa_acc_anomalyScore, timestamp)
        pepa_acc_likelihood2 = self.anomalyLikelihood.anomalyProbability(float(pepa_acc_y), pepa_acc_anomalyScore, timestamp)
        pepa_acc_likelihood3 = self.anomalyLikelihood.anomalyProbability(float(pepa_acc_z), pepa_acc_anomalyScore, timestamp)
        pepa_acc_likelihood = (pepa_acc_likelihood1 + pepa_acc_likelihood2 + pepa_acc_likelihood3)/3
        
        pepa_qua_anomalyScore = pepa_qua_result.inferences['anomalyScore']
        pepa_qua_likelihood1 = self.anomalyLikelihood.anomalyProbability(float(pepa_qua_w), pepa_qua_anomalyScore, timestamp)
        pepa_qua_likelihood2 = self.anomalyLikelihood.anomalyProbability(float(pepa_qua_x), pepa_qua_anomalyScore, timestamp)
        pepa_qua_likelihood3 = self.anomalyLikelihood.anomalyProbability(float(pepa_qua_y), pepa_qua_anomalyScore, timestamp)
        pepa_qua_likelihood4 = self.anomalyLikelihood.anomalyProbability(float(pepa_qua_z), pepa_qua_anomalyScore, timestamp)
        pepa_qua_likelihood = (pepa_qua_likelihood1 + pepa_qua_likelihood2 + pepa_qua_likelihood3 + pepa_qua_likelihood4)/4
        
        return salt_acc_likelihood, salt_qua_likelihood, pepa_acc_likelihood, pepa_qua_likelihood
    
    
    def save_model(self, model_path, likelihood_path):
        self.salt_acc_model.save(model_path + '_SALT_ACC')
        self.salt_qua_model.save(model_path + '_SALT_QUA')
        self.pepa_acc_model.save(model_path + '_PEPA_ACC')
        self.pepa_qua_model.save(model_path + '_PEPA_QUA')
        with open(likelihood_path, "wb") as f:
            self.anomalyLikelihood.writeToFile(f)
