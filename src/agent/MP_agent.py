# -*- coding: utf-8 -*-
"""
Created on Wed Nov 27 13:44:00 2024

@author: Jichen Zhu
"""

import numpy as np



class MPAgent:
    """Interacts with and learns from the environment."""
    
    def __init__(self,i):
        """Initialize an Agent object.
        
        Params
        ======
            state_size (int): dimension of each state
            action_size (int): dimension of each action
            random_seed (int): random seed
        """
        super(MPAgent, self).__init__()

   
    def get_action(self, pressure):
        """Returns actions for given state as per current policy."""
        # state = torch.from_numpy(state).float().to(self.device)
        action = pressure.index(max(pressure)) 
        return int(action)

 