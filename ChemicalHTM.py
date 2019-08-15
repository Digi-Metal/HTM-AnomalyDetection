#!/usr/bin/env python
# coding: utf-8

import matplotlib.pyplot as plt
import csv
from itertools import islice
import json
import time
from datetime import datetime
from nupic.data.file_record_stream import FileRecordStream
from nupic.engine import Network
from nupic.encoders import MultiEncoder, ScalarEncoder, DateEncoder


def createTemporalAnomaly_chemical(recordParams, spatialParams, temporalParams, verbosity):

    inputFilePath = recordParams["inputFilePath"]
    scalarEncoder1Args = recordParams["scalarEncoder1Args"]
    scalarEncoder2Args = recordParams["scalarEncoder2Args"]
    scalarEncoder3Args = recordParams["scalarEncoder3Args"]
    scalarEncoder4Args = recordParams["scalarEncoder4Args"]
    scalarEncoder5Args = recordParams["scalarEncoder5Args"]
    scalarEncoder6Args = recordParams["scalarEncoder6Args"]
    scalarEncoder7Args = recordParams["scalarEncoder7Args"]
    dateEncoderArgs = recordParams["dateEncoderArgs"]

    scalarEncoder1 = ScalarEncoder(**scalarEncoder1Args)
    scalarEncoder2 = ScalarEncoder(**scalarEncoder2Args)
    scalarEncoder3 = ScalarEncoder(**scalarEncoder3Args)
    scalarEncoder4 = ScalarEncoder(**scalarEncoder4Args)
    scalarEncoder5 = ScalarEncoder(**scalarEncoder5Args)
    scalarEncoder6 = ScalarEncoder(**scalarEncoder6Args)
    scalarEncoder7 = ScalarEncoder(**scalarEncoder7Args)    
    dateEncoder = DateEncoder(**dateEncoderArgs)

    encoder = MultiEncoder()
    encoder.addEncoder(scalarEncoder1Args["name"], scalarEncoder1)
    encoder.addEncoder(scalarEncoder2Args["name"], scalarEncoder2)
    encoder.addEncoder(scalarEncoder3Args["name"], scalarEncoder3)
    encoder.addEncoder(scalarEncoder4Args["name"], scalarEncoder4)
    encoder.addEncoder(scalarEncoder5Args["name"], scalarEncoder5)
    encoder.addEncoder(scalarEncoder6Args["name"], scalarEncoder6)
    encoder.addEncoder(scalarEncoder7Args["name"], scalarEncoder7)
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


def get_round(input_list, n):
    result = []
    for i in input_list:
        result.append(round(i, n))
    return result


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
            date.append(Record_in_Dict["Time"])
    return date


def plot_chemical_data(Bath_T, CaO, Fe_SiO2, Cu_Slag, Cu_Matte, Fe, SiO2, date, buffer_size=800):
    if len(Bath_T) > buffer_size and len(CaO) > buffer_size and len(Fe_SiO2) > buffer_size and len(Cu_Slag) > buffer_size and len(Cu_Matte) > buffer_size and len(Fe) > buffer_size and len(SiO2) > buffer_size:
        new_Bath_T = Bath_T[-buffer_size:]        
        new_CaO = CaO[-buffer_size:]
        new_Fe_SiO2 = Fe_SiO2[-buffer_size:]
        new_Cu_Slag = Cu_Slag[-buffer_size:]
        new_Cu_Matte = Cu_Matte[-buffer_size:]
        new_Fe = Fe[-buffer_size:]
        new_SiO2 = SiO2[-buffer_size:]
        new_date = date[-buffer_size:]
        
#        new_CaO = get_round(new_CaO, 5)
#        new_Fe_SiO2 = get_round(new_Fe_SiO2, 5)
#        new_Cu_Slag = get_round(new_Cu_Slag, 5)
#        new_Cu_Matte = get_round(new_Cu_Matte, 5)
#        new_Fe = get_round(new_Fe, 5)
#        new_SiO2 = get_round(new_SiO2, 5)
        
        return new_Bath_T, new_CaO, new_Fe_SiO2, new_Cu_Slag, new_Cu_Matte, new_Fe, new_SiO2, new_date
    else:
#        CaO = get_round(CaO, 5)
#        Fe_SiO2 = get_round(Fe_SiO2, 5)
#        Cu_Slag = get_round(Cu_Slag, 5)
#        Cu_Matte = get_round(Cu_Matte, 5)
#        Fe = get_round(Fe, 5)
#        SiO2 = get_round(SiO2, 5)
        return Bath_T, CaO, Fe_SiO2, Cu_Slag, Cu_Matte, Fe, SiO2, date

    
def plot_input_data(lance_air, lance_oxy, silica_flux, lime_flux, use_anomalies, date, buffer_size=800):
    if len(lance_air) > buffer_size and len(lance_oxy) > buffer_size and len(silica_flux) > buffer_size and len(lime_flux) > buffer_size and len(use_anomalies) > buffer_size:
        new_lance_air = lance_air[-buffer_size:]
        new_lance_oxy = lance_oxy[-buffer_size:]
        new_silica_flux = silica_flux[-buffer_size:]
        new_lime_flux = lime_flux[-buffer_size:]
        new_use_anomalies = use_anomalies[-buffer_size:]
        new_date = date[-buffer_size:]
        return new_lance_air, new_lance_oxy, new_silica_flux, new_lime_flux, new_use_anomalies, new_date
    else:        
        return lance_air, lance_oxy, silica_flux, lime_flux, use_anomalies, date
    
    
def runNetwork(network, date1, input_data_file):
    sensorRegion = network.regions["sensor"]
    temporalPoolerRegion = network.regions["temporalPoolerRegion"]

    # output data
    date = []
    Bath_T = []
    CaO = []
    Fe_SiO2 = []
    Cu_Slag = []
    Cu_Matte = []
    Fe = []
    SiO2 = []
    
    # input data
    lance_air = []
    lance_oxy = []
    silica_flux = []
    lime_flux = []
    use_anomalies = []
    
    plt_lance_air = []
    plt_lance_oxy = []
    plt_silica_flux = []
    plt_lime_flux = []
    plt_use_anomalies = []
    
    # initial input data to display
    with open(input_data_file) as fin:
        reader = csv.reader(fin)
        headers = reader.next()
        reader.next()
        reader.next()
        for record in reader:
            record_dict = dict(zip(headers, record))
            lance_air.append(float(record_dict["Lance Air"]))
            lance_oxy.append(float(record_dict["Lance Oxygen"]))
            silica_flux.append(float(record_dict["Silica Flux"]))
            lime_flux.append(float(record_dict["Lime Flux"]))
            use_anomalies.append(int(record_dict["Use Nominals"]))
    
    # intial table and other parameters below        
    table_content = [[' ', ' ', ' '],[' ', ' ', ' '],[' ', ' ', ' '],[' ', ' ', ' ']]
    status_table_content = [[' ', ' ', ' ']]
    status_table_color = [["w", "", ""]]
    previous_result = 'G'
    contineous_flag = False

    plot = plt.figure("Outotec Motion Anomaly Detection", figsize=(32, 6))
    plot.subplots_adjust(wspace =1, hspace =0.5)
    plot.subplots(ncols=2, nrows=3)
    
    for i in xrange(_NUM_RECORDS):
        network.run(1)
        anomalyScore = temporalPoolerRegion.getOutputData("anomalyScore")[0]
        pre1_1 = sensorRegion.getOutputData("sourceOut")[0]
        pre2_1 = sensorRegion.getOutputData("sourceOut")[1]
        pre3_1 = sensorRegion.getOutputData("sourceOut")[2]
        pre4_1 = sensorRegion.getOutputData("sourceOut")[3]
        pre5_1 = sensorRegion.getOutputData("sourceOut")[4]
        pre6_1 = sensorRegion.getOutputData("sourceOut")[5]
        pre7_1 = sensorRegion.getOutputData("sourceOut")[6]
        
        Bath_T.append(pre1_1)
        CaO.append(pre2_1)
        Fe_SiO2.append(pre3_1)
        Cu_Slag.append(pre4_1)
        Cu_Matte.append(pre5_1)
        Fe.append(pre6_1)
        SiO2.append(pre7_1)
        
        # append the input data
        plt_lance_air.append(lance_air[i])
        plt_lance_oxy.append(lance_oxy[i])
        plt_silica_flux.append(silica_flux[i])
        plt_lime_flux.append(lime_flux[i])
        plt_use_anomalies.append(use_anomalies[i])
        
        average_anomalyScore = anomalyScore
        
        date.append(date1[i])

#        print "Date: ", date1[i], "  Chemical Anomaly Score:", anomalyScore
#        print "    --> Bath_T:   \t", pre1_1
#        print "        CaO:      \t", pre2_1
#        print "        Fe/SiO2:  \t", pre3_1
#        print "        Cu Slag:  \t", pre4_1
#        print "        Cu Matte: \t", pre5_1
#        print "        Fe:       \t", pre6_1
#        print "        SiO2:     \t", pre7_1

        if average_anomalyScore < 0.1:
#            print "        \033[1;42m GOOD CONDITION \033[0m"
            previous_result = 'G'
            status_table_content[0][0] = date1[i]
            status_table_content[0][1] = 'GOOD CONDITION'
            status_table_color[0][1] = '#31de5f'
            status_table_content[0][2] = anomalyScore
            status_table_color[0][2] = 'w'
        elif average_anomalyScore > 0.1 and average_anomalyScore < 0.2:
#            print "        \033[1;43m WARNING CAUTION \033[0m"
            previous_result = 'W'
            status_table_content[0][0] = date1[i]
            status_table_content[0][1] = 'WARNING CAUTION'
            status_table_color[0][1] = '#ff9e36'
            status_table_content[0][2] = anomalyScore
            status_table_color[0][2] = 'w'
        else:
            if previous_result == 'D':
                contineous_flag = True
            else:
                contineous_flag = False

            if table_content[0][0] == ' ' and contineous_flag == False:
                table_content[0][0] = date1[i]
                table_content[0][1] = str(average_anomalyScore) + ' (B)'
                table_content[0][2] = float(0)
            elif table_content[1][0] == ' ' and contineous_flag == False:
                table_content[1][0] = date1[i]
                table_content[1][1] = str(average_anomalyScore) + ' (B)'
                table_content[1][2] = float(0)
            elif table_content[2][0] == ' ' and contineous_flag == False:
                table_content[2][0] = date1[i]
                table_content[2][1] = str(average_anomalyScore) + ' (B)'
                table_content[2][2] = float(0)
            elif table_content[3][0] == ' ' and contineous_flag == False:
                table_content[3][0] = date1[i]
                table_content[3][1] = str(average_anomalyScore) + ' (B)'
                table_content[3][2] = float(0)         
            elif table_content[1][0] == ' ' and contineous_flag == True:
                table_content[0][0] = date1[i]
                table_content[0][1] = str(average_anomalyScore) + ' (B)'
                table_content[0][2] += seconds_difference(date1[i-1], date1[i])
            elif table_content[2][0] == ' ' and contineous_flag == True:
                table_content[1][0] = date1[i]
                table_content[1][1] = str(average_anomalyScore) + ' (B)'
                table_content[1][2] += seconds_difference(date1[i-1], date1[i])
            elif table_content[3][0] == ' ' and contineous_flag == True:
                table_content[2][0] = date1[i]
                table_content[2][1] = str(average_anomalyScore) + ' (B)'
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
                table_content[3][1] = str(average_anomalyScore) + ' (B)'
                table_content[3][2] = 0
            elif table_content[0][0] != ' ' and table_content[1][0] != ' ' and table_content[2][0] != ' ' and table_content[3][0] != ' ' and contineous_flag == True:                
                table_content[3][0] = date1[i]
                table_content[3][1] = str(average_anomalyScore) + ' (B)'
                table_content[3][2] += seconds_difference(date1[i-1], date1[i])   
#            print "        \033[1;41m DANGEROUS CONDITION \033[0m"
            previous_result = 'D'
            status_table_content[0][0] = date1[i]
            status_table_content[0][1] = 'BAD CONDITION'
            status_table_color[0][1] = '#db4439'
            status_table_content[0][2] = anomalyScore
            status_table_color[0][2] = 'w'
#        print "\n"        

        plt_BathT, plt_CaO, plt_Fe_SiO2, plt_Cu_Slag, plt_Cu_Matte, plt_Fe, plt_SiO2, plt_date = plot_chemical_data(Bath_T, CaO, Fe_SiO2, Cu_Slag, Cu_Matte, Fe, SiO2, date)
        plt2_lance_air, plt2_lance_oxy, plt2_silica_flux, plt2_lime_flux, plt2_use_anomalies, plt2_date = plot_input_data(plt_lance_air, plt_lance_oxy, plt_silica_flux, plt_lime_flux, plt_use_anomalies, date)

        # display the input data
        ax1 = plot.add_subplot(3,6,1)
        ax1.set_xticks([])
        ax1.plot(plt2_date, plt2_lance_air, "r--", linewidth=1)
        ax1.set_title('Lance Air\n')
        
        ax2 = plot.add_subplot(3,6,2)
        ax2.set_xticks([])
        ax2.plot(plt2_date, plt2_lance_oxy, "r--", linewidth=1)
        ax2.set_title('Lance Oxygen\n')
    
        ax3 = plot.add_subplot(3,6,3)
        ax3.set_xticks([])
        ax3.plot(plt2_date, plt2_silica_flux, "r--", linewidth=1)
        ax3.set_title('Silica Flux\n')
        
        ax4 = plot.add_subplot(3,6,4)
        ax4.set_xticks([])
        ax4.plot(plt2_date, plt2_lime_flux, "r--", linewidth=1)
        ax4.set_title('Lime Flux\n')
        
        ax5 = plot.add_subplot(3,6,5)
        ax5.set_xticks([])
        ax5.plot(plt2_date, plt2_use_anomalies, "g-", linewidth=2)
        ax5.set_title('Use Nominals\n')
        
        # Chemical plot
        ax6 = plot.add_subplot(3,6,6)
        ax6.set_xticks([])
        ax6.plot(plt_date, plt_BathT, "b--", linewidth=1)
        ax6.set_title('Bath T\n')
        
        ax7 = plot.add_subplot(3,6,7)
        ax7.set_xticks([])
        ax7.plot(plt_date, plt_CaO, "b--", linewidth=1)
        ax7.set_title('CaO\n')
        
        ax8 = plot.add_subplot(3,6,8)
        ax8.set_xticks([])
        ax8.plot(plt_date, plt_Fe_SiO2, "b--", linewidth=1)
        ax8.set_title('Fe/SiO2\n')
    
        ax9 = plot.add_subplot(3,6,9)
        ax9.set_xticks([])
        ax9.plot(plt_date, plt_Cu_Slag, "b--", linewidth=1)
        ax9.set_title('Cu Slag\n')
        
        ax10 = plot.add_subplot(3,6,10)
        ax10.set_xticks([])
        ax10.plot(plt_date, plt_Cu_Matte, "b--", linewidth=1)
        ax10.set_title('Cu Matte\n')
        
        ax11 = plot.add_subplot(3,6,11)
        ax11.set_xticks([])
        ax11.plot(plt_date, plt_Fe, "b--", linewidth=1)
        ax11.set_title('Fe\n')
    
        ax12 = plot.add_subplot(3,6,12)
        ax12.set_xticks([])
        ax12.plot(plt_date, plt_SiO2, "b--", linewidth=1)
        ax12.set_title('SiO2\n')
        
        # table has been defined here
        ax13 = plot.add_subplot(3,6,13)
        table = ax13.table(
                cellText = table_content,
                cellLoc = 'center',
                colLabels = ['Log date', 'Average anomaly score', 'Duration (seconds)'],
                bbox=[0, -0.5, 5, 1.6]
                )
        table.scale(6, 6)
        ax13.axis("off")
        
        for key, cell in table.get_celld().items():
            cell.set_linewidth(0.5)
            
        # status showing table has been defined here
        ax14 = plot.add_subplot(3,6,16)
        table = ax14.table(
                cellText = status_table_content,
                cellColours = status_table_color,
                cellLoc = 'center',
                colLabels = ['Current date', 'Predicted Status', 'Anomaly Score'],
                bbox=[0, -0.3, 5, 1.4]
                )
        table.scale(5.5, 5.5)
        ax14.axis("off")
        
        for key, cell in table.get_celld().items():
            cell.set_linewidth(0.5)
        
        plot.show()
        plt.pause(1e-17)
        
        time.sleep(1.5)
        plot.clf()


if __name__ == "__main__":
    
    # Simulation data
#    output_data_feed_rate = 'D:\\chemical_data\\output_feed_rate.csv'
    
    output_data_feed_rate = '/media/tpc2/DATA/chemical_data/output_feed_rate.csv'
    input_data_feed_rate = '/media/tpc2/DATA/chemical_data/input_feed_rate.csv'
    
    # Global parameters
    _VERBOSITY = 0
    _NUM_RECORDS = 899
    
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
      "minval": 1200.00 - 16.00,
      "maxval": 1200.00 + 16.00,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "Bath T",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }
        
    scalarEncoder2Args = {
      "w": 21,
      "minval": 5.00 - 0.025,
      "maxval": 5.00 + 0.025,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "CaO %",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }
    
    scalarEncoder3Args = {
      "w": 21,
      "minval": 1.249 - 0.005,
      "maxval": 1.249 + 0.005,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "Fe/SiO2",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }

    scalarEncoder4Args = {
      "w": 21,
      "minval": 0.0119 - 0.001,
      "maxval": 0.0119 + 0.001,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "Cu Slag",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }
    
    scalarEncoder5Args = {
      "w": 21,
      "minval": 59.93 - 0.5,
      "maxval": 59.93 + 0.5,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "Cu Matte",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }

    scalarEncoder6Args = {
      "w": 21,
      "minval": 38.90 - 0.06,
      "maxval": 38.90 + 0.06,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "Fe %",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }

    scalarEncoder7Args = {
      "w": 21,
      "minval": 31.13 - 0.05,
      "maxval": 31.13 + 0.05,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "SiO2 %",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }
        
    dateEncoderArgs = {
      "season": 0,
      "dayOfWeek": 0,
      "weekend": 0,
      "holiday": 0,
      "timeOfDay": (21, 0.3),
      "customDays": 0,
      "name": "Time",
      "forced": False
    }

    chemical_recordParams = {
      "inputFilePath": output_data_feed_rate,
      "scalarEncoder1Args": scalarEncoder1Args,
      "scalarEncoder2Args": scalarEncoder2Args,
      "scalarEncoder3Args": scalarEncoder3Args,
      "scalarEncoder4Args": scalarEncoder4Args,
      "scalarEncoder5Args": scalarEncoder5Args,
      "scalarEncoder6Args": scalarEncoder6Args,
      "scalarEncoder7Args": scalarEncoder7Args,
      "dateEncoderArgs": dateEncoderArgs,
    }
    
    #--------------------------------------------------------------------------
    #
    #
    # Generate networks and run them
    chemical_network = createTemporalAnomaly_chemical(chemical_recordParams,
                                                      spatialParams=_SP_PARAMS,
                                                      temporalParams=_TM_PARAMS,
                                                      verbosity=_VERBOSITY)
    
    chemical_date = getDate(chemical_recordParams, _NUM_RECORDS) 
    
    runNetwork(chemical_network, chemical_date, input_data_feed_rate)
