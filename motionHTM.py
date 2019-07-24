#!/usr/bin/env python
# coding: utf-8

import csv
from itertools import islice
import json
import os
import time
from pkg_resources import resource_filename

from nupic.data.file_record_stream import FileRecordStream
from nupic.engine import Network
from nupic.encoders import MultiEncoder, ScalarEncoder, DateEncoder

# Global parameters
_VERBOSITY = 0
_NUM_RECORDS = 153501

# Default config fields for SPRegion
_SP_PARAMS = {
    "spVerbosity": _VERBOSITY,
    "spatialImp": "cpp",
    "globalInhibition": 1,
    "columnCount": 2048,
    "inputWidth": 0,
    "numActiveColumnsPerInhArea": 40,
    "seed": 1956,
    "potentialPct": 0.8,
    "synPermConnected": 0.1,
    "synPermActiveInc": 0.0001,
    "synPermInactiveDec": 0.0005,
    "boostStrength": 0.0,
}

# Default config fields for TPRegion
_TM_PARAMS = {
    "verbosity": _VERBOSITY,
    "columnCount": 2048,
    "cellsPerColumn": 32,
    "inputWidth": 2048,
    "seed": 1960,
    "temporalImp": "cpp",
    "newSynapseCount": 20,
    "maxSynapsesPerSegment": 32,
    "maxSegmentsPerCell": 128,
    "initialPerm": 0.21,
    "permanenceInc": 0.1,
    "permanenceDec": 0.1,
    "globalDecay": 0.0,
    "maxAge": 0,
    "minThreshold": 9,
    "activationThreshold": 12,
    "outputType": "normal",
    "pamLength": 3,
}


def createTemporalAnomaly_acc(recordParams, spatialParams=_SP_PARAMS,
                              temporalParams=_TM_PARAMS,
                              verbosity=_VERBOSITY):

    inputFilePath = recordParams["inputFilePath"]
    scalarEncoder1Args = recordParams["scalarEncoder1Args"]
    scalarEncoder2Args = recordParams["scalarEncoder2Args"]
    scalarEncoder3Args = recordParams["scalarEncoder3Args"]
    dateEncoderArgs = recordParams["dateEncoderArgs"]

    scalarEncoder1 = ScalarEncoder(**scalarEncoder1Args)
    scalarEncoder2 = ScalarEncoder(**scalarEncoder2Args)
    scalarEncoder3 = ScalarEncoder(**scalarEncoder3Args)
    dateEncoder = DateEncoder(**dateEncoderArgs)

    encoder = MultiEncoder()
    encoder.addEncoder(scalarEncoder1Args["name"], scalarEncoder1)
    encoder.addEncoder(scalarEncoder2Args["name"], scalarEncoder2)
    encoder.addEncoder(scalarEncoder3Args["name"], scalarEncoder3)
    encoder.addEncoder(dateEncoderArgs["name"], dateEncoder)

    network = Network()

    network.addRegion("sensor", "py.RecordSensor",
                    json.dumps({"verbosity": verbosity}))

    sensor = network.regions["sensor"].getSelf()
    sensor.encoder = encoder
    sensor.dataSource = FileRecordStream(streamID=inputFilePath)

    # Create the spatial pooler region
    spatialParams["inputWidth"] = sensor.encoder.getWidth()
    network.addRegion("spatialPoolerRegion", "py.SPRegion",
                      json.dumps(spatialParams))

    # Link the SP region to the sensor input
    network.link("sensor", "spatialPoolerRegion", "UniformLink", "")
    network.link("sensor", "spatialPoolerRegion", "UniformLink", "",
                 srcOutput="resetOut", destInput="resetIn")
    network.link("spatialPoolerRegion", "sensor", "UniformLink", "",
                 srcOutput="spatialTopDownOut", destInput="spatialTopDownIn")
    network.link("spatialPoolerRegion", "sensor", "UniformLink", "",
                 srcOutput="temporalTopDownOut", destInput="temporalTopDownIn")

    # Add the TPRegion on top of the SPRegion
    network.addRegion("temporalPoolerRegion", "py.TMRegion",
                      json.dumps(temporalParams))

    network.link("spatialPoolerRegion", "temporalPoolerRegion", "UniformLink", "")
    network.link("temporalPoolerRegion", "spatialPoolerRegion", "UniformLink", "",
                 srcOutput="topDownOut", destInput="topDownIn")

    spatialPoolerRegion = network.regions["spatialPoolerRegion"]

    # Make sure learning is enabled
    spatialPoolerRegion.setParameter("learningMode", True)
    # We want temporal anomalies so disable anomalyMode in the SP. This mode is
    # used for computing anomalies in a non-temporal model.
    spatialPoolerRegion.setParameter("anomalyMode", False)

    temporalPoolerRegion = network.regions["temporalPoolerRegion"]

    # Enable topDownMode to get the predicted columns output
    temporalPoolerRegion.setParameter("topDownMode", True)
    # Make sure learning is enabled (this is the default)
    temporalPoolerRegion.setParameter("learningMode", True)
    # Enable inference mode so we get predictions
    temporalPoolerRegion.setParameter("inferenceMode", True)
    # Enable anomalyMode to compute the anomaly score.
    temporalPoolerRegion.setParameter("anomalyMode", True)

    return network

def createTemporalAnomaly_qua(recordParams, spatialParams=_SP_PARAMS,
                              temporalParams=_TM_PARAMS,
                              verbosity=_VERBOSITY):

    inputFilePath = recordParams["inputFilePath"]
    scalarEncoder1Args = recordParams["scalarEncoder1Args"]
    scalarEncoder2Args = recordParams["scalarEncoder2Args"]
    scalarEncoder3Args = recordParams["scalarEncoder3Args"]
    scalarEncoder4Args = recordParams["scalarEncoder4Args"]
    dateEncoderArgs = recordParams["dateEncoderArgs"]

    scalarEncoder1 = ScalarEncoder(**scalarEncoder1Args)
    scalarEncoder2 = ScalarEncoder(**scalarEncoder2Args)
    scalarEncoder3 = ScalarEncoder(**scalarEncoder3Args)
    scalarEncoder4 = ScalarEncoder(**scalarEncoder4Args)
    dateEncoder = DateEncoder(**dateEncoderArgs)

    encoder = MultiEncoder()
    encoder.addEncoder(scalarEncoder1Args["name"], scalarEncoder1)
    encoder.addEncoder(scalarEncoder2Args["name"], scalarEncoder2)
    encoder.addEncoder(scalarEncoder3Args["name"], scalarEncoder3)
    encoder.addEncoder(scalarEncoder4Args["name"], scalarEncoder4)
    encoder.addEncoder(dateEncoderArgs["name"], dateEncoder)

    network = Network()

    network.addRegion("sensor", "py.RecordSensor",
                    json.dumps({"verbosity": verbosity}))

    sensor = network.regions["sensor"].getSelf()
    sensor.encoder = encoder
    sensor.dataSource = FileRecordStream(streamID=inputFilePath)

    # Create the spatial pooler region
    spatialParams["inputWidth"] = sensor.encoder.getWidth()
    network.addRegion("spatialPoolerRegion", "py.SPRegion",
                      json.dumps(spatialParams))

    # Link the SP region to the sensor input
    network.link("sensor", "spatialPoolerRegion", "UniformLink", "")
    network.link("sensor", "spatialPoolerRegion", "UniformLink", "",
                 srcOutput="resetOut", destInput="resetIn")
    network.link("spatialPoolerRegion", "sensor", "UniformLink", "",
                 srcOutput="spatialTopDownOut", destInput="spatialTopDownIn")
    network.link("spatialPoolerRegion", "sensor", "UniformLink", "",
                 srcOutput="temporalTopDownOut", destInput="temporalTopDownIn")

    # Add the TPRegion on top of the SPRegion
    network.addRegion("temporalPoolerRegion", "py.TMRegion",
                      json.dumps(temporalParams))

    network.link("spatialPoolerRegion", "temporalPoolerRegion", "UniformLink", "")
    network.link("temporalPoolerRegion", "spatialPoolerRegion", "UniformLink", "",
                 srcOutput="topDownOut", destInput="topDownIn")

    spatialPoolerRegion = network.regions["spatialPoolerRegion"]

    # Make sure learning is enabled
    spatialPoolerRegion.setParameter("learningMode", True)
    # We want temporal anomalies so disable anomalyMode in the SP. This mode is
    # used for computing anomalies in a non-temporal model.
    spatialPoolerRegion.setParameter("anomalyMode", False)

    temporalPoolerRegion = network.regions["temporalPoolerRegion"]

    # Enable topDownMode to get the predicted columns output
    temporalPoolerRegion.setParameter("topDownMode", True)
    # Make sure learning is enabled (this is the default)
    temporalPoolerRegion.setParameter("learningMode", True)
    # Enable inference mode so we get predictions
    temporalPoolerRegion.setParameter("inferenceMode", True)
    # Enable anomalyMode to compute the anomaly score.
    temporalPoolerRegion.setParameter("anomalyMode", True)

    return network

def getDate(recordParams, total = _NUM_RECORDS):
    inputFilePath = recordParams["inputFilePath"]
    date = []
    with open(inputFilePath) as fin:
        reader = csv.reader(fin)
        headers = reader.next()  # skip the header
        reader.next()
        reader.next()
        for record in islice(reader, total):
            Record_in_Dict = dict(zip(headers, record))
            date.append(Record_in_Dict["time"])
    return date
    
def runNetwork(network1, network2, network3, network4, date1, date2, date3, date4):
    sensorRegion1 = network1.regions["sensor"]
    temporalPoolerRegion1 = network1.regions["temporalPoolerRegion"]

    sensorRegion2 = network2.regions["sensor"]
    temporalPoolerRegion2 = network2.regions["temporalPoolerRegion"]
    
    sensorRegion3 = network3.regions["sensor"]
    temporalPoolerRegion3 = network3.regions["temporalPoolerRegion"]
    
    sensorRegion4 = network4.regions["sensor"]
    temporalPoolerRegion4 = network4.regions["temporalPoolerRegion"]
    
    for i in xrange(_NUM_RECORDS):
      # Run the network for a single iteration
        network1.run(1)
        anomalyScore1 = temporalPoolerRegion1.getOutputData("anomalyScore")[0]
        pre1_1 = sensorRegion1.getOutputData("sourceOut")[0]
        pre2_1 = sensorRegion1.getOutputData("sourceOut")[1]
        pre3_1 = sensorRegion1.getOutputData("sourceOut")[2]
        
        network2.run(1)
        anomalyScore2 = temporalPoolerRegion2.getOutputData("anomalyScore")[0]
        pre1_2 = sensorRegion2.getOutputData("sourceOut")[0]
        pre2_2 = sensorRegion2.getOutputData("sourceOut")[1]
        pre3_2 = sensorRegion2.getOutputData("sourceOut")[2]
        
        network3.run(1)
        anomalyScore3 = temporalPoolerRegion3.getOutputData("anomalyScore")[0]
        pre1_3 = sensorRegion3.getOutputData("sourceOut")[0]
        pre2_3 = sensorRegion3.getOutputData("sourceOut")[1]
        pre3_3 = sensorRegion3.getOutputData("sourceOut")[2]
        pre4_3 = sensorRegion3.getOutputData("sourceOut")[3]
        
        network4.run(1)
        anomalyScore4 = temporalPoolerRegion4.getOutputData("anomalyScore")[0]
        pre1_4 = sensorRegion4.getOutputData("sourceOut")[0]
        pre2_4 = sensorRegion4.getOutputData("sourceOut")[1]
        pre3_4 = sensorRegion4.getOutputData("sourceOut")[2]
        pre4_4 = sensorRegion4.getOutputData("sourceOut")[3]
        
        average_anomalyScore = (anomalyScore1 + anomalyScore2 + anomalyScore3 + anomalyScore4) // 4
        
#         if anomalyScore1 > 0.3 and anomalyScore2 > 0.3 and anomalyScore3 > 0.3 and anomalyScore4 > 0.3 and date1[i] == date2[i] and date2[i] == date3[i] and date3[i] == date4[i] and date4[i] == date1[i]:
#             print "Date: ", date1[i], "  PEPA ACC:", anomalyScore1, "  PEPA QUA:", anomalyScore3, "  SALT ACC:", anomalyScore2, "  SALT QUA", anomalyScore4
#             print "    --> PEPA_ACC: ", (pre1_1, pre2_1, pre3_1)
#             print "        SALT_ACC: ", (pre1_2, pre2_2, pre3_2)
#             print "        PEPA_QUA: ", (pre1_3, pre2_3, pre3_3, pre4_3)
#             print "        SALT_QUA: ", (pre1_4, pre2_4, pre3_4, pre4_4)
#             print "\n"

        print "Date: ", date1[i], "  PEPA ACC:", anomalyScore1, "  PEPA QUA:", anomalyScore3, "  SALT ACC:", anomalyScore2, "  SALT QUA", anomalyScore4
        print "    --> PEPA_ACC: ", (pre1_1, pre2_1, pre3_1)
        print "        SALT_ACC: ", (pre1_2, pre2_2, pre3_2)
        print "        PEPA_QUA: ", (pre1_3, pre2_3, pre3_3, pre4_3)
        print "        SALT_QUA: ", (pre1_4, pre2_4, pre3_4, pre4_4)
        if average_anomalyScore < 0.3:
            print "        \033[1;42m GOOD CONDITION \033[0m"
        elif average_anomalyScore > 0.3 and average_anomalyScore < 0.5:
            print "        \033[1;43m WARNING \033[0m"
        else:
            print "        \033[1;41m DANGEROUS CONDITION \033[0m"
        print "\n"

	time.sleep(5)

if __name__ == "__main__":
    
    pepa_acc_file = '/media/tpc2/DATA/ProcessedLanceData/pepa_acc_timestep3.csv'
    salt_acc_file = '/media/tpc2/DATA/ProcessedLanceData/salt_acc_timestep3.csv'
    pepa_qua_file = '/media/tpc2/DATA/ProcessedLanceData/pepa_qua_timestep3.csv'
    salt_qua_file = '/media/tpc2/DATA/ProcessedLanceData/salt_qua_timestep3.csv'
    
    scalarEncoder1Args = {
      "w": 21,
      "minval": 0.9,
      "maxval": 1.0,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "pepa_acc_x",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }
    
    scalarEncoder2Args = {
      "w": 21,
      "minval": -0.1,
      "maxval": 0.1,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "pepa_acc_y",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }

    scalarEncoder3Args = {
      "w": 21,
      "minval": -0.1,
      "maxval": 0.1,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "pepa_acc_z",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }
    
    dateEncoderArgs = {
      "season": 0,
      "dayOfWeek": 0,
      "weekend": 0,
      "holiday": 0,
      "timeOfDay": (21, 1),
      "customDays": 0,
      "name": "time",
      "forced": False
    }

    pepa_acc_recordParams = {
      "inputFilePath": pepa_acc_file,
      "scalarEncoder1Args": scalarEncoder1Args,
      "scalarEncoder2Args": scalarEncoder2Args,
      "scalarEncoder3Args": scalarEncoder3Args,
      "dateEncoderArgs": dateEncoderArgs,
    }

    scalarEncoder1Args = {
      "w": 21,
      "minval": 0.9,
      "maxval": 1.0,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "salt_acc_x",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }
    
    scalarEncoder2Args = {
      "w": 21,
      "minval": -0.1,
      "maxval": 0.1,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "salt_acc_y",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }

    scalarEncoder3Args = {
      "w": 21,
      "minval": -0.1,
      "maxval": 0.1,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "salt_acc_z",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }
    
    dateEncoderArgs = {
      "season": 0,
      "dayOfWeek": 0,
      "weekend": 0,
      "holiday": 0,
      "timeOfDay": (21, 1),
      "customDays": 0,
      "name": "time",
      "forced": False
    }
    
    salt_acc_recordParams = {
      "inputFilePath": salt_acc_file,
      "scalarEncoder1Args": scalarEncoder1Args,
      "scalarEncoder2Args": scalarEncoder2Args,
      "scalarEncoder3Args": scalarEncoder3Args,
      "dateEncoderArgs": dateEncoderArgs,
    }
    
    scalarEncoder1Args = {
      "w": 21,
      "minval": -0.8,
      "maxval": -0.2,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "pepa_qua_w",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }
    
    scalarEncoder2Args = {
      "w": 21,
      "minval": 0.2,
      "maxval": 0.8,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "pepa_qua_x",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }

    scalarEncoder3Args = {
      "w": 21,
      "minval": -0.8,
      "maxval": -0.2,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "pepa_qua_y",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }
    
    scalarEncoder4Args = {
      "w": 21,
      "minval": 0.2,
      "maxval": 0.8,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "pepa_qua_z",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }
    
    dateEncoderArgs = {
      "season": 0,
      "dayOfWeek": 0,
      "weekend": 0,
      "holiday": 0,
      "timeOfDay": (21, 1),
      "customDays": 0,
      "name": "time",
      "forced": False
    }

    pepa_qua_recordParams = {
      "inputFilePath": pepa_qua_file,
      "scalarEncoder1Args": scalarEncoder1Args,
      "scalarEncoder2Args": scalarEncoder2Args,
      "scalarEncoder3Args": scalarEncoder3Args,
      "scalarEncoder4Args": scalarEncoder4Args,
      "dateEncoderArgs": dateEncoderArgs,
    }
    
    scalarEncoder1Args = {
      "w": 21,
      "minval": 0.2,
      "maxval": 0.8,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "salt_qua_w",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }
    
    scalarEncoder2Args = {
      "w": 21,
      "minval": -0.8,
      "maxval": -0.3,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "salt_qua_x",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }

    scalarEncoder3Args = {
      "w": 21,
      "minval": 0.2,
      "maxval": 0.8,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "salt_qua_y",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }
    
    scalarEncoder4Args = {
      "w": 21,
      "minval": -0.8,
      "maxval": -0.3,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "salt_qua_z",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }
    
    dateEncoderArgs = {
      "season": 0,
      "dayOfWeek": 0,
      "weekend": 0,
      "holiday": 0,
      "timeOfDay": (21, 1),
      "customDays": 0,
      "name": "time",
      "forced": False
    }

    salt_qua_recordParams = {
      "inputFilePath": salt_qua_file,
      "scalarEncoder1Args": scalarEncoder1Args,
      "scalarEncoder2Args": scalarEncoder2Args,
      "scalarEncoder3Args": scalarEncoder3Args,
      "scalarEncoder4Args": scalarEncoder4Args,
      "dateEncoderArgs": dateEncoderArgs,
    }
    
    pepa_acc_network = createTemporalAnomaly_acc(pepa_acc_recordParams)
    salt_acc_network = createTemporalAnomaly_acc(salt_acc_recordParams)
    pepa_qua_network = createTemporalAnomaly_qua(pepa_qua_recordParams)
    salt_qua_network = createTemporalAnomaly_qua(salt_qua_recordParams)

    pepa_acc_date = getDate(pepa_acc_recordParams, _NUM_RECORDS)
    salt_acc_date = getDate(salt_acc_recordParams, _NUM_RECORDS)
    pepa_qua_date = getDate(pepa_qua_recordParams, _NUM_RECORDS)
    salt_qua_date = getDate(salt_qua_recordParams, _NUM_RECORDS)
    
    runNetwork(pepa_acc_network, salt_acc_network, pepa_qua_network, salt_qua_network, pepa_acc_date, salt_acc_date, pepa_qua_date, salt_qua_date)
