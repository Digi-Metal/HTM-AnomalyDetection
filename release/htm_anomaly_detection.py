# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 09:33:14 2019

@author: Ming Jin
"""

import json
from itertools import islice
from datetime import datetime
from streamReader import streamReader
from nupic.engine import Network
from nupic.encoders import MultiEncoder, ScalarEncoder, DateEncoder



class HTM:
    '''
    HTM class for create networks and do prediction.
    -- getEncoderParams: read encoder parameters from json files
    -- setEncoderParams: write encoder parameters to json files
    -- createNetwork: create HTM network based on parameters and data source
    -- run: run a pre-defined HTM network. You need to loop this method for
            iterative prediction on records
    -- save_network: save the network structure and states after running
    '''
    
    def __init__(self, use_saved_model):
        self.use_saved_model = use_saved_model
    
    
    def getEncoderParams(self, encoder_path, key):
        with open(encoder_path, 'r') as json_file:
            all_params = json.load(json_file)
            return all_params[key]
        
        
    def setEncoderParams(self, encoder_path, encoder_dict):
        with open(encoder_path, 'w') as json_file:
            json.dump(encoder_dict, json_file)
            
            
    def createNetwork(self,
                      datasource,
                      recordParams, 
                      spatialParams, 
                      temporalParams, 
                      verbosity = 0, 
                      model_path = None):
        
        scalarEncoder1Args = recordParams["scalarEncoderArgs"]
        dateEncoderArgs = recordParams["dateEncoderArgs"]
    
        scalarEncoder1 = ScalarEncoder(**scalarEncoder1Args)  
        dateEncoder = DateEncoder(**dateEncoderArgs)
    
        encoder = MultiEncoder()
        encoder.addEncoder(scalarEncoder1Args["name"], scalarEncoder1)
        encoder.addEncoder(dateEncoderArgs["name"], dateEncoder)
    
        network = Network()
        
        if self.use_saved_model == False:
            network.addRegion("sensor", "py.RecordSensor",
                            json.dumps({"verbosity": verbosity}))
        
            sensor = network.regions["sensor"].getSelf()
            sensor.encoder = encoder
            sensor.dataSource = datasource
        
            # Create the spatial pooler region
            spatialParams["inputWidth"] = sensor.encoder.getWidth()
            network.addRegion("spatialPoolerRegion", "py.SPRegion",
                              json.dumps(spatialParams))
        
            # Link the SP region to the sensor input
            network.link("sensor", "spatialPoolerRegion", "UniformLink", "")
            network.link("sensor", "spatialPoolerRegion", "UniformLink", "",
                         srcOutput="resetOut", destInput="resetIn")
            network.link("spatialPoolerRegion", "sensor", "UniformLink", "",
                         srcOutput="spatialTopDownOut", destInput="spatialTopDownIn")
            network.link("spatialPoolerRegion", "sensor", "UniformLink", "",
                         srcOutput="temporalTopDownOut", destInput="temporalTopDownIn")
        
            # Add the TPRegion on top of the SPRegion
            network.addRegion("temporalPoolerRegion", "py.TMRegion",
                              json.dumps(temporalParams))
        
            network.link("spatialPoolerRegion", "temporalPoolerRegion", "UniformLink", "")
            network.link("temporalPoolerRegion", "spatialPoolerRegion", "UniformLink", "",
                         srcOutput="topDownOut", destInput="topDownIn")
            
            # Add the AnomalyLikelihoodRegion on top of the TMRegion
            network.addRegion("anomalyLikelihoodRegion", "py.AnomalyLikelihoodRegion", json.dumps({}))
            network.link("temporalPoolerRegion", "anomalyLikelihoodRegion", "UniformLink",
                         "", srcOutput="anomalyScore", destInput="rawAnomalyScore")
            network.link("sensor", "anomalyLikelihoodRegion", "UniformLink", "",
                         srcOutput="sourceOut", destInput="metricValue")    
        
        
            spatialPoolerRegion = network.regions["spatialPoolerRegion"]
        
            # Make sure learning is enabled
            spatialPoolerRegion.setParameter("learningMode", True)
            # We want temporal anomalies so disable anomalyMode in the SP. This mode is
            # used for computing anomalies in a non-temporal model.
            spatialPoolerRegion.setParameter("anomalyMode", False)
        
            temporalPoolerRegion = network.regions["temporalPoolerRegion"]
        
            # Enable topDownMode to get the predicted columns output
            temporalPoolerRegion.setParameter("topDownMode", True)
            # Make sure learning is enabled (this is the default)
            temporalPoolerRegion.setParameter("learningMode", True)
            # Enable inference mode so we get predictions
            temporalPoolerRegion.setParameter("inferenceMode", True)
            # Enable anomalyMode to compute the anomaly score.
            temporalPoolerRegion.setParameter("anomalyMode", True)
        
        else:
            network = Network(model_path)
    
        return network
    
    
    def run(self, network):
        sensorRegion = network.regions["sensor"]
        anomalyLikelihoodRegion = network.regions["anomalyLikelihoodRegion"]
        try:
            network.run(1)
            anomalyLikelihood = anomalyLikelihoodRegion.getOutputData("anomalyLikelihood")[0]
            fed_in_data = sensorRegion.getOutputData("sourceOut")[0]
            return fed_in_data, anomalyLikelihood
        except:
            raise StopIteration
    
    
    def save_network(self, network, model_path):
        network.save(model_path)