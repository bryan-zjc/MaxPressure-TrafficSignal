# -*- coding: utf-8 -*-
"""
Created on Mon Apr 29 10:53:59 2024

@author: Jichen Zhu
"""
import traci
import optparse
from sumolib import checkBinary
import sys
from collections import defaultdict

def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                          default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options

def _read_in_and_out(controlledlinks):
    lanes_all = []
    lanes_in = []
    lanes_out = []
    lanes_connect = []
    edges_in = []
    for sublist in controlledlinks:
        for item in sublist:
            lanes_in.append(item[0])
            lanes_out.append(item[1])
            lanes_connect.append(item[2])
    lanes_all = list(set(lanes_in + lanes_out))
    lanes_in = list(set(lanes_in))
    lanes_out = list(set(lanes_out))
    lanes_connect = list(set(lanes_connect))
    # 排序
    lanes_all.sort()
    lanes_in.sort()
    lanes_out.sort()
    lanes_connect.sort()
    
    for lane in lanes_in:
        edges_in.append(lane[:-2])
    edges_in = list(set(edges_in))
    edges_in.sort()
    
    return tuple(lanes_all), tuple(lanes_in), tuple(lanes_out), tuple(lanes_connect), tuple(edges_in)

def _read_phase2edge(tls_id):
    phase2edge = {}
    edge2phase = {}
    for phase_idx in range(net_info[tls_id]['phase_num']):
        signal_state = traci.trafficlight.getAllProgramLogics(tls_id)[0].phases[phase_idx].state
        # extract the index of G and g in the signal state 并集
        G_idx = [i for i, x in enumerate(signal_state) if x == 'G' or x == 'g']
        list = []
        for idx in G_idx:
            list.append(traci.trafficlight.getControlledLinks(tls_id)[idx][0][0][:-2])
            phase2edge[phase_idx] = set(list)
            for edge in list:
                edge2phase[edge] = phase_idx
    
    return phase2edge, edge2phase

options = get_options()
# this script has been called from the command line. It will start sumo as a
# server, then connect and run
if options.nogui:
    sumoBinary = checkBinary('sumo')
else:
    sumoBinary = checkBinary('sumo-gui')

step = 0

traci.start([sumoBinary, "-c", r"1x1.sumocfg"])

while step < 100:
    traci.simulationStep()
    
    # tls_ids = traci.trafficlight.getIDList()
    # net_info = defaultdict(dict)
    # for tls_id in tls_ids:
    #     phase_num = len((traci.trafficlight.getAllProgramLogics(tls_id)[0]).phases)
    #     lanes_all, lanes_in, lanes_out, lanes_connect, edge_in = _read_in_and_out(traci.trafficlight.getControlledLinks(tls_id))
    #     net_info[tls_id]['phase_num'] = phase_num
    #     net_info[tls_id]['lanes_all'] = lanes_all
    #     net_info[tls_id]['lanes_in'] = lanes_in
    #     net_info[tls_id]['lanes_out'] = lanes_out
    #     net_info[tls_id]['lanes_connect'] = lanes_connect
    #     net_info[tls_id]['edges_in'] = edge_in
    #     net_info[tls_id]['phase2edge'], net_info[tls_id]['edge2phase'] = _read_phase2edge(tls_id)
    
    # print(traci.trafficlight.getNextSwitch('0'))
    # print(traci.simulation.getTime())
    
    vehs = traci.vehicle.getIDList()
    for i in vehs:
        print(i)
        print(traci.vehicle.getLaneID(i))
        print(traci.vehicle.getBestLanes(i)[0][0])
        
        print(traci.vehicle.getLanePosition(i))
        
    
    
    step+=1

traci.close()
