Use HTM to learn from and predict to the real-time data stream based on cache
You can play with it by using your real-time CPU and memory usage.


Implementation:
Based on Python 2
<HOW_TO_USE_HTM_INTERFACE.ipynb> is the main entry, see comments inside.
<htm_anomaly_detection.py> provide methods that realted to use HTM, see comments inside.
<data_simulator.py> provide methods that related to save real-time data stream into cache 
for HTM to learn and do the prediction, see comments inside.

The logic is: Define some parameters and data source to create one or more HTM networks,
and the while loop inside the main entry will call for new data. You're able to save and
load networks at any time.


Notice:
* Delete ./temp and ./models before you run it again.
* At the begining, the anomalylikelihood will be 0.5, which is a normal behavior. 
  HTM need some data to train itself, see ipynb outputs for details.
* Usually the value of anomalylikelihood > 0.99 or 0.999 will be regarded as anomalies.
  You can experiment on your data and decide this threshold by yourself.
* You should experiment on INTERNAL buffer size and MIN/MAX values for the best performance.