# -*- coding: utf-8 -*-
"""
Created on Fri Mar  7 16:12:25 2025

@author: Jichen Zhu
"""

from MP_control import MP_control
import os



if __name__ == "__main__":
    
    intersection = '5x5'
    
    sumo_visualization = True # True: open sumo gui; False: close sumo gui
    
    max_steps = 1800 # simulation time steps
    
    sumocfg_file = f"./envs/{intersection}/{intersection}.sumocfg"
    net_file = f"./envs/{intersection}/{intersection}.net.xml"
    rou_file = f"./envs/{intersection}/Demand.rou.xml"
    MPtripinfo_path =  f"./tripinfo/{intersection}/tripinfo_MP.xml"
    
    # creat tripinfo dir
    directory = os.path.dirname(MPtripinfo_path)
    os.makedirs(directory, exist_ok=True)
    
    # initial MP control envrionment
    MP_control_env = MP_control(sumocfg_file, net_file, rou_file, MPtripinfo_path, sumo_visualization, max_steps)
    MP_control_env.exe_MP()