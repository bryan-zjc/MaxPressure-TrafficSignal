# -*- coding: utf-8 -*-
"""
Created on Tue Mar  1 20:27:36 2022

@author: Administrator
"""
from __future__ import absolute_import
from __future__ import print_function

import os
import sys  # 导入sys模块
#sys.setrecursionlimit(10**5)  # 将默认的递归深度修改为3000
import numpy as np
import random
import pandas as pd
from numpy import nan
import copy



incoming_link = ['1','-2','3','-4']
outcoming_link = ['-1','2','-3','4']
demand_per_od = 300

#RV渗透率
p = 0.2


#生成trip文件，需要再利用cmd命令转化为rou文件
def generate_tripfile(incoming_link,outcoming_link,demand_per_od):
    random.seed(37)  # make tests reproducible
    # demand per second from different directions    
    
    #修改换道属性在vType里面
    for s in range(1):
        filename=('trip.trip.xml')
        with open(filename, "w") as routes:
            print("""<routes>
        <vType id="NV" accel="3" decel="5" tau="1.0" speedFactor="1.0" speedDev="0.0" sigma="0.5" length="5" minGap="2" maxSpeed="60" guiShape="passenger" color="0,1,0"/>
        <vType id="RV" accel="3" decel="5" tau="1.0" speedFactor="1.0" speedDev="0.0" sigma="0.5" length="5" minGap="2" maxSpeed="60" guiShape="passenger" color="1,0,0"/>
            """, file=routes)
            
            #NV为绿色，RV为红色
            
            number = 0
            for m in range(len(incoming_link)):
                for n in range(len(outcoming_link)):
                    if m!=n:
                        from_link = incoming_link[m]
                        to_link = outcoming_link[n]
                        nv_demand = demand_per_od*(1-p)
                        rv_demand = demand_per_od*p
                        print('''<flow id="OD%i_NV" begin="0" end= "3600" vehsPerHour="%s" type='NV' from="%s" to="%s"/>''' % (number, nv_demand,from_link, to_link), file=routes)
                        print('''<flow id="OD%i_RV" begin="0" end= "3600" vehsPerHour="%s" type='RV' from="%s" to="%s"/>''' % (number, rv_demand,from_link, to_link), file=routes)
                        number += 1

            print("</routes>", file=routes)


generate_tripfile(incoming_link,outcoming_link,demand_per_od)



#duarouter --route-files=trip.trip.xml --net-file=1x1.net.xml --output-file=Demand_20.rou.xml --randomize-flows true --departspeed 10 --weights.random-factor 1.5 --seed 30



