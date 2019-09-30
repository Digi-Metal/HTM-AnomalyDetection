# -*- coding: utf-8 -*-
"""
Created on Sun Sep 29 22:02:49 2019

@author: Ming Jin
"""

import os
import datetime
import time
import psutil
from htm_anomaly_detection import HTM

model = HTM(use_saved_model = False, checkpoint_path = None, likelihood_path = None)
#model = HTM(use_saved_model = True, checkpoint_path = 'model.pkl')

i = 1
while True:
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory().percent
    timestamp = datetime.datetime.now()
    
    anomaly_likelihood = model.run(cpu, memory, timestamp)
    
    print timestamp.strftime("%Y-%m-%d %H:%M:%S"), '\tCPU:', cpu, '\tMemory:', memory, '\tAnomaly likelihood:', anomaly_likelihood
    
    if i % 10 == 0:
        model.save_model(os.path.join(os.getcwd(), "model"),
                         os.path.join(os.getcwd(), "likelihood.pkl"))
        print 'checkpoint saved.'
    i += 1
    
    time.sleep(1)