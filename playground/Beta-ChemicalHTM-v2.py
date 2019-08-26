#!/usr/bin/env python
# coding: utf-8
'''
This script is suitable for the latest version of chemical data

This script starts from version 2.0
'''

import matplotlib.pyplot as plt
import csv
from itertools import islice
import json
import time
from datetime import datetime
from nupic.data.file_record_stream import FileRecordStream
from nupic.engine import Network
from nupic.encoders import MultiEncoder, ScalarEncoder, DateEncoder


def createTemporalAnomaly(recordParams, spatialParams, temporalParams, verbosity):

    inputFilePath = recordParams["inputFilePath"]
    scalarEncoder1Args = recordParams["scalarEncoder1Args"]
    dateEncoderArgs = recordParams["dateEncoderArgs"]

    scalarEncoder1 = ScalarEncoder(**scalarEncoder1Args)  
    dateEncoder = DateEncoder(**dateEncoderArgs)

    encoder = MultiEncoder()
    encoder.addEncoder(scalarEncoder1Args["name"], scalarEncoder1)
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
    
    # Add the AnomalyLikelihoodRegion on top of the TMRegion
    network.addRegion("anomalyLikelihoodRegion", "py.AnomalyLikelihoodRegion", json.dumps({}))
    network.link("temporalPoolerRegion", "anomalyLikelihoodRegion", "UniformLink",
                 "", srcOutput="anomalyScore", destInput="rawAnomalyScore")
    network.link("sensor", "anomalyLikelihoodRegion", "UniformLink", "",
                 srcOutput="sourceOut", destInput="metricValue")    


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


def reverse(in_list):
    out_list = []
    for i in in_list:
        if int(i) == 0:
            out_list.append(1)
        else:
            out_list.append(0)
    return out_list


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


def plot_chemical_data(matte_cu, 
                       matte_fe, 
                       matte_pb, 
                       matte_zn, 
                       slag_cu, 
                       slag_fe, 
                       slag_pb, 
                       slag_zn, 
                       fe_sio2,
                       slag_cao,
                       bath_t,
                       freeboard_t,
                       date,
                       buffer_size=500):
    # sliding
    if len(matte_cu) > buffer_size:
        new_matte_cu = matte_cu[-buffer_size:]        
        new_matte_fe = matte_fe[-buffer_size:]
        new_matte_pb = matte_pb[-buffer_size:]
        new_matte_zn = matte_zn[-buffer_size:]
        new_slag_cu = slag_cu[-buffer_size:]
        new_slag_fe = slag_fe[-buffer_size:]
        new_slag_pb = slag_pb[-buffer_size:]
        new_slag_zn = slag_zn[-buffer_size:]
        new_fe_sio2 = fe_sio2[-buffer_size:]
        new_slag_cao = slag_cao[-buffer_size:]
        new_bath_t = bath_t[-buffer_size:]
        new_freeboard_t = freeboard_t[-buffer_size:]
        new_date = date[-buffer_size:]        
        return new_matte_cu, new_matte_fe, new_matte_pb, new_matte_zn, \
               new_slag_cu, new_slag_fe, new_slag_pb, new_slag_zn, \
               new_fe_sio2, new_slag_cao, new_bath_t, \
               new_freeboard_t, new_date
    # or buffering
    else:
        return matte_cu, matte_fe, matte_pb, matte_zn, slag_cu, slag_fe, slag_pb, \
               slag_zn, fe_sio2, slag_cao, bath_t, \
               freeboard_t, date

    
def plot_input_data(lance_air, 
                    lance_oxy, 
                    actual_moisture1, 
                    actual_moisture2, 
                    actual_conc, 
                    actual_feed,
                    use_anomalies1,
                    use_anomalies2,
                    use_anomalies3,
                    use_anomalies4,
                    date, 
                    buffer_size=500):
    
    if len(lance_air) > buffer_size:
        new_lance_air = lance_air[-buffer_size:]
        new_lance_oxy = lance_oxy[-buffer_size:]
        new_actual_moisture1 = actual_moisture1[-buffer_size:]
        new_actual_moisture2 = actual_moisture2[-buffer_size:]
        new_actual_conc = actual_conc[-buffer_size:]
        new_actual_feed = actual_feed[-buffer_size:]
        new_use_anomalies1 = use_anomalies1[-buffer_size:]
        new_use_anomalies2 = use_anomalies2[-buffer_size:]
        new_use_anomalies3 = use_anomalies3[-buffer_size:]
        new_use_anomalies4 = use_anomalies4[-buffer_size:]
        new_date = date[-buffer_size:]
        return new_lance_air, new_lance_oxy, new_actual_moisture1, \
               new_actual_moisture2, new_actual_conc, new_actual_feed, \
               new_use_anomalies1, new_use_anomalies2, new_use_anomalies3, \
               new_use_anomalies4, new_date
    else:        
        return lance_air, lance_oxy, actual_moisture1, actual_moisture2, \
               actual_conc, actual_feed, use_anomalies1, use_anomalies2, use_anomalies3, \
               use_anomalies4, date


def plot_anomaly_data(anomalies_history, 
                      date, 
                      buffer_size=500):
    
    if len(anomalies_history) > buffer_size:
        new_anomalies_history = anomalies_history[-buffer_size:]
        new_date = date[-buffer_size:]
        return new_anomalies_history, new_date
    else:        
        return anomalies_history, date
    
    
def runNetwork(network1,
               network2,
               network3,
               network4,
               network5,
               network6,
               network7,
               network8,
               network9,
               network10,
               network11,
               network12,
               date1, 
               input_data_file):
    
    sensorRegion1 = network1.regions["sensor"]
    anomalyLikelihoodRegion1 = network1.regions["anomalyLikelihoodRegion"]
    sensorRegion2 = network2.regions["sensor"]
    anomalyLikelihoodRegion2 = network2.regions["anomalyLikelihoodRegion"]
    sensorRegion3 = network3.regions["sensor"]
    anomalyLikelihoodRegion3 = network3.regions["anomalyLikelihoodRegion"]
    sensorRegion4 = network4.regions["sensor"]
    anomalyLikelihoodRegion4 = network4.regions["anomalyLikelihoodRegion"]
    sensorRegion5 = network5.regions["sensor"]
    anomalyLikelihoodRegion5 = network5.regions["anomalyLikelihoodRegion"]
    sensorRegion6 = network6.regions["sensor"]
    anomalyLikelihoodRegion6 = network6.regions["anomalyLikelihoodRegion"]
    sensorRegion7 = network7.regions["sensor"]
    anomalyLikelihoodRegion7 = network7.regions["anomalyLikelihoodRegion"]
    sensorRegion8 = network8.regions["sensor"]
    anomalyLikelihoodRegion8 = network8.regions["anomalyLikelihoodRegion"]
    sensorRegion9 = network9.regions["sensor"]
    anomalyLikelihoodRegion9 = network9.regions["anomalyLikelihoodRegion"]
    sensorRegion10 = network10.regions["sensor"]
    anomalyLikelihoodRegion10 = network10.regions["anomalyLikelihoodRegion"]
    sensorRegion11 = network11.regions["sensor"]
    anomalyLikelihoodRegion11 = network11.regions["anomalyLikelihoodRegion"]   
    sensorRegion12 = network12.regions["sensor"]
    anomalyLikelihoodRegion12 = network12.regions["anomalyLikelihoodRegion"]   

    # output data
    date = []
    matte_cu = []
    matte_fe = []
    matte_pb = []
    matte_zn = []
    slag_cu = []
    slag_fe = []
    slag_pb = []
    slag_zn = []
    fe_sio2 = []
    slag_cao = []
    bath_t = []
    freeboard_t = []
    
    # input data
    lance_air = []
    lance_oxy = []
    actual_moisture1 = []
    actual_moisture2 = []
    actual_conc = []
    actual_feed = []
    use_anomalies1 = []
    use_anomalies2 = []
    use_anomalies3 = []
    use_anomalies4 = []
    
    plt_lance_air = []
    plt_lance_oxy = []
    plt_actual_moisture1 = []
    plt_actual_moisture2 = []
    plt_actual_conc =[]
    plt_actual_feed = []
    plt_use_anomalies1 = []
    plt_use_anomalies2 = []
    plt_use_anomalies3 = []
    plt_use_anomalies4 = []
    
#    # data used for evaluation
#    status_records = []
    
    # data used to plot anomalies
    plt_bad_records = []
    
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
            actual_moisture1.append(float(record_dict["Actual Moisture 1"]))
            actual_moisture2.append(float(record_dict["Actual Moisture 2"]))
            actual_conc.append(float(record_dict["Actual Conc 1 %"]))
            actual_feed.append(float(record_dict["Actual Feed"]))
            use_anomalies1.append(int(record_dict["Moisture 1 AF"]))
            use_anomalies2.append(int(record_dict["Moisture 2 AF"]))
            use_anomalies3.append(int(record_dict["Blend AF"]))
            use_anomalies4.append(int(record_dict["Feed AF"]))
    
    # intial table and other parameters below        
    table_content = [[' ', ' ', ' '],[' ', ' ', ' '],[' ', ' ', ' '],[' ', ' ', ' ']]
    status_table_content = [[' ', ' ', ' ']]
    status_table_color = [["w", "", ""]]
    previous_result = 'G'
    contineous_flag = False

    plot = plt.figure("Outotec Motion Anomaly Detection", figsize=(32, 16))
    plot.subplots_adjust(wspace =1, hspace =0.5)
    plot.subplots(ncols=2, nrows=3)
    
    for i in xrange(_NUM_RECORDS):
        network1.run(1)
        anomalyLikelihood1 = anomalyLikelihoodRegion1.getOutputData("anomalyLikelihood")[0]
        pre1_1 = sensorRegion1.getOutputData("sourceOut")[0]
        
        network2.run(1)
        anomalyLikelihood2 = anomalyLikelihoodRegion2.getOutputData("anomalyLikelihood")[0]
        pre2_1 = sensorRegion2.getOutputData("sourceOut")[0]
        
        network3.run(1)
        anomalyLikelihood3 = anomalyLikelihoodRegion3.getOutputData("anomalyLikelihood")[0]
        pre3_1 = sensorRegion3.getOutputData("sourceOut")[0]
        
        network4.run(1)
        anomalyLikelihood4 = anomalyLikelihoodRegion4.getOutputData("anomalyLikelihood")[0]
        pre4_1 = sensorRegion4.getOutputData("sourceOut")[0]
        
        network5.run(1)
        anomalyLikelihood5 = anomalyLikelihoodRegion5.getOutputData("anomalyLikelihood")[0]
        pre5_1 = sensorRegion5.getOutputData("sourceOut")[0]
        
        network6.run(1)
        anomalyLikelihood6 = anomalyLikelihoodRegion6.getOutputData("anomalyLikelihood")[0]
        pre6_1 = sensorRegion6.getOutputData("sourceOut")[0]
        
        network7.run(1)
        anomalyLikelihood7 = anomalyLikelihoodRegion7.getOutputData("anomalyLikelihood")[0]
        pre7_1 = sensorRegion7.getOutputData("sourceOut")[0]
        
        network8.run(1)
        anomalyLikelihood8 = anomalyLikelihoodRegion8.getOutputData("anomalyLikelihood")[0]
        pre8_1 = sensorRegion8.getOutputData("sourceOut")[0]
        
        network9.run(1)
        anomalyLikelihood9 = anomalyLikelihoodRegion9.getOutputData("anomalyLikelihood")[0]
        pre9_1 = sensorRegion9.getOutputData("sourceOut")[0]
        
        network10.run(1)
        anomalyLikelihood10 = anomalyLikelihoodRegion10.getOutputData("anomalyLikelihood")[0]
        pre10_1 = sensorRegion10.getOutputData("sourceOut")[0]
        
        network11.run(1)
        anomalyLikelihood11 = anomalyLikelihoodRegion11.getOutputData("anomalyLikelihood")[0]
        pre11_1 = sensorRegion11.getOutputData("sourceOut")[0]
        
        network12.run(1)
        anomalyLikelihood12 = anomalyLikelihoodRegion12.getOutputData("anomalyLikelihood")[0]
        pre12_1 = sensorRegion12.getOutputData("sourceOut")[0]
        
        avg_anomaly_likelihood = mean([anomalyLikelihood1,
                                       anomalyLikelihood2,
                                       anomalyLikelihood3,
                                       anomalyLikelihood4,
                                       anomalyLikelihood5,
                                       anomalyLikelihood6,
                                       anomalyLikelihood7,
                                       anomalyLikelihood8,
                                       anomalyLikelihood9,
                                       anomalyLikelihood10,
                                       anomalyLikelihood11,
                                       anomalyLikelihood12])

        matte_cu.append(pre1_1)
        matte_fe.append(pre2_1)
        matte_pb.append(pre3_1)
        matte_zn.append(pre4_1)
        slag_cu.append(pre5_1)
        slag_fe.append(pre6_1)
        slag_pb.append(pre7_1)
        slag_zn.append(pre8_1)
        fe_sio2.append(pre9_1)
        slag_cao.append(pre10_1)
        bath_t.append(pre11_1)
        freeboard_t.append(pre12_1)
        
        # append the input data
        plt_lance_air.append(lance_air[i])
        plt_lance_oxy.append(lance_oxy[i])
        plt_actual_moisture1.append(actual_moisture1[i])
        plt_actual_moisture2.append(actual_moisture2[i])
        plt_actual_conc.append(actual_conc[i])
        plt_actual_feed.append(actual_feed[i])
        plt_use_anomalies1.append(use_anomalies1[i])
        plt_use_anomalies2.append(use_anomalies2[i])
        plt_use_anomalies3.append(use_anomalies3[i])
        plt_use_anomalies4.append(use_anomalies4[i])
                
        date.append(date1[i])

#        print "Date: ", date1[i], "  Chemical Anomaly Score:", anomalyScore
#        print "    --> Bath_T:   \t", pre1_1
#        print "        CaO:      \t", pre2_1
#        print "        Fe/SiO2:  \t", pre3_1
#        print "        Cu Slag:  \t", pre4_1
#        print "        Cu Matte: \t", pre5_1
#        print "        Fe:       \t", pre6_1
#        print "        SiO2:     \t", pre7_1

#        if avg_anomaly_likelihood < 0.85:
##            print "        \033[1;42m GOOD CONDITION \033[0m"
#            previous_result = 'G'
##            status_records.append('G')
#            plt_bad_records.append(0)
#            status_table_content[0][0] = date1[i]
#            status_table_content[0][1] = 'GOOD CONDITION'
#            status_table_color[0][1] = '#31de5f'
#            status_table_content[0][2] = avg_anomaly_likelihood
#            status_table_color[0][2] = 'w'
#        elif avg_anomaly_likelihood >=0.85 and avg_anomaly_likelihood < 0.94:
##            print "        \033[1;43m WARNING CAUTION \033[0m"
#            previous_result = 'W'
##            status_records.append('W')
#            plt_bad_records.append(0)
#            status_table_content[0][0] = date1[i]
#            status_table_content[0][1] = 'WARNING CAUTION'
#            status_table_color[0][1] = '#ff9e36'
#            status_table_content[0][2] = avg_anomaly_likelihood
#            status_table_color[0][2] = 'w'
#        else:
#            if previous_result == 'D':
#                contineous_flag = True
#            else:
#                contineous_flag = False
#
#            if table_content[0][0] == ' ' and contineous_flag == False:
#                table_content[0][0] = date1[i]
#                table_content[0][1] = str(avg_anomaly_likelihood) + ' (B)'
#                table_content[0][2] = float(0)
#            elif table_content[1][0] == ' ' and contineous_flag == False:
#                table_content[1][0] = date1[i]
#                table_content[1][1] = str(avg_anomaly_likelihood) + ' (B)'
#                table_content[1][2] = float(0)
#            elif table_content[2][0] == ' ' and contineous_flag == False:
#                table_content[2][0] = date1[i]
#                table_content[2][1] = str(avg_anomaly_likelihood) + ' (B)'
#                table_content[2][2] = float(0)
#            elif table_content[3][0] == ' ' and contineous_flag == False:
#                table_content[3][0] = date1[i]
#                table_content[3][1] = str(avg_anomaly_likelihood) + ' (B)'
#                table_content[3][2] = float(0)         
#            elif table_content[1][0] == ' ' and contineous_flag == True:
#                table_content[0][0] = date1[i]
#                table_content[0][1] = str(avg_anomaly_likelihood) + ' (B)'
#                table_content[0][2] += seconds_difference(date1[i-1], date1[i])
#            elif table_content[2][0] == ' ' and contineous_flag == True:
#                table_content[1][0] = date1[i]
#                table_content[1][1] = str(avg_anomaly_likelihood) + ' (B)'
#                table_content[1][2] += seconds_difference(date1[i-1], date1[i])
#            elif table_content[3][0] == ' ' and contineous_flag == True:
#                table_content[2][0] = date1[i]
#                table_content[2][1] = str(avg_anomaly_likelihood) + ' (B)'
#                table_content[2][2] += seconds_difference(date1[i-1], date1[i])
#            elif table_content[0][0] != ' ' and table_content[1][0] != ' ' and table_content[2][0] != ' ' and table_content[3][0] != ' ' and contineous_flag == False:
#                table_content[0][0] = table_content[1][0]
#                table_content[0][1] = table_content[1][1]
#                table_content[0][2] = table_content[1][2]
#                
#                table_content[1][0] = table_content[2][0]
#                table_content[1][1] = table_content[2][1]
#                table_content[1][2] = table_content[2][2]
#                
#                table_content[2][0] = table_content[3][0]
#                table_content[2][1] = table_content[3][1]
#                table_content[2][2] = table_content[3][2]
#                
#                table_content[3][0] = date1[i]
#                table_content[3][1] = str(avg_anomaly_likelihood) + ' (B)'
#                table_content[3][2] = 0
#            elif table_content[0][0] != ' ' and table_content[1][0] != ' ' and table_content[2][0] != ' ' and table_content[3][0] != ' ' and contineous_flag == True:                
#                table_content[3][0] = date1[i]
#                table_content[3][1] = str(avg_anomaly_likelihood) + ' (B)'
#                table_content[3][2] += seconds_difference(date1[i-1], date1[i])   
##            print "        \033[1;41m DANGEROUS CONDITION \033[0m"
#            previous_result = 'D'
##            status_records.append('D')
#            plt_bad_records.append(1)
#            status_table_content[0][0] = date1[i]
#            status_table_content[0][1] = 'BAD CONDITION'
#            status_table_color[0][1] = '#db4439'
#            status_table_content[0][2] = avg_anomaly_likelihood
#            status_table_color[0][2] = 'w'
##        print "\n"


        if avg_anomaly_likelihood > 0.9 or anomalyLikelihood1 > 0.999 \
            or anomalyLikelihood2 > 0.999 or anomalyLikelihood3 > 0.999 \
            or anomalyLikelihood4 > 0.999 or anomalyLikelihood5 > 0.999 \
            or anomalyLikelihood6 > 0.999 or anomalyLikelihood7 > 0.999 \
            or anomalyLikelihood8 > 0.999 or anomalyLikelihood9 > 0.999 \
            or anomalyLikelihood10 > 0.999 or anomalyLikelihood11 > 0.999 \
            or anomalyLikelihood12 > 0.999:
            
            if previous_result == 'D':
                contineous_flag = True
            else:
                contineous_flag = False

            if table_content[0][0] == ' ' and contineous_flag == False:
                table_content[0][0] = date1[i]
                table_content[0][1] = str(avg_anomaly_likelihood) + ' (B)'
                table_content[0][2] = float(0)
            elif table_content[1][0] == ' ' and contineous_flag == False:
                table_content[1][0] = date1[i]
                table_content[1][1] = str(avg_anomaly_likelihood) + ' (B)'
                table_content[1][2] = float(0)
            elif table_content[2][0] == ' ' and contineous_flag == False:
                table_content[2][0] = date1[i]
                table_content[2][1] = str(avg_anomaly_likelihood) + ' (B)'
                table_content[2][2] = float(0)
            elif table_content[3][0] == ' ' and contineous_flag == False:
                table_content[3][0] = date1[i]
                table_content[3][1] = str(avg_anomaly_likelihood) + ' (B)'
                table_content[3][2] = float(0)         
            elif table_content[1][0] == ' ' and contineous_flag == True:
                table_content[0][0] = date1[i]
                table_content[0][1] = str(avg_anomaly_likelihood) + ' (B)'
                table_content[0][2] += seconds_difference(date1[i-1], date1[i])
            elif table_content[2][0] == ' ' and contineous_flag == True:
                table_content[1][0] = date1[i]
                table_content[1][1] = str(avg_anomaly_likelihood) + ' (B)'
                table_content[1][2] += seconds_difference(date1[i-1], date1[i])
            elif table_content[3][0] == ' ' and contineous_flag == True:
                table_content[2][0] = date1[i]
                table_content[2][1] = str(avg_anomaly_likelihood) + ' (B)'
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
                table_content[3][1] = str(avg_anomaly_likelihood) + ' (B)'
                table_content[3][2] = 0
            elif table_content[0][0] != ' ' and table_content[1][0] != ' ' and table_content[2][0] != ' ' and table_content[3][0] != ' ' and contineous_flag == True:                
                table_content[3][0] = date1[i]
                table_content[3][1] = str(avg_anomaly_likelihood) + ' (B)'
                table_content[3][2] += seconds_difference(date1[i-1], date1[i])   
            previous_result = 'D'
            plt_bad_records.append(1)
            status_table_content[0][0] = date1[i]
            status_table_content[0][1] = 'BAD CONDITION'
            status_table_color[0][1] = '#db4439'
            status_table_content[0][2] = avg_anomaly_likelihood
            status_table_color[0][2] = 'w'        
        
        elif avg_anomaly_likelihood > 0.8 or anomalyLikelihood1 > 0.9 \
            or anomalyLikelihood2 > 0.9 or anomalyLikelihood3 > 0.9 \
            or anomalyLikelihood4 > 0.9 or anomalyLikelihood5 > 0.9 \
            or anomalyLikelihood6 > 0.9 or anomalyLikelihood7 > 0.9 \
            or anomalyLikelihood8 > 0.9 or anomalyLikelihood9 > 0.9 \
            or anomalyLikelihood10 > 0.9 or anomalyLikelihood11 > 0.9 \
            or anomalyLikelihood12 > 0.9:
                
            previous_result = 'W'
            plt_bad_records.append(0)
            status_table_content[0][0] = date1[i]
            status_table_content[0][1] = 'WARNING CAUTION'
            status_table_color[0][1] = '#ff9e36'
            status_table_content[0][2] = avg_anomaly_likelihood
            status_table_color[0][2] = 'w'
            
        else:
            previous_result = 'G'
            plt_bad_records.append(0)
            status_table_content[0][0] = date1[i]
            status_table_content[0][1] = 'GOOD CONDITION'
            status_table_color[0][1] = '#31de5f'
            status_table_content[0][2] = avg_anomaly_likelihood
            status_table_color[0][2] = 'w'            
                
            

        plt_matte_cu, plt_matte_fe, plt_matte_pb, plt_matte_zn, plt_slag_cu, \
        plt_slag_fe, plt_slag_pb, plt_slag_zn, \
        plt_fe_sio2, plt_slag_cao, plt_bath_t, plt_freeboard_t, \
        plt_date = plot_chemical_data(matte_cu, 
                                      matte_fe, 
                                      matte_pb, 
                                      matte_zn, 
                                      slag_cu, 
                                      slag_fe, 
                                      slag_pb,
                                      slag_zn,
                                      fe_sio2,
                                      slag_cao,
                                      bath_t,
                                      freeboard_t,
                                      date)
        
        plt2_lance_air, plt2_lance_oxy, plt2_actual_moisture1, plt2_actual_moisture2, \
        plt2_actual_conc, plt2_actual_feed, plt2_use_anomalies1, plt2_use_anomalies2, \
        plt2_use_anomalies3, plt2_use_anomalies4, plt2_date \
        = plot_input_data(plt_lance_air, 
                          plt_lance_oxy, 
                          plt_actual_moisture1, 
                          plt_actual_moisture2, 
                          plt_actual_conc, 
                          plt_actual_feed,
                          plt_use_anomalies1,
                          plt_use_anomalies2,
                          plt_use_anomalies3,
                          plt_use_anomalies4,
                          date)
        
        plt2_bad_records, plt2_bad_date = plot_anomaly_data(plt_bad_records, date)

        # display the input data
        ax5 = plot.add_subplot(6,5,5)
        ax5.set_xticks([])
        ax5.plot(plt2_date, plt2_lance_air, "y--", linewidth=1)
        ax5.set_title('Lance Air\n')
        
        ax1 = plot.add_subplot(6,5,1)
        ax1.set_xticks([])
        ax1.plot(plt2_date, plt2_actual_moisture1, "y--", linewidth=1)
        ax1.set_title('Actual Moisture 1\n')
        
        ax2 = plot.add_subplot(6,5,2)
        ax2.set_xticks([])
        ax2.plot(plt2_date, plt2_actual_moisture2, "y--", linewidth=1)
        ax2.set_title('Actual Moisture 2\n')
        
        ax10 = plot.add_subplot(6,5,10)
        ax10.set_xticks([])
        ax10.plot(plt2_date, plt2_lance_oxy, "y--", linewidth=1)
        ax10.set_title('Lance Oxygen\n')
        
        ax3 = plot.add_subplot(6,5,3)
        ax3.set_xticks([])
        ax3.plot(plt2_date, plt2_actual_conc, "y--", linewidth=1)
        ax3.set_title('Actual Conc\n')
        
        ax4 = plot.add_subplot(6,5,4)
        ax4.set_xticks([])
        ax4.plot(plt2_date, plt2_actual_feed, "y--", linewidth=1)
        ax4.set_title('Actual Feed\n')
        
        ax6 = plot.add_subplot(6,5,6)
        ax6.set_xticks([])
        ax6.plot(plt2_date, plt2_use_anomalies1, "g-", linewidth=2)
        ax6.plot(plt2_bad_date, plt2_bad_records, "r-", linewidth=1)
        ax6.set_title('(EVA) Moisture 1 AF\n')
        
        ax7 = plot.add_subplot(6,5,7)
        ax7.set_xticks([])
        ax7.plot(plt2_date, plt2_use_anomalies2, "g-", linewidth=2)
        ax7.plot(plt2_bad_date, plt2_bad_records, "r-", linewidth=1)
        ax7.set_title('(EVA) Moisture 2 AF\n')
        
        ax8 = plot.add_subplot(6,5,8)
        ax8.set_xticks([])
        ax8.plot(plt2_date, plt2_use_anomalies3, "g-", linewidth=2)
        ax8.plot(plt2_bad_date, plt2_bad_records, "r-", linewidth=1)
        ax8.set_title('(EVA) Blend AF\n')
        
        ax9 = plot.add_subplot(6,5,9)
        ax9.set_xticks([])
        ax9.plot(plt2_date, plt2_use_anomalies4, "g-", linewidth=2)
        ax9.plot(plt2_bad_date, plt2_bad_records, "r-", linewidth=1)
        ax9.set_title('(EVA) Feed AF\n')
        
        # Chemical plot
        ax11 = plot.add_subplot(6,5,11)
        ax11.set_xticks([])
        ax11.plot(plt_date, plt_matte_cu, "b--", linewidth=1)
        ax11.set_title('Matte Cu\n')
        
        ax12 = plot.add_subplot(6,5,12)
        ax12.set_xticks([])
        ax12.plot(plt_date, plt_matte_fe, "b--", linewidth=1)
        ax12.set_title('Matte Fe\n')
        
        ax13 = plot.add_subplot(6,5,13)
        ax13.set_xticks([])
        ax13.plot(plt_date, plt_matte_pb, "b--", linewidth=1)
        ax13.set_title('Matte Pb\n')
    
        ax14 = plot.add_subplot(6,5,14)
        ax14.set_xticks([])
        ax14.plot(plt_date, plt_matte_zn, "b--", linewidth=1)
        ax14.set_title('Matte Zn\n')
        
        ax15 = plot.add_subplot(6,5,15)
        ax15.set_xticks([])
        ax15.plot(plt_date, plt_slag_cu, "b--", linewidth=1)
        ax15.set_title('Slag Cu\n')
        
        ax16 = plot.add_subplot(6,5,16)
        ax16.set_xticks([])
        ax16.plot(plt_date, plt_slag_fe, "b--", linewidth=1)
        ax16.set_title('Slag Fe\n')
    
        ax17 = plot.add_subplot(6,5,17)
        ax17.set_xticks([])
        ax17.plot(plt_date, plt_slag_pb, "b--", linewidth=1)
        ax17.set_title('Slag Pb\n')

        ax18 = plot.add_subplot(6,5,18)
        ax18.set_xticks([])
        ax18.plot(plt_date, plt_slag_zn, "b--", linewidth=1)
        ax18.set_title('Slag Zn\n')
        
        ax19 = plot.add_subplot(6,5,19)
        ax19.set_xticks([])
        ax19.plot(plt_date, plt_fe_sio2, "b--", linewidth=1)
        ax19.set_title('Fe/SiO2\n')

        ax20 = plot.add_subplot(6,5,20)
        ax20.set_xticks([])
        ax20.plot(plt_date, plt_slag_cao, "b--", linewidth=1)
        ax20.set_title('Slag CaO\n')
        
        ax21 = plot.add_subplot(6,5,21)
        ax21.set_xticks([])
        ax21.plot(plt_date, plt_bath_t, "b--", linewidth=1)
        ax21.set_title('Bath Temperature\n')

        ax22 = plot.add_subplot(6,5,22)
        ax22.set_xticks([])
        ax22.plot(plt_date, plt_freeboard_t, "b--", linewidth=1)
        ax22.set_title('Freeboard Temperature\n')
        
        # table has been defined here
        ax26 = plot.add_subplot(6,5,26)
        table = ax26.table(
                cellText = table_content,
                cellLoc = 'center',
                colLabels = ['Log date', 'Anomaly Likelihood', 'Duration (seconds)'],
                bbox=[0, -0.5, 5, 1.6]
                )
        table.scale(6, 6)
        ax26.axis("off")
        
        for key, cell in table.get_celld().items():
            cell.set_linewidth(0.5)
            
        # status showing table has been defined here
        ax27 = plot.add_subplot(6,5,29)
        table = ax27.table(
                cellText = status_table_content,
                cellColours = status_table_color,
                cellLoc = 'center',
                colLabels = ['Current date', 'Predicted Status', 'Anomaly Likelihood'],
                bbox=[0, -0.3, 3.5, 1.4]
                )
        table.scale(5.5, 5.5)
        ax27.axis("off")
        
        for key, cell in table.get_celld().items():
            cell.set_linewidth(0.5)
            
        # print real-time evaluation results
#        u1_top_1, u1_top_2, u0_top_1, u0_top_2 = evaluation(plt_use_anomalies, status_records)
#        print "anomalyLikelihood: ", anomalyLikelihood
#        print "When < Use nominals = 1 >, top-1: ", u1_top_1, " ; top-2: ", u1_top_2
#        print "When < Use nominals = 0 >, top-1: ", u0_top_1, " ; top-2: ", u0_top_2
#        print "\n"
        
        # print real-time evaluation results
        print "anomalyLikelihood1 :", anomalyLikelihood1
        print "anomalyLikelihood2 :", anomalyLikelihood2
        print "anomalyLikelihood3 :", anomalyLikelihood3
        print "anomalyLikelihood4 :", anomalyLikelihood4
        print "anomalyLikelihood5 :", anomalyLikelihood5
        print "anomalyLikelihood6 :", anomalyLikelihood6
        print "anomalyLikelihood7 :", anomalyLikelihood7
        print "anomalyLikelihood8 :", anomalyLikelihood8
        print "anomalyLikelihood9 :", anomalyLikelihood9
        print "anomalyLikelihood10 :", anomalyLikelihood10
        print "anomalyLikelihood11 :", anomalyLikelihood11
        print "anomalyLikelihood12 :", anomalyLikelihood12
        print "\n"

        
        plot.show()
        plt.pause(1e-17)
        
        time.sleep(0.01)
        plot.clf()


if __name__ == "__main__":
    
    # Simulation data    
    output_data = '/media/tpc2/DATA/chemical_data/2nd round/output_file_2.csv'
    input_data = '/media/tpc2/DATA/chemical_data/2nd round/input_file_2.csv'
    
    # Global parameters here
    _VERBOSITY = 0
    _NUM_RECORDS = 5914 - 3
    _TIMEOFDAY = (21, 8)
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
    # The encoder fields for variables that used for detection
    scalarEncoder1Args = {
      "w": 21,
      "minval": 61 - 1.5,
      "maxval": 61 + 1.5,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "Matte Cu",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }
    
    dateEncoder1Args = {
      "season": 0,
      "dayOfWeek": 0,
      "weekend": 0,
      "holiday": 0,
      "timeOfDay": _TIMEOFDAY,
      "customDays": 0,
      "name": "Time",
      "forced": False
    }
    
    MatteCu_recordParams = {
      "inputFilePath": output_data,
      "scalarEncoder1Args": scalarEncoder1Args,
      "dateEncoderArgs": dateEncoder1Args,
    }
        
    scalarEncoder2Args = {
      "w": 21,
      "minval": 10.45 - 0.3,
      "maxval": 10.45 + 0.8,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "Matte Fe",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }
    
    dateEncoder2Args = {
      "season": 0,
      "dayOfWeek": 0,
      "weekend": 0,
      "holiday": 0,
      "timeOfDay": _TIMEOFDAY,
      "customDays": 0,
      "name": "Time",
      "forced": False
    }
    
    MatteFe_recordParams = {
      "inputFilePath": output_data,
      "scalarEncoder1Args": scalarEncoder2Args,
      "dateEncoderArgs": dateEncoder2Args,
    }
    
    scalarEncoder3Args = {
      "w": 21,
      "minval": 0.6 - 0.1,
      "maxval": 0.6 + 0.1,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "Matte Pb",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }
    
    dateEncoder3Args = {
      "season": 0,
      "dayOfWeek": 0,
      "weekend": 0,
      "holiday": 0,
      "timeOfDay": _TIMEOFDAY,
      "customDays": 0,
      "name": "Time",
      "forced": False
    }
    
    MattePb_recordParams = {
      "inputFilePath": output_data,
      "scalarEncoder1Args": scalarEncoder3Args,
      "dateEncoderArgs": dateEncoder3Args,
    }

    scalarEncoder4Args = {
      "w": 21,
      "minval": 0.82 - 0.08,
      "maxval": 0.82 + 0.08,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "Matte Zn",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }
    
    dateEncoder4Args = {
      "season": 0,
      "dayOfWeek": 0,
      "weekend": 0,
      "holiday": 0,
      "timeOfDay": _TIMEOFDAY,
      "customDays": 0,
      "name": "Time",
      "forced": False
    }
    
    MatteZn_recordParams = {
      "inputFilePath": output_data,
      "scalarEncoder1Args": scalarEncoder4Args,
      "dateEncoderArgs": dateEncoder4Args,
    }
    
    scalarEncoder5Args = {
      "w": 21,
      "minval": 0.129 - 0.01,
      "maxval": 0.129 + 0.01,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "Slag Cu",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }
    
    dateEncoder5Args = {
      "season": 0,
      "dayOfWeek": 0,
      "weekend": 0,
      "holiday": 0,
      "timeOfDay": _TIMEOFDAY,
      "customDays": 0,
      "name": "Time",
      "forced": False
    }
    
    SlagCu_recordParams = {
      "inputFilePath": output_data,
      "scalarEncoder1Args": scalarEncoder5Args,
      "dateEncoderArgs": dateEncoder5Args,
    }

    scalarEncoder6Args = {
      "w": 21,
      "minval": 37.95 - 0.1,
      "maxval": 37.95 + 0.1,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "Slag Fe",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }

    dateEncoder6Args = {
      "season": 0,
      "dayOfWeek": 0,
      "weekend": 0,
      "holiday": 0,
      "timeOfDay": _TIMEOFDAY,
      "customDays": 0,
      "name": "Time",
      "forced": False
    }
    
    SlagFe_recordParams = {
      "inputFilePath": output_data,
      "scalarEncoder1Args": scalarEncoder6Args,
      "dateEncoderArgs": dateEncoder6Args,
    }
    
    scalarEncoder7Args = {
      "w": 21,
      "minval": 0.35 - 0.08,
      "maxval": 0.35 + 0.08,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "Slag Pb",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }

    dateEncoder7Args = {
      "season": 0,
      "dayOfWeek": 0,
      "weekend": 0,
      "holiday": 0,
      "timeOfDay": _TIMEOFDAY,
      "customDays": 0,
      "name": "Time",
      "forced": False
    }
    
    SlagPb_recordParams = {
      "inputFilePath": output_data,
      "scalarEncoder1Args": scalarEncoder7Args,
      "dateEncoderArgs": dateEncoder7Args,
    }
    
    scalarEncoder8Args = {
      "w": 21,
      "minval": 2.04 - 0.05,
      "maxval": 2.04 + 0.05,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "Slag Zn",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }

    dateEncoder8Args = {
      "season": 0,
      "dayOfWeek": 0,
      "weekend": 0,
      "holiday": 0,
      "timeOfDay": _TIMEOFDAY,
      "customDays": 0,
      "name": "Time",
      "forced": False
    }
    
    SlagZn_recordParams = {
      "inputFilePath": output_data,
      "scalarEncoder1Args": scalarEncoder8Args,
      "dateEncoderArgs": dateEncoder8Args,
    }
    
    scalarEncoder9Args = {
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

    dateEncoder9Args = {
      "season": 0,
      "dayOfWeek": 0,
      "weekend": 0,
      "holiday": 0,
      "timeOfDay": _TIMEOFDAY,
      "customDays": 0,
      "name": "Time",
      "forced": False
    }
    
    FeSiO2_recordParams = {
      "inputFilePath": output_data,
      "scalarEncoder1Args": scalarEncoder9Args,
      "dateEncoderArgs": dateEncoder9Args,
    }
    
    scalarEncoder10Args = {
      "w": 21,
      "minval": 5.0 - 0.1,
      "maxval": 5.0 + 0.1,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "Slag CaO",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }

    dateEncoder10Args = {
      "season": 0,
      "dayOfWeek": 0,
      "weekend": 0,
      "holiday": 0,
      "timeOfDay": _TIMEOFDAY,
      "customDays": 0,
      "name": "Time",
      "forced": False
    }
    
    SlagCaO_recordParams = {
      "inputFilePath": output_data,
      "scalarEncoder1Args": scalarEncoder10Args,
      "dateEncoderArgs": dateEncoder10Args,
    }
    
    scalarEncoder11Args = {
      "w": 21,
      "minval": 1200 - 20,
      "maxval": 1200 + 20,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "Bath T",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }

    dateEncoder11Args = {
      "season": 0,
      "dayOfWeek": 0,
      "weekend": 0,
      "holiday": 0,
      "timeOfDay": _TIMEOFDAY,
      "customDays": 0,
      "name": "Time",
      "forced": False
    }
    
    BathT_recordParams = {
      "inputFilePath": output_data,
      "scalarEncoder1Args": scalarEncoder11Args,
      "dateEncoderArgs": dateEncoder11Args,
    }
    
    scalarEncoder12Args = {
      "w": 21,
      "minval": 1060 - 20,
      "maxval": 1060 + 20,
      "periodic": False,
      "n": 50,
      "radius": 0,
      "resolution": 0,
      "name": "Freeboard T",
      "verbosity": 0,
      "clipInput": True,
      "forced": False,
    }
        
    dateEncoder12Args = {
      "season": 0,
      "dayOfWeek": 0,
      "weekend": 0,
      "holiday": 0,
      "timeOfDay": _TIMEOFDAY,
      "customDays": 0,
      "name": "Time",
      "forced": False
    }

    FreeboardT_recordParams = {
      "inputFilePath": output_data,
      "scalarEncoder1Args": scalarEncoder12Args,
      "dateEncoderArgs": dateEncoder12Args,
    }
    
    #--------------------------------------------------------------------------
    #
    #
    # Generate networks and run them
    MatteCu_network = createTemporalAnomaly(MatteCu_recordParams,
                                            spatialParams=_SP_PARAMS,
                                            temporalParams=_TM_PARAMS,
                                            verbosity=_VERBOSITY)

    MatteFe_network = createTemporalAnomaly(MatteFe_recordParams,
                                            spatialParams=_SP_PARAMS,
                                            temporalParams=_TM_PARAMS,
                                            verbosity=_VERBOSITY)

    MattePb_network = createTemporalAnomaly(MattePb_recordParams,
                                            spatialParams=_SP_PARAMS,
                                            temporalParams=_TM_PARAMS,
                                            verbosity=_VERBOSITY)
    
    MatteZn_network = createTemporalAnomaly(MatteZn_recordParams,
                                            spatialParams=_SP_PARAMS,
                                            temporalParams=_TM_PARAMS,
                                            verbosity=_VERBOSITY)
    
    SlagCu_network = createTemporalAnomaly(SlagCu_recordParams,
                                            spatialParams=_SP_PARAMS,
                                            temporalParams=_TM_PARAMS,
                                            verbosity=_VERBOSITY)
    
    SlagFe_network = createTemporalAnomaly(SlagFe_recordParams,
                                            spatialParams=_SP_PARAMS,
                                            temporalParams=_TM_PARAMS,
                                            verbosity=_VERBOSITY)
    
    SlagPb_network = createTemporalAnomaly(SlagPb_recordParams,
                                            spatialParams=_SP_PARAMS,
                                            temporalParams=_TM_PARAMS,
                                            verbosity=_VERBOSITY)
    
    SlagZn_network = createTemporalAnomaly(SlagZn_recordParams,
                                            spatialParams=_SP_PARAMS,
                                            temporalParams=_TM_PARAMS,
                                            verbosity=_VERBOSITY)
    
    FeSiO2_network = createTemporalAnomaly(FeSiO2_recordParams,
                                            spatialParams=_SP_PARAMS,
                                            temporalParams=_TM_PARAMS,
                                            verbosity=_VERBOSITY)
    
    SlagCaO_network = createTemporalAnomaly(SlagCaO_recordParams,
                                            spatialParams=_SP_PARAMS,
                                            temporalParams=_TM_PARAMS,
                                            verbosity=_VERBOSITY)
    
    BathT_network = createTemporalAnomaly(BathT_recordParams,
                                            spatialParams=_SP_PARAMS,
                                            temporalParams=_TM_PARAMS,
                                            verbosity=_VERBOSITY)
    
    FreeboardT_network = createTemporalAnomaly(FreeboardT_recordParams,
                                            spatialParams=_SP_PARAMS,
                                            temporalParams=_TM_PARAMS,
                                            verbosity=_VERBOSITY)
    
    chemical_date = getDate(MatteCu_recordParams, _NUM_RECORDS)
    
    runNetwork(MatteCu_network,
               MatteFe_network,
               MattePb_network,
               MatteZn_network,
               SlagCu_network,
               SlagFe_network,
               SlagPb_network,
               SlagZn_network,
               FeSiO2_network,
               SlagCaO_network,
               BathT_network,
               FreeboardT_network,
               chemical_date, 
               input_data)
