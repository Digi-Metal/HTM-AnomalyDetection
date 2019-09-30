# -*- coding: utf-8 -*-
"""
Created on Sun Sep 29 18:45:14 2019

@author: Ming Jin
"""

import datetime
import time
import psutil
from nupic.frameworks.opf.model_factory import ModelFactory
from nupic.algorithms import anomaly_likelihood
import model_params


def runCPU():
  """Poll CPU usage, make predictions, and plot the results. Runs forever."""
  # Create the model for predicting CPU usage.
  model = ModelFactory.create(model_params.MODEL_PARAMS)
  model.enableInference({'predictedField': 'cpu'})
  anomalyLikelihood = anomaly_likelihood.AnomalyLikelihood()
  
  while True:
    s = datetime.datetime.now()

    # Get the CPU usage.
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory().percent
    
    # Run the input through the model and shift the resulting prediction.
    modelInput = {'cpu': float(cpu),
                  'memory': float(memory),
                  'timestamp': s
                  }
    result = model.run(modelInput)

    anomalyScore = result.inferences['anomalyScore']
    likelihood = anomalyLikelihood.anomalyProbability(cpu, anomalyScore, s)
    print s.strftime("%Y-%m-%d %H:%M:%S"), '\tCPU:', cpu, '\tMemory:', memory, '\tAnomaly likelihood:', likelihood
    time.sleep(1)

if __name__ == "__main__":
  runCPU()