# -*- coding: utf-8 -*-
"""
Created on Sat Sep 14 14:08:36 2019

@author: Ming Jin
"""

import os
#import numpy as np
import psutil
import csv
import datetime

'''
The data simulator that you can play with, and you have to modify this file to
fit for your data.

In this case, I used my real-time cpu and memory usage for experiments, which
performs normally.


-- data_generator: define your source of data

-- count_rows: count how many rows in csv cache

-- write_to_csv: write data to csv cache

-- time_arithmetic: add 1 hour to a give datetime. You can also modify this 
                    based on your time gap, like in minutes or in seconds
                    
-- getLastTimeFromCSV: get the datetime for the last record in current cache

-- getRunningTime: get the datetime based on an indicator

-- getBatchData2csv: should be called externally to write a new batch of data 
                     into csv cache
'''
    
def data_generator():
#    x1 = np.random.uniform(2, 5)
#    x2 = np.random.uniform(2, 5)
    x1 = psutil.cpu_percent(interval=1)
    x2 = psutil.virtual_memory().percent
    return x1, x2


def count_rows(filepath):
    with open(filepath, 'r') as f:
        return len(f.readlines())
 
    
def write_to_csv(data, filepath):
    '''
    This function has been defined for csv file writing.
        --outputfile: The output csv file
        --row: The rows write to csv file
    
    '''
    csvfile = open(filepath, 'wb+')
    writer = csv.writer(csvfile)
    writer.writerows(data)
    csvfile.close()
    
    
def time_arithmetic(date):
    delta = datetime.timedelta(hours=1)
    out_date = date + delta
    return out_date


def getLastTimeFromCSV(filepath):
    with open(filepath, 'r') as csvfile:
        lines = csvfile.readlines()
        targetLine = lines[-1]
        lastime = targetLine.split(',')[0]
        return datetime.datetime.strptime(lastime, '%Y-%m-%d %H:%M:%S')


def getRunningTime(filepath, indicator):
    with open(filepath, 'r') as csvfile:
        lines = csvfile.readlines()
        targetLine = lines[indicator]
        lastime = targetLine.split(',')[0]
        return datetime.datetime.strptime(lastime, '%Y-%m-%d %H:%M:%S')


def getBatchData2csv(buffer_size, filepath1, filepath2):
    buffer_count = 0
    buffer1 = []
    buffer2 = []
    
    if os.path.exists(filepath1) and os.path.exists(filepath2):
        date = getLastTimeFromCSV(filepath1)
    else:
        date = datetime.datetime.strptime('2019-09-09 00:00:00', '%Y-%m-%d %H:%M:%S')
        
    while(1):
        if buffer_count < buffer_size:
            data1, data2 = data_generator()
            date = time_arithmetic(date)
            buffer1.append([date, data1])
            buffer2.append([date, data2])
            buffer_count += 1
        else:
            buffer1.insert(0, ['time', 'value'])
            buffer2.insert(0, ['time', 'value'])
        
            buffer1.insert(1, ['datetime', 'float'])
            buffer2.insert(1, ['datetime', 'float'])
            
            buffer1.insert(2, ['T', ''])
            buffer2.insert(2, ['T', ''])
            
            write_to_csv(buffer1, filepath1)
            write_to_csv(buffer2, filepath2)
            
            buffer_count = 0
            buffer1 = []
            buffer2 = []
            
            break