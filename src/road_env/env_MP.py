# -*- coding: utf-8 -*-
"""
Created on Wed Nov 27 13:44:00 2024

@author: Jichen Zhu
"""

import os
import traci
# import wandb
import numpy as np
import pandas as pd
import torch
from collections import defaultdict
import bs4
import random
import copy
import time
import xml.etree.ElementTree as ET

'''
Intersec_Env for rl offline data collection, training, and fine-tuning
'''

class Intersec_Env:
    def __init__(self, rou_file, net_file, num_agent, sumo_cmd, max_steps, seed):
        # sumo config
        # self.MP_PR = MP_PR
        self._max_steps = max_steps
        self._sumo_cmd = sumo_cmd
        # self.t_sequence = t_sequence
        # self._generator = generator

        # signal control parameters config
        self._yellow = 3
        self._green_min = 10
        self._green_max = 40
        
        # agent config
        self.num_agent = num_agent

        # self.control_input = [0 for _ in range(num_agent)]
        self.net_info = None # a dict to store the basic intersection info
        self.net_links = [] # a list to store the edge id in the network (except the out links at the border)
        
        # code config
        # self.wandb = wandb
        
        # random seed
        self.seed = seed
        
        
    def reset(self, MPtripinfo_path):
        # start sumo with traci
        sumo_cmd1 = self._sumo_cmd + ["--tripinfo-output", MPtripinfo_path]
        traci.start(sumo_cmd1) 


        # retrieve the basic inter info
        if not self.net_info:
            tls_ids = traci.trafficlight.getIDList()
            self.net_info = defaultdict(dict)
            for tls_id in tls_ids:
                phase_num = len((traci.trafficlight.getAllProgramLogics(tls_id)[0]).phases)
                lanes_all, lanes_in, lanes_out, lanes_connect, edge_in = self._read_in_and_out(traci.trafficlight.getControlledLinks(tls_id))
                self.net_info[tls_id]['phase_num'] = phase_num
                self.net_info[tls_id]['lanes_all'] = lanes_all
                self.net_info[tls_id]['lanes_in'] = lanes_in
                self.net_info[tls_id]['lanes_out'] = lanes_out
                self.net_info[tls_id]['lanes_connect'] = lanes_connect
                self.net_info[tls_id]['edges_in'] = edge_in
                self.net_info[tls_id]['phase2lane'], self.net_info[tls_id]['lane2phase'] = self._read_phase2lane(tls_id)
                
                self.net_info[tls_id]['lanes_in_no_right'] = []
                self.net_info[tls_id]['lanes_out_no_right'] = []
                for lane in lanes_in:
                    if lane.split('_')[-1] != '0':
                        self.net_info[tls_id]['lanes_in_no_right'].append(lane)
                for lane in lanes_out:
                    if lane.split('_')[-1] != '0':
                        self.net_info[tls_id]['lanes_out_no_right'].append(lane)
                
                self.net_links+=edge_in
        
        # for tls_id in tls_ids:      
        #     print(tls_id)
        #     print(self.net_info[tls_id]['lanes_in_no_right'])
        #     print(self.net_info[tls_id]['lanes_out_no_right'])
        
        # initialize the env
        self.phase_switch_pointer = {} # save the start time of current phase
        self._policy_dict = {} # save the policy info
        
        self.g_max_flag = {}
        
        
        for tls_id in self.net_info.keys():
            traci.trafficlight.setPhase(tls_id, 0)
            self.phase_switch_pointer[tls_id] = 0
            self._policy_dict[tls_id] = []
            self.g_max_flag[tls_id] = 0
        
        self._step = 0

        self._simulate()
        self.decision_step = {}
        
        for tls_id in self.net_info.keys():
            self.decision_step[tls_id] = self._step + self._green_min
        
        total_pressure = {}
        for tls_id in self.net_info.keys():
            total_pressure[tls_id] = self._collect_pressure(tls_id)
        
        return total_pressure, self.net_info


    def close(self):
        traci.close()
        # print("----- connection to sumo closed")


    def step(self, action):
        # self.control_input = action
        # print('self.g_max_flag: ', self.g_max_flag)
        self.control_input = {}
        for tls_id in self.net_info.keys():
            if self.g_max_flag[tls_id] == 1:
                current_phase = traci.trafficlight.getPhase(tls_id)
                self.control_input[tls_id] = ((current_phase + 1) % self.net_info[tls_id]['phase_num'])/2 #人为修改下一次的执行相位，此时相位为黄灯
            else:
                self.control_input[tls_id] = action[tls_id] # apply action to the signal
        # print('control input: ', self.control_input)
        self._update_env() # update the env
        
        total_pressure = {}
        dones = {}
        for tls_id in self.net_info.keys():
            total_pressure[tls_id] = self._collect_pressure(tls_id)
            dones[tls_id]=[self._step >= self._max_steps-15]
            
        return total_pressure, dones, self.next_decision_flag


    # state function candidates
    def _collect_pressure(self, tls_id):
        # do not consider the right turnning movement
        num_info_in = []
        num_info_out = []

        for lane_id in self.net_info[tls_id]['lanes_in_no_right']:
            num_info_in.append(traci.lane.getLastStepHaltingNumber(lane_id))

        for lane_id in self.net_info[tls_id]['lanes_out_no_right']:
            num_info_out.append(traci.lane.getLastStepHaltingNumber(lane_id))
        
        pressure = [0] * 4
        pressure[0] = ((num_info_in[3]-(1/3*num_info_out[0]+1/3*num_info_out[3])) + (num_info_in[7]-(1/3*num_info_out[4]+1/3*num_info_out[7]))) * 1650
        pressure[1] = ((num_info_in[2]-(1/3*num_info_out[2]+1/3*num_info_out[5])) + (num_info_in[6]-(1/3*num_info_out[1]+1/3*num_info_out[6]))) * 1800
        pressure[2] = ((num_info_in[1]-(1/3*num_info_out[1]+1/3*num_info_out[6])) + (num_info_in[5]-(1/3*num_info_out[2]+1/3*num_info_out[5]))) * 1650
        pressure[3] = ((num_info_in[0]-(1/3*num_info_out[0]+1/3*num_info_out[3])) + (num_info_in[4]-(1/3*num_info_out[4]+1/3*num_info_out[7]))) * 1800    

        
        return pressure
    


    # network information reading
    def _read_in_and_out(self, controlledlinks):
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
        lanes_all = (lanes_in + lanes_out)
        # lanes_in is sorted by north-east-south-west
        
        # lanes_in = list(set(lanes_in))
        # lanes_out = list(set(lanes_out))
        # lanes_connect = list(set(lanes_connect))
        # 排序
        # lanes_all.sort()
        # lanes_in.sort()
        # lanes_out.sort()
        # lanes_connect.sort()
        
        for lane in lanes_in:
            edges_in.append(lane[:-2])
        edges_in = list(set(edges_in))
        edges_in.sort()
        
        return tuple(lanes_all), tuple(lanes_in), tuple(lanes_out), tuple(lanes_connect), tuple(edges_in)
    
    
    def _read_phase2lane(self, tls_id):
        phase2lane = {}
        lane2phase = {}
        for phase_idx in range(self.net_info[tls_id]['phase_num']):
            signal_state = traci.trafficlight.getAllProgramLogics(tls_id)[0].phases[phase_idx].state
            # extract the index of G and g in the signal state 并集
            G_idx = [i for i, x in enumerate(signal_state) if x == 'G' or x == 'g']
            list = []
            for idx in G_idx:
                list.append(traci.trafficlight.getControlledLinks(tls_id)[idx][0][0])
                phase2lane[phase_idx] = set(list)
                for edge in list:
                    lane2phase[edge] = phase_idx
        
        return phase2lane, lane2phase
    

    def _update_env(self):
        phases = {}
        switch_flag = {}
        decision_flag = {}
        self.next_decision_flag = {}
        for tls_id in self.net_info.keys():
            phases[tls_id] = traci.trafficlight.getPhase(tls_id)
            # print( traci.simulation.getTime())
            if self.decision_step[tls_id] == traci.simulation.getTime():
                decision_flag[tls_id] = 1
            else:
                decision_flag[tls_id] = 0
            if self.control_input[tls_id]*2 != phases[tls_id]:
                switch_flag[tls_id] = 1
            else:
                switch_flag[tls_id] = 0
        # print('g_max_flag: ', self.g_max_flag)
        # print('current step: ', self._step)
        # print('decision flag:', decision_flag)
        # print('switch flag: ', switch_flag)
        # print('control input: ', self.control_input)
        # print('decision_step: ', self.decision_step)
        # print('phase_switch_pointer: ', self.phase_switch_pointer)
        # print('-------------------------------------------------')
        # set the action to signal switch a large step when the phase is in yellow
        for tls_id in self.net_info.keys():
            if decision_flag[tls_id] == 1:
                if switch_flag[tls_id] == 1:
                    # exectute yellow phase
                    self._set_next_phase(tls_id)
                    self.decision_step[tls_id] = traci.simulation.getTime()+self._yellow+self._green_min
                else:
                    if traci.simulation.getTime() == self.phase_switch_pointer[tls_id] + self._green_max:
                        self.g_max_flag[tls_id] = 1
                        self._set_next_phase(tls_id)
                        self.decision_step[tls_id] = traci.simulation.getTime()+self._yellow+self._green_min
                    else:
                        self._set_control_phase(tls_id)
                        self.decision_step[tls_id] = traci.simulation.getTime()+1
            else: #decision_flag = 0
                if traci.simulation.getTime() == self.phase_switch_pointer[tls_id]+self._yellow and traci.simulation.getTime()>3 and phases[tls_id]%2 == 1:
                    self._set_control_phase(tls_id)
                    self.g_max_flag[tls_id] = 0

        
        self._simulate(steps_todo=1)
        # print('decision_step:',self.decision_step)
        
        for tls_id in self.net_info.keys():
            if self.decision_step[tls_id] == traci.simulation.getTime():
                self.next_decision_flag[tls_id] = 1
            else:
                self.next_decision_flag[tls_id] = 0
        
        
    def _simulate(self, steps_todo=1):
        if (self._step + steps_todo) >= self._max_steps:  # do not do more steps than the maximum allowed number of steps
            steps_todo = self._max_steps - self._step
        while steps_todo > 0:
            phases = {}
            for tls_id in self.net_info.keys():
                phases[tls_id] = traci.trafficlight.getPhase(tls_id)
                # print('phases', phases[tls_id])

            traci.simulationStep()  # simulate 1 step in sumo
            
            # collect data to train reward estimator
            next_phases = {}
            for tls_id in self.net_info.keys():
                next_phases[tls_id] = traci.trafficlight.getPhase(tls_id)
                # print('next_phases', next_phases[tls_id])
                # self._collect_policy_info(tls_id, next_phases[tls_id])  # save the policy info
                # if next_phases[tls_id] != phases[tls_id]:
                #     self.phase_switch_pointer[tls_id] = traci.simulation.getTime() -1
            
            self._step += 1 # update the step counter
            steps_todo -= 1
            
            # self._veh_delay_collect() # collect the delay info of the vehicles
            
        return self._step

    
    def _set_next_phase(self, tls_id):
        current_phase = traci.trafficlight.getPhase(tls_id)
        next_phase = (current_phase + 1) % self.net_info[tls_id]['phase_num']
        # print(f'current phase: {current_phase}, next phase: {next_phase}')
        traci.trafficlight.setPhase(tls_id, next_phase)
        
        self.phase_switch_pointer[tls_id] = traci.simulation.getTime()
        # print('time to change the phase', traci.simulation.getTime())
    
    def _set_control_phase(self,tls_id):
        current_phase = traci.trafficlight.getPhase(tls_id)
        next_phase = self.control_input[tls_id]*2
        traci.trafficlight.setPhase(tls_id, next_phase)
        # print('tls_id: ', tls_id)
        # print('current phase: ', current_phase)
        # print('next phase: ', next_phase)
        if current_phase != next_phase:
            self.phase_switch_pointer[tls_id] = traci.simulation.getTime()
    

    


    

        
    