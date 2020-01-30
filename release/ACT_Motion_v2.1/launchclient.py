#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 17 15:56:02 2020

@author: tpc2
"""

import socket
import json

port = 8001
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", port))

while True:
    data, address = sock.recvfrom(1024 * 10)
    print("Received:", json.loads(data)[-4:], "from", address)