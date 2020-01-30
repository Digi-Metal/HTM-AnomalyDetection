#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 11:21:52 2020

@author: tpc2
"""


# -*- encoding: utf-8 -*-
import socket
import json
import sys
IP = '192.168.1.1'
port = 40005
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.connect((IP,port))
except Exception as e:
    print('server not find or not open')
    sys.exit()
    
while True:
    data = s.recv(1024)
    data = data.decode()
    data = json.loads(data)
    print('recieved:',data)
    
s.close()