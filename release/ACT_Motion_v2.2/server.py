#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 11:20:35 2020

@author: tpc2
"""

import socket
import json
import time
 
IP = "192.168.1.1" 
port = 40005
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((IP,port))
s.listen(1)
print('listen at port :',port)
conn,addr = s.accept()
print('connected by',addr)
 
while True:
#    send = [1,2,3]
    conn.sendall(json.dumps([1,2,3]).encode())
    time.sleep(2)
 
 
conn.close()
s.close()