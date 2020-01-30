# -*- coding: utf-8 -*-
"""
Created on Sun Sep 29 22:02:49 2019

@author: Ming Jin
"""

import os
import pandas
import socket
import datetime
import time
import json
from htm_anomaly_detection import HTM


def csv_handler(source, header):
    data = pandas.read_csv(source, names=header)
    return data
    
def data_simulator(raw, index):
    data = raw[index % len(raw)]
    return round(data, 3)

def getAverageAnomaly(raw1, raw2, raw3, raw4):
    average = (raw1 + raw2 + raw3 + raw4) / 4.0   
    if raw1 < 0.99 and raw2 < 0.99 and raw3 < 0.99 and raw4 < 0.99 and average < 0.96:
        return 1, average
    elif raw1 >= 0.99 and raw2 >= 0.99 and raw3 < 0.99 and raw4 < 0.99:
        return 2, average
    elif raw1 >= 0.99 and raw2 < 0.99 and raw3 >= 0.99 and raw4 < 0.99:
        return 2, average
    elif raw1 >= 0.99 and raw2 < 0.99 and raw3 < 0.99 and raw4 >= 0.99:
        return 2, average
    elif raw1 < 0.99 and raw2 >= 0.99 and raw3 >= 0.99 and raw4 < 0.99:
        return 2, average
    elif raw1 < 0.99 and raw2 >= 0.99 and raw3 < 0.99 and raw4 >= 0.99:
        return 2, average
    elif raw1 < 0.99 and raw2 < 0.99 and raw3 >= 0.99 and raw4 >= 0.99:
        return 2, average
    elif raw1 >= 0.99 and raw2 >= 0.99 and raw3 >= 0.99 and raw4 >= 0.99:
        return 3, average
    elif average > 0.96 and average < 0.98:
        return 2, average
    elif average >= 0.98:
        return 3, average
    else:
        return 1, average

'''
use model or not to create a HTM instance
'''
#model = HTM(use_saved_model = False, checkpoint_path = None, likelihood_path = None)
model = HTM(use_saved_model = True, checkpoint_path = 'model', likelihood_path = 'likelihood.pkl')

# process the raw data to be as the random source
header_salt_acc = ['salt_acc_x', 'salt_acc_y', 'salt_acc_z', 'time']
raw_salt_acc = csv_handler('./data/salt_acc_timestep3.csv', header_salt_acc)

header_salt_qua = ['salt_qua_w', 'salt_qua_x', 'salt_qua_y', 'salt_qua_z', 'time']
raw_salt_qua = csv_handler('./data/salt_qua_timestep3.csv', header_salt_qua)

header_pepa_acc = ['pepa_acc_x', 'pepa_acc_y', 'pepa_acc_z', 'time']
raw_pepa_acc = csv_handler('./data/pepa_acc_timestep3.csv', header_pepa_acc)

header_pepa_qua = ['pepa_qua_w', 'pepa_qua_x', 'pepa_qua_y', 'pepa_qua_z', 'time']
raw_pepa_qua = csv_handler('./data/pepa_qua_timestep3.csv', header_pepa_qua)

'''
Socket setup
'''
port = 8001
host = 'localhost'
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

i = 17300
while True:
    salt_acc_x = data_simulator(raw_salt_acc.salt_acc_x.tolist(), i)
    salt_acc_y = data_simulator(raw_salt_acc.salt_acc_y.tolist(), i)
    salt_acc_z = data_simulator(raw_salt_acc.salt_acc_z.tolist(), i)

    salt_qua_w = data_simulator(raw_salt_qua.salt_qua_w.tolist(), i)    
    salt_qua_x = data_simulator(raw_salt_qua.salt_qua_x.tolist(), i)
    salt_qua_y = data_simulator(raw_salt_qua.salt_qua_y.tolist(), i)
    salt_qua_z = data_simulator(raw_salt_qua.salt_qua_z.tolist(), i)
    
    pepa_acc_x = data_simulator(raw_pepa_acc.pepa_acc_x.tolist(), i)
    pepa_acc_y = data_simulator(raw_pepa_acc.pepa_acc_y.tolist(), i)
    pepa_acc_z = data_simulator(raw_pepa_acc.pepa_acc_z.tolist(), i)

    pepa_qua_w = data_simulator(raw_pepa_qua.pepa_qua_w.tolist(), i)    
    pepa_qua_x = data_simulator(raw_pepa_qua.pepa_qua_x.tolist(), i)
    pepa_qua_y = data_simulator(raw_pepa_qua.pepa_qua_y.tolist(), i)
    pepa_qua_z = data_simulator(raw_pepa_qua.pepa_qua_z.tolist(), i)
    
    timestamp = datetime.datetime.now()
    
    anomaly_likelihood1, anomaly_likelihood2, \
    anomaly_likelihood3, anomaly_likelihood4 = model.run(salt_acc_x,
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
                                                         timestamp)
    
    RunningCondition, AverageAnomaly = getAverageAnomaly(anomaly_likelihood1, 
                                         anomaly_likelihood2, 
                                         anomaly_likelihood3, 
                                         anomaly_likelihood4)
    

    if RunningCondition != 'Good condition':
        print timestamp.strftime("%Y-%m-%d %H:%M:%S"), '\tSALT_ACC:', \
        round(anomaly_likelihood1,2), '\tSALT_QUA:', round(anomaly_likelihood2,2), \
        '\tPEPA_ACC:', round(anomaly_likelihood3,2), '\tPEPA_QUA:', round(anomaly_likelihood4,2), \
        '\t', RunningCondition, '\tAnomaly:', round(AverageAnomaly,2)
    
#     saving model after a while
    if i % 100 == 0:
        model.save_model(os.path.join(os.getcwd(), "model"),
                         os.path.join(os.getcwd(), "likelihood.pkl"))
        print i, 'iter - checkpoint saved.'
        
    sock.sendto(json.dumps([salt_acc_x,
                            salt_acc_y,
                            salt_acc_z,
                            salt_qua_w,
                            salt_qua_x,
                            salt_qua_y,
                            salt_qua_z,
                            anomaly_likelihood1,
                            anomaly_likelihood2,
                            anomaly_likelihood3,
                            anomaly_likelihood4,
                            pepa_acc_x, 
                            pepa_acc_y, 
                            pepa_acc_z, 
                            pepa_qua_w,
                            pepa_qua_x,
                            pepa_qua_y,
                            pepa_qua_z,
                            RunningCondition,
                            AverageAnomaly,
                            timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                            i]), (host, port))
    i += 1
        
    time.sleep(5)
