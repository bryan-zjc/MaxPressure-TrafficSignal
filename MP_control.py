# -*- coding: utf-8 -*-
"""
Created on Wed Nov 27 14:39:20 2024

@author: Jichen Zhu
"""

import numpy as np
from src.utils import utils
from src.agent.MP_agent import MPAgent 
from src.road_env.env_MP import Intersec_Env




class MP_control:
    def __init__(self, sumocfg_file, net_file, rou_file, MPtripinfo_path,sumo_visualization, steps):
        super(MP_control, self).__init__()
        self.sumo_visualization = sumo_visualization
        self.sumocfg_file, self.net_file, self.rou_file = sumocfg_file, net_file, rou_file
        self.MPtripinfo_path = MPtripinfo_path
        self.steps = steps
        
    def exe_MP(self):
        # random seed (date)
        seed=20250102
        np.random.seed(seed)

        # simulation time
        max_steps = self.steps
        
        
        # multi agents dict
        agent_list = {}
        
        # save setting
        MPtripinfo_path = self.MPtripinfo_path
     
        inters_list = utils.extract_trafficlight_ids(self.net_file)
        num_agents = len(inters_list)
        
      
        # generator_offline_train = TrafficGenerator(net_file_static, trip_file, veh_params, demand, online_train_save_path)
        sumo_cmd_offline_train = utils.set_sumo(self.sumo_visualization, self.sumocfg_file, max_steps)
        
        env_online_train = Intersec_Env(self.rou_file,
                                        self.net_file,
                                        num_agents,
                                        sumo_cmd_offline_train,
                                        max_steps,
                                        seed)
        # train the agent
        for i in inters_list:
            agent_list[str(i)]=MPAgent(i)

        self.runMP(agent_list, env_online_train, inters_list, MPtripinfo_path)



    def runMP(self, agent_list, env, inters_list, MPtripinfo_path = None):
        total_steps = 0
        # Reset the environment
        total_pressure, net_info = env.reset(MPtripinfo_path)
        # print(net_info)
        done = False
        decision_flag = {}
        action={}
        for tls_id in net_info.keys():
            decision_flag[tls_id] = 0
            action[tls_id] = 0
    
        while not done:
            # print('----------------------------------------------------------------')
           
            num_act_agent = 0
            act_agent_ids = []
            for tls_id in net_info.keys():
                if decision_flag[tls_id] == 1:
                    num_act_agent+=1
                    act_agent_ids.append(tls_id)
    
            if num_act_agent > 0:
                for tls_id in act_agent_ids:
                    # print(f'signal {tls_id} take a decision')
                    agent = agent_list[tls_id]
    
                    action[tls_id] = agent.get_action(total_pressure[tls_id])
                    
            
            total_pressure, dones, next_decision_flag = env.step(action)
            
            
            done = []
            for tls_id in inters_list:
                done.append(dones[tls_id][0])
            done = np.any(done)
            
            decision_flag = next_decision_flag
              
        
        total_steps += 1
    
        # kill the sumo process
        env.close()

