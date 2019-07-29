#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 11:15:45 2019

@author: tpc2
"""

import matplotlib.pyplot as plt
import numpy as np

plot = plt.figure("Visulization")

ax1 = plot.add_subplot(111)

a = np.empty((4, 3))
the_table = ax1.table(
    cellText=a,
    cellLoc = 'center',
    colLabels = ['Date', 'Avg_anomalyScore', 'Last for']
)
ax1.axis("off")  

plot.show()