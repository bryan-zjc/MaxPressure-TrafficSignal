import os
import sys
import configparser
from sumolib import checkBinary
from collections import defaultdict
import numpy as np
import torch
import xml.etree.ElementTree as ET
import traci

def import_train_configuration(config_file):
    """
    Read the config file regarding the training and import its content
    """
    content = configparser.ConfigParser()
    content.read(config_file)
    config = {}
    config['gui'] = content['simulation'].getboolean('gui')
    config['total_episodes'] = content['simulation'].getint('total_episodes')
    config['max_steps'] = content['simulation'].getint('max_steps')
    config['n_cars_generated'] = content['simulation'].getint('n_cars_generated')
    # config['green_duration'] = content['simulation'].getint('green_duration')
    config['green_duration_min'] = content['simulation'].getint('green_duration_min')
    config['green_duration_max'] = content['simulation'].getint('green_duration_max')
    config['green_extend'] = content['simulation'].getint('green_extend')
    config['yellow_duration'] = content['simulation'].getint('yellow_duration')
    config['num_layers'] = content['model'].getint('num_layers')
    config['width_layers'] = content['model'].getint('width_layers')
    config['batch_size'] = content['model'].getint('batch_size')
    config['learning_rate'] = content['model'].getfloat('learning_rate')
    config['training_epochs'] = content['model'].getint('training_epochs')
    config['memory_size_min'] = content['memory'].getint('memory_size_min')
    config['memory_size_max'] = content['memory'].getint('memory_size_max')
    config['num_states'] = content['agent'].getint('num_states')
    config['num_actions'] = content['agent'].getint('num_actions')
    config['gamma'] = content['agent'].getfloat('gamma')
    config['models_path_name'] = content['dir']['models_path_name']
    config['sumocfg_file_name'] = content['dir']['sumocfg_file_name']
    return config


def import_test_configuration(config_file):
    """
    Read the config file regarding the testing and import its content
    """
    content = configparser.ConfigParser()
    content.read(config_file)
    config = {}
    config['gui'] = content['simulation'].getboolean('gui')
    config['max_steps'] = content['simulation'].getint('max_steps')
    config['n_cars_generated'] = content['simulation'].getint('n_cars_generated')
    config['episode_seed'] = content['simulation'].getint('episode_seed')
    # config['green_duration'] = content['simulation'].getint('green_duration')
    config['green_duration_min'] = content['simulation'].getint('green_duration_min')
    config['green_duration_max'] = content['simulation'].getint('green_duration_max')
    config['green_extend'] = content['simulation'].getint('green_extend')
    config['yellow_duration'] = content['simulation'].getint('yellow_duration')
    config['num_states'] = content['agent'].getint('num_states')
    config['num_actions'] = content['agent'].getint('num_actions')
    config['sumocfg_file_name'] = content['dir']['sumocfg_file_name']
    config['models_path_name'] = content['dir']['models_path_name']
    config['model_to_test'] = content['dir'].getint('model_to_test')
    config['num_layers'] = content['model'].getint('num_layers')
    config['width_layers'] = content['model'].getint('width_layers')
    return config


def set_sumo(gui, sumocfg_file_name, max_steps):
    """
    Configure various parameters of SUMO
    """
    # sumo things - we need to import python modules from the $SUMO_HOME/tools directory
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")

    # setting the cmd mode or the visual mode
    if gui == False:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')
 
    # setting the cmd command to run sumo at simulation time
    # sumo_cmd = [sumoBinary, "-c", sumocfg_file_name, "--no-step-log", "true", "--waiting-time-memory", str(max_steps), "--step-length", str(0.5)]
    # sumo_cmd = [sumoBinary, "-c", sumocfg_file_name, "--no-step-log", "true", "--waiting-time-memory", str(max_steps),'--start','--quit-on-end']
    sumo_cmd = [sumoBinary, "-c", sumocfg_file_name, "--no-step-log", "true", "--waiting-time-memory", str(max_steps)]
    return sumo_cmd

def set_sumo_test(gui, sumocfg_file_name, max_steps):
    """
    Configure various parameters of SUMO
    """
    # sumo things - we need to import python modules from the $SUMO_HOME/tools directory
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")

    # setting the cmd mode or the visual mode
    if gui == False:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # setting the cmd command to run sumo at simulation time
    sumo_cmd = [sumoBinary, "-c", os.path.join('intersection_test', sumocfg_file_name), "--no-step-log", "true",
                "--waiting-time-memory", str(max_steps)]

    return sumo_cmd


def set_save_path(save_path_name):
    # Ensure the 'save' directory exists
    base_path = os.path.join(os.getcwd(), 'save')
    os.makedirs(base_path, exist_ok=True)

    # List existing model versions within the directory
    dir_content = os.listdir(base_path)
    # if dir_content:
    if any(name.startswith(save_path_name) for name in dir_content):
        # Filter directories that start with save_path_name
        previous_versions = [int(name.rsplit("_", 1)[1]) for name in dir_content if name.startswith(save_path_name) and name.rsplit("_", 1)[1].isdigit()]
        new_version = str(max(previous_versions) + 1)
    else:
        new_version = '1'

    data_path = os.path.join(base_path, f'{save_path_name}_'+new_version, '')
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    return data_path 


def set_test_path(models_path_name, model_n):
    """
    Returns a model path that identifies the model number provided as argument and a newly created 'test' path
    """
    model_folder_path = os.path.join(os.getcwd(), models_path_name, 'model_'+str(model_n), '')

    if os.path.isdir(model_folder_path):    
        plot_path = os.path.join(model_folder_path, 'test', '')
        os.makedirs(os.path.dirname(plot_path), exist_ok=True)
        return model_folder_path, plot_path
    else: 
        sys.exit('The model number specified does not exist in the models folder')


def find_your_path():
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)
    os.chdir(script_dir)
    
    
def get_demand(dt = 600, T = 3, flow_main = [450,600,700], flow_side = [450,600,700]):
    connection_dict = defaultdict(dict)
    connection_dict['top0A0']['straight'] = 'A0bottom0'
    connection_dict['top0A0']['side1'] = 'A0left0'
    connection_dict['top0A0']['side2'] = 'A0right0'
    connection_dict['left0A0']['straight'] = 'A0right0'
    connection_dict['left0A0']['side1'] = 'A0top0'
    connection_dict['left0A0']['side2'] = 'A0bottom0'
    connection_dict['right0A0']['straight'] = 'A0left0'
    connection_dict['right0A0']['side1'] = 'A0bottom0'
    connection_dict['right0A0']['side2'] = 'A0top0'
    connection_dict['bottom0A0']['straight'] = 'A0top0'
    connection_dict['bottom0A0']['side1'] = 'A0right0'
    connection_dict['bottom0A0']['side2'] = 'A0left0'

    max_steps = dt * T
    t_sequence = []
    ratio = []
    for i in range(dt, max_steps+dt, dt):
        t_sequence.append(i)
    for i in range(T):
        ratio.append(min(1.5, 1.2 + i/T, 1.7-0.4*i/T)) # if T=30 then the 1.5 is between 9 and 15
        # ratio.append(1)
    demand = dict()
    
    for i,t in enumerate(t_sequence):
        demand[t] = defaultdict(float)
        demand[t]['top0A0', connection_dict['top0A0']['straight']] = flow_main[i]*ratio[i]
        demand[t]['top0A0', connection_dict['top0A0']['side1']] = 0.1 * flow_main[i]*ratio[i]
        demand[t]['top0A0', connection_dict['top0A0']['side2']] = 0.1 * flow_main[i]*ratio[i]

        demand[t]['bottom0A0', connection_dict['bottom0A0']['straight']] = flow_main[i]*ratio[i]
        demand[t]['bottom0A0', connection_dict['bottom0A0']['side1']] = 0.1 * flow_main[i]*ratio[i]
        demand[t]['bottom0A0', connection_dict['bottom0A0']['side2']] = 0.1 * flow_main[i]*ratio[i]

        demand[t]['left0A0', connection_dict['left0A0']['straight']] = flow_side[i]*ratio[i]
        demand[t]['left0A0', connection_dict['left0A0']['side1']] = 0.1 * flow_side[i]*ratio[i]
        demand[t]['left0A0', connection_dict['left0A0']['side2']] = 0.1 * flow_side[i]*ratio[i]

        demand[t]['right0A0', connection_dict['right0A0']['straight']] = flow_side[i]*ratio[i]
        demand[t]['right0A0', connection_dict['right0A0']['side1']] = 0.1 * flow_side[i]*ratio[i]
        demand[t]['right0A0', connection_dict['right0A0']['side2']] = 0.1 * flow_side[i]*ratio[i]
    
    return demand, t_sequence

def get_t_sequence(dt = 600, T = 3):
    max_steps = dt * T
    t_sequence = []
    for i in range(dt, max_steps+dt, dt):
        t_sequence.append(i)
    return t_sequence



class OUNoise:
    def __init__(self, action_size, mu=0.0, theta=0.15, sigma=0.2):
        # Initialize parameters and noise process.
        self.action_size = action_size
        self.mu = mu
        self.theta = theta
        self.sigma = sigma
        self.state = np.ones(self.action_size) * self.mu
        self.reset()

    def sample(self):
        # Update internal state and return it as a noise sample.
        x = self.state
        dx = self.theta * (self.mu - x) + self.sigma * np.random.randn(len(x))
        self.state = x + dx
        return self.state

    def reset(self):
        # Reset the internal state (= noise) to mean (mu).
        self.state = np.ones(self.action_size) * self.mu


class GaussianNoise:
    def __init__(self, action_size, mean=0.0, std_dev=0.2):
        self.action_size = action_size
        self.mean = mean
        self.std_dev = std_dev

    def sample(self):
        return np.random.normal(self.mean, self.std_dev, self.action_size)


def extract_trafficlight_ids(net_file):
    # 解析 .net.xml 文件
    tree = ET.parse(net_file)
    root = tree.getroot()

    # 创建一个列表存储所有交通灯控制的交叉口ID
    trafficlight_ids = []

    # 遍历所有的 junction 元素
    for junction in root.findall('junction'):
        # 检查 junction 是否有交通信号灯控制
        if junction.attrib.get('type') == 'traffic_light':
            trafficlight_id = junction.attrib['id']
            trafficlight_ids.append(trafficlight_id)

    return trafficlight_ids


