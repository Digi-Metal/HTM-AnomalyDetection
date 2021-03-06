#!/usr/bin/env python
# coding: utf-8

import matplotlib.pyplot as plt

import csv
from itertools import islice
import json
import time
from datetime import datetime
import numpy as np

from nupic.data.file_record_stream import FileRecordStream
from nupic.engine import Network
from nupic.encoders import MultiEncoder, ScalarEncoder, DateEncoder


def createTemporalAnomaly_acc(recordParams, spatialParams, temporalParams, verbosity):

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


def createTemporalAnomaly_qua(recordParams, spatialParams, temporalParams, verbosity):

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


def mean(numbers):
    return float(sum(numbers)) / max(len(numbers), 1)


def seconds_difference(date_str1, date_str2):
    date1 = datetime.strptime(date_str1, '%Y-%m-%d %H:%M:%S')
    date2 = datetime.strptime(date_str2, '%Y-%m-%d %H:%M:%S')
    return float((date2 - date1).total_seconds())


def getDate(recordParams, total):
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


def plot_acc_data(x, y, z, date, buffer_size=100):
    if len(x) > buffer_size and len(y) > buffer_size and len(z) > buffer_size:
        new_x = x[-buffer_size:]
        new_y = y[-buffer_size:]
        new_z = z[-buffer_size:]
        new_date = date[-buffer_size:]
        return new_x, new_y, new_z, new_date
    else:        
        return x, y, z, date

    
def plot_qua_data(w, x, y, z, date, buffer_size=100):
    if len(w) > buffer_size and len(x) > buffer_size and len(y) > buffer_size and len(z) > buffer_size:
        new_w = w[-buffer_size:]
        new_x = x[-buffer_size:]
        new_y = y[-buffer_size:]
        new_z = z[-buffer_size:]
        new_date = date[-buffer_size:]
        return new_w, new_x, new_y, new_z, new_date
    else:        
        return w, x, y, z, date

	  
def runNetwork(network1, network2, network3, network4, date1, date2, date3, date4):
    sensorRegion1 = network1.regions["sensor"]
    temporalPoolerRegion1 = network1.regions["temporalPoolerRegion"]

    sensorRegion2 = network2.regions["sensor"]
    temporalPoolerRegion2 = network2.regions["temporalPoolerRegion"]
    
    sensorRegion3 = network3.regions["sensor"]
    temporalPoolerRegion3 = network3.regions["temporalPoolerRegion"]
    
    sensorRegion4 = network4.regions["sensor"]
    temporalPoolerRegion4 = network4.regions["temporalPoolerRegion"]
	
    date = []
    pepa_acc_plot_x = []
    pepa_acc_plot_y = []
    pepa_acc_plot_z = []
    salt_acc_plot_x = []
    salt_acc_plot_y = []
    salt_acc_plot_z = []    
    pepa_qua_plot_w = []
    pepa_qua_plot_x = []
    pepa_qua_plot_y = []
    pepa_qua_plot_z = []
    salt_qua_plot_w = []
    salt_qua_plot_x = []
    salt_qua_plot_y = []
    salt_qua_plot_z = []
    
    table_content = [[' ', ' ', ' '],[' ', ' ', ' '],[' ', ' ', ' '],[' ', ' ', ' ']]
    previous_result = 'G'
    contineous_flag = False

    plot = plt.figure("Outotec Motion Anomaly Detection", figsize=(28, 6))
    plot.subplots_adjust(wspace =1, hspace =0.5)
    plot.subplots(ncols=2, nrows=3)
    
    for i in xrange(_NUM_RECORDS):
        network1.run(1)
        anomalyScore1 = temporalPoolerRegion1.getOutputData("anomalyScore")[0]
        pre1_1 = sensorRegion1.getOutputData("sourceOut")[0]
        pre2_1 = sensorRegion1.getOutputData("sourceOut")[1]
        pre3_1 = sensorRegion1.getOutputData("sourceOut")[2]
        pepa_acc_plot_x.append(pre1_1)
        pepa_acc_plot_y.append(pre2_1)
        pepa_acc_plot_z.append(pre3_1)
		
        network2.run(1)
        anomalyScore2 = temporalPoolerRegion2.getOutputData("anomalyScore")[0]
        pre1_2 = sensorRegion2.getOutputData("sourceOut")[0]
        pre2_2 = sensorRegion2.getOutputData("sourceOut")[1]
        pre3_2 = sensorRegion2.getOutputData("sourceOut")[2]
        salt_acc_plot_x.append(pre1_2)
        salt_acc_plot_y.append(pre2_2)
        salt_acc_plot_z.append(pre3_2)

        network3.run(1)
        anomalyScore3 = temporalPoolerRegion3.getOutputData("anomalyScore")[0]
        pre1_3 = sensorRegion3.getOutputData("sourceOut")[0]
        pre2_3 = sensorRegion3.getOutputData("sourceOut")[1]
        pre3_3 = sensorRegion3.getOutputData("sourceOut")[2]
        pre4_3 = sensorRegion3.getOutputData("sourceOut")[3]
        pepa_qua_plot_w.append(pre1_3)
        pepa_qua_plot_x.append(pre2_3)
        pepa_qua_plot_y.append(pre3_3)
        pepa_qua_plot_z.append(pre4_3)
        
        network4.run(1)
        anomalyScore4 = temporalPoolerRegion4.getOutputData("anomalyScore")[0]
        pre1_4 = sensorRegion4.getOutputData("sourceOut")[0]
        pre2_4 = sensorRegion4.getOutputData("sourceOut")[1]
        pre3_4 = sensorRegion4.getOutputData("sourceOut")[2]
        pre4_4 = sensorRegion4.getOutputData("sourceOut")[3]
        salt_qua_plot_w.append(pre1_4)
        salt_qua_plot_x.append(pre2_4)
        salt_qua_plot_y.append(pre3_4)
        salt_qua_plot_z.append(pre4_4)
        
        average_anomalyScore = mean([anomalyScore1, anomalyScore2, anomalyScore3, anomalyScore4])
        
        date.append(date1[i])
        		
        print "Date: ", date1[i], "  PEPA ACC:", anomalyScore1, "  PEPA QUA:", anomalyScore3, "  SALT ACC:", anomalyScore2, "  SALT QUA", anomalyScore4
        print "    --> PEPA_ACC: ", (pre1_1, pre2_1, pre3_1)
        print "        SALT_ACC: ", (pre1_2, pre2_2, pre3_2)
        print "        PEPA_QUA: ", (pre1_3, pre2_3, pre3_3, pre4_3)
        print "        SALT_QUA: ", (pre1_4, pre2_4, pre3_4, pre4_4)
        if average_anomalyScore < 0.3:
            print "        \033[1;42m GOOD CONDITION \033[0m"
            previous_result = 'G'
        elif average_anomalyScore > 0.3 and average_anomalyScore < 0.5:
            print "        \033[1;43m WARNING CAUTION \033[0m"
            previous_result = 'W'
        else:
            if previous_result == 'D':
                contineous_flag = True
            else:
                contineous_flag = False

            if table_content[0][0] == ' ' and contineous_flag == False:
                table_content[0][0] = date1[i]
                table_content[0][1] = average_anomalyScore
                table_content[0][2] = float(0)
            elif table_content[1][0] == ' ' and contineous_flag == False:
                table_content[1][0] = date1[i]
                table_content[1][1] = average_anomalyScore
                table_content[1][2] = float(0)
            elif table_content[2][0] == ' ' and contineous_flag == False:
                table_content[2][0] = date1[i]
                table_content[2][1] = average_anomalyScore
                table_content[2][2] = float(0)
            elif table_content[3][0] == ' ' and contineous_flag == False:
                table_content[3][0] = date1[i]
                table_content[3][1] = average_anomalyScore
                table_content[3][2] = float(0)         
            elif table_content[1][0] == ' ' and contineous_flag == True:
                table_content[0][0] = date1[i]
                table_content[0][1] = average_anomalyScore
                table_content[0][2] += seconds_difference(date1[i-1], date1[i])
            elif table_content[2][0] == ' ' and contineous_flag == True:
                table_content[1][0] = date1[i]
                table_content[1][1] = average_anomalyScore
                table_content[1][2] += seconds_difference(date1[i-1], date1[i])
            elif table_content[3][0] == ' ' and contineous_flag == True:
                table_content[2][0] = date1[i]
                table_content[2][1] = average_anomalyScore
                table_content[2][2] += seconds_difference(date1[i-1], date1[i])
            elif table_content[0][0] != ' ' and table_content[1][0] != ' ' and table_content[2][0] != ' ' and table_content[3][0] != ' ' and contineous_flag == False:
                table_content[0][0] = table_content[1][0]
                table_content[0][1] = table_content[1][1]
                table_content[0][2] = table_content[1][2]
                
                table_content[1][0] = table_content[2][0]
                table_content[1][1] = table_content[2][1]
                table_content[1][2] = table_content[2][2]
                
                table_content[2][0] = table_content[3][0]
                table_content[2][1] = table_content[3][1]
                table_content[2][2] = table_content[3][2]
                
                table_content[3][0] = date1[i]
                table_content[3][1] = average_anomalyScore
                table_content[3][2] = 0
            elif table_content[0][0] != ' ' and table_content[1][0] != ' ' and table_content[2][0] != ' ' and table_content[3][0] != ' ' and contineous_flag == True:                
                table_content[3][0] = date1[i]
                table_content[3][1] = average_anomalyScore
                table_content[3][2] += seconds_difference(date1[i-1], date1[i])   
            print "        \033[1;41m DANGEROUS CONDITION \033[0m"
            previous_result = 'D'
        print "\n"
        
        plt_pepa_acc_x, plt_pepa_acc_y, plt_pepa_acc_z, plt_date_pepa_acc = plot_acc_data(pepa_acc_plot_x, pepa_acc_plot_y, pepa_acc_plot_z, date)
        plt_salt_acc_x, plt_salt_acc_y, plt_salt_acc_z, plt_date_salt_acc = plot_acc_data(salt_acc_plot_x, salt_acc_plot_y, salt_acc_plot_z, date)
        plt_pepa_qua_w, plt_pepa_qua_x, plt_pepa_qua_y, plt_pepa_qua_z, plt_date_pepa_qua = plot_qua_data(pepa_qua_plot_w, pepa_qua_plot_x, pepa_qua_plot_y, pepa_qua_plot_z, date)
        plt_salt_qua_w, plt_salt_qua_x, plt_salt_qua_y, plt_salt_qua_z, plt_date_salt_qua = plot_qua_data(salt_qua_plot_w, salt_qua_plot_x, salt_qua_plot_y, salt_qua_plot_z, date)

        # pepa acc plot
        ax1 = plot.add_subplot(4,4,1)
        ax1.set_xticks([])
        ax1.plot(plt_date_pepa_acc, plt_pepa_acc_x, "b--", linewidth=1)
        ax1.set_title('PEPA_ACC_X')
        
        ax2 = plot.add_subplot(4,4,5)
        ax2.set_xticks([])
        ax2.plot(plt_date_pepa_acc, plt_pepa_acc_y, "b--", linewidth=1)
        ax2.set_title('PEPA_ACC_Y')
    
        ax3 = plot.add_subplot(4,4,9)
        ax3.set_xticks([])
        ax3.plot(plt_date_pepa_acc, plt_pepa_acc_z, "b--", linewidth=1)
        ax3.set_title('PEPA_ACC_Z')
        
        # salt acc plot
        ax4 = plot.add_subplot(4,4,2)
        ax4.set_xticks([])
        ax4.plot(plt_date_salt_acc, plt_salt_acc_x, "b--", linewidth=1)
        ax4.set_title('SALT_ACC_X')
        
        ax5 = plot.add_subplot(4,4,6)
        ax5.set_xticks([])
        ax5.plot(plt_date_salt_acc, plt_salt_acc_y, "b--", linewidth=1)
        ax5.set_title('SALT_ACC_Y')
    
        ax6 = plot.add_subplot(4,4,10)
        ax6.set_xticks([])
        ax6.plot(plt_date_salt_acc, plt_salt_acc_z, "b--", linewidth=1)
        ax6.set_title('SALT_ACC_Z')
        
        # pepa qua plot
        ax7 = plot.add_subplot(4,4,3)
        ax7.set_xticks([])
        ax7.plot(plt_date_pepa_qua, plt_pepa_qua_w, "b--", linewidth=1)
        ax7.set_title('PEPA_QUA_W')
        
        ax8 = plot.add_subplot(4,4,7)
        ax8.set_xticks([])
        ax8.plot(plt_date_pepa_qua, plt_pepa_qua_x, "b--", linewidth=1)
        ax8.set_title('PEPA_QUA_X')
    
        ax9 = plot.add_subplot(4,4,11)
        ax9.set_xticks([])
        ax9.plot(plt_date_pepa_qua, plt_pepa_qua_y, "b--", linewidth=1)
        ax9.set_title('PEPA_QUA_Y')

        ax10 = plot.add_subplot(4,4,15)
        ax10.set_xticks([])
        ax10.plot(plt_date_pepa_qua, plt_pepa_qua_z, "b--", linewidth=1)
        ax10.set_title('PEPA_QUA_Z')
        
        # salt qua plot
        ax11 = plot.add_subplot(4,4,4)
        ax11.set_xticks([])
        ax11.plot(plt_date_salt_qua, plt_salt_qua_w, "b--", linewidth=1)
        ax11.set_title('SALT_QUA_W')
        
        ax12 = plot.add_subplot(4,4,8)
        ax12.set_xticks([])
        ax12.plot(plt_date_salt_qua, plt_salt_qua_x, "b--", linewidth=1)
        ax12.set_title('SALT_QUA_X')
    
        ax13 = plot.add_subplot(4,4,12)
        ax13.set_xticks([])
        ax13.plot(plt_date_salt_qua, plt_salt_qua_y, "b--", linewidth=1)
        ax13.set_title('SALT_QUA_Y')

        ax14 = plot.add_subplot(4,4,16)
        ax14.set_xticks([])
        ax14.plot(plt_date_salt_qua, plt_salt_qua_z, "b--", linewidth=1)
        ax14.set_title('SALT_QUA_Z')
        
        # table has been defined here
        ax15 = plot.add_subplot(4,4,13)
        table = ax15.table(
                cellText=table_content,
                cellLoc = 'center',
                colLabels = ['Date', 'Average anomaly score', 'Duration (seconds)'],
                bbox=[0, -0.55, 3, 1.8]
                )
        table.scale(4, 4)
        ax15.axis("off")  
        
        plot.show()
        plt.pause(1e-17)
        
        time.sleep(1)
        plot.clf()


if __name__ == "__main__":
    
    # Simulation data
    pepa_acc_file = '/media/tpc2/DATA/ProcessedLanceData/pepa_acc_timestep3.csv'
    salt_acc_file = '/media/tpc2/DATA/ProcessedLanceData/salt_acc_timestep3.csv'
    pepa_qua_file = '/media/tpc2/DATA/ProcessedLanceData/pepa_qua_timestep3.csv'
    salt_qua_file = '/media/tpc2/DATA/ProcessedLanceData/salt_qua_timestep3.csv'
    
    # Global parameters
    _VERBOSITY = 0
    _NUM_RECORDS = 153501
    
    # -------------------------------------------------------------------------
    #
    #
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
    
    #--------------------------------------------------------------------------
    #
    #
    # The encoder fields for inputs
    scalarEncoder1Args = {
      "w": 21,
      "minval": 0.97 - 0.03,
      "maxval": 0.97 + 0.03,
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
      "minval": -0.002 - 0.005,
      "maxval": -0.002 + 0.005,
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
      "minval": -0.012 - 0.005,
      "maxval": -0.012 + 0.005,
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
      "minval": 0.96 - 0.03,
      "maxval": 0.96 + 0.03,
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
      "minval": 0.050 - 0.010,
      "maxval": 0.050 + 0.010,
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
      "minval": 0.025 - 0.010,
      "maxval": 0.025 + 0.010,
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
      "minval": -0.48 - 0.05,
      "maxval": -0.48 + 0.05,
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
      "minval": 0.51 - 0.05,
      "maxval": 0.51 + 0.05,
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
      "minval": -0.49 - 0.05,
      "maxval": -0.49 + 0.05,
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
      "minval": 0.50 - 0.05,
      "maxval": 0.50 + 0.05,
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
      "minval": 0.43 - 0.05,
      "maxval": 0.43 + 0.05,
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
      "minval": -0.57 - 0.05,
      "maxval": -0.57 + 0.05,
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
      "minval": 0.39 - 0.05,
      "maxval": 0.39 + 0.05,
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
      "minval": -0.56 - 0.05,
      "maxval": -0.56 + 0.05,
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
    
    #--------------------------------------------------------------------------
    #
    #
    # Generate networks and run them
    pepa_acc_network = createTemporalAnomaly_acc(pepa_acc_recordParams, spatialParams=_SP_PARAMS, temporalParams=_TM_PARAMS, verbosity=_VERBOSITY)
    salt_acc_network = createTemporalAnomaly_acc(salt_acc_recordParams, spatialParams=_SP_PARAMS, temporalParams=_TM_PARAMS, verbosity=_VERBOSITY)
    pepa_qua_network = createTemporalAnomaly_qua(pepa_qua_recordParams, spatialParams=_SP_PARAMS, temporalParams=_TM_PARAMS, verbosity=_VERBOSITY)
    salt_qua_network = createTemporalAnomaly_qua(salt_qua_recordParams, spatialParams=_SP_PARAMS, temporalParams=_TM_PARAMS, verbosity=_VERBOSITY)

    pepa_acc_date = getDate(pepa_acc_recordParams, _NUM_RECORDS)
    salt_acc_date = getDate(salt_acc_recordParams, _NUM_RECORDS)
    pepa_qua_date = getDate(pepa_qua_recordParams, _NUM_RECORDS)
    salt_qua_date = getDate(salt_qua_recordParams, _NUM_RECORDS)
    
    runNetwork(pepa_acc_network, salt_acc_network, pepa_qua_network, salt_qua_network, pepa_acc_date, salt_acc_date, pepa_qua_date, salt_qua_date)
