# -*- coding: utf-8 -*-
"""
Created on Sun Sep 29 18:44:27 2019

@author: Ming Jin
"""

MODEL_PARAMS = {
    # Type of model that the rest of these parameters apply to.
    'model': "HTMPrediction",

    # Version that specifies the format of the config.
    'version': 1,

    'predictAheadTime': None,

    'modelParams': {
            
        # The type of inference that this model will perform
        'inferenceType': 'TemporalAnomaly',
        'sensorParams': {
                
            'verbosity' : 0,
            
            # define encoders below.
            'encoders': { 
                'x': {
                    'clipInput': True,
                    'fieldname': u'x',
                    'n': 50,
                    'name': u'x',
                    'type': 'ScalarEncoder',
                    'minval': 0.91,
                    'maxval': 1.10,
                    'w': 21
                },   
                'y': {
                    'clipInput': True,
                    'fieldname': u'y',
                    'n': 50,
                    'name': u'y',
                    'type': 'ScalarEncoder',
                    'minval': -0.07,
                    'maxval': 0.21,
                    'w': 21
                }, 
                'z': {
                    'clipInput': True,
                    'fieldname': u'z',
                    'n': 50,
                    'name': u'z',
                    'type': 'ScalarEncoder',
                    'minval': -0.10,
                    'maxval': 0.14,
                    'w': 21
                }, 
                u'timestamp_timeOfDay': {
                    'fieldname': u'timestamp',
                    'name': u'timestamp_timeOfDay',
                    'timeOfDay': (21, 9),
                    'type': 'DateEncoder'
                },
                u'timestamp_dayOfWeek': None,
                u'timestamp_weekend': None, 
            },

            'sensorAutoReset' : None,
        },
                        
        # Spacial pooling Parameters
        'spEnable': True,
        'spParams': {
            'spVerbosity' : 0,
            'spatialImp': 'cpp',
            'globalInhibition': 1,
            'boostStrength': 2.0,
            'columnCount': 2048,
            'inputWidth': 0,
            'numActiveColumnsPerInhArea': 40,
            'seed': 1956,
            'potentialPct': 0.8,
            'synPermConnected': 0.1,
            'synPermActiveInc': 0.05,
            'synPermInactiveDec': 0.005,
        },

        # Temporal memory Parameters
        'tmEnable' : True,
        'tmParams': {
            'verbosity': 0,
            'columnCount': 2048,
            'cellsPerColumn': 32,
            'inputWidth': 2048,
            'seed': 1960,
            'temporalImp': 'cpp',
            'newSynapseCount': 20,
            'maxSynapsesPerSegment': 32,
            'maxSegmentsPerCell': 128,
            'initialPerm': 0.21,
            'permanenceInc': 0.1,
            'permanenceDec' : 0.1,
            'globalDecay': 0.0,
            'maxAge': 0,
            'minThreshold': 12,
            'activationThreshold': 16,
            'outputType': 'normal',
            'pamLength': 1,
        },

        # Don't create the classifier since we don't need predictions.
        'clEnable': False,
        'clParams': None,

        'anomalyParams': {  u'anomalyCacheRecords': None,
                            u'autoDetectThreshold': None,
                            u'autoDetectWaitRecords': None},

        'trainSPNetOnlyIfRequested': False,
    },
}
