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
import xml.etree.ElementTree as ET


def extract_boundary_edges(net_file):
    # 解析 .net.xml 文件
    tree = ET.parse(net_file)
    root = tree.getroot()

    # 记录所有 edge 的连接情况
    all_edges = set()
    from_edges = set()  # 有下游的 edge
    to_edges = set()    # 有上游的 edge

    # 遍历所有的 edge
    for edge in root.findall('edge'):
        edge_id = edge.attrib['id']
        # 跳过内部 edge
        if 'function' in edge.attrib and edge.attrib['function'] == 'internal':
            continue
        all_edges.add(edge_id)

    # 遍历所有的 connection，找到所有有连接的 edge
    for connection in root.findall('connection'):
        from_edge = connection.attrib['from']
        to_edge = connection.attrib['to']

        from_edges.add(from_edge)  # 有下游连接的 edge
        to_edges.add(to_edge)      # 有上游连接的 edge

    # 流入的 edge：没有上游连接
    inflow_edges = all_edges - to_edges

    # 流出的 edge：没有下游连接
    outflow_edges = all_edges - from_edges

    return inflow_edges, outflow_edges



# 输入 net.xml 文件路径
net_file = '5x5.net.xml'

# 提取流入和流出的 edge
incoming_link, outcoming_link = extract_boundary_edges(net_file)
incoming_link = list(incoming_link)
outcoming_link = list(outcoming_link)
# 输出结果
print("Inflow edges:")
for edge in incoming_link:
    print(edge)

print("\nOutflow edges:")
for edge in outcoming_link:
    print(edge)


demand_per_od = 800/(len(incoming_link)-1)

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



#duarouter --route-files=trip.trip.xml --net-file=5x5.net.xml --output-file=Demand_20.rou.xml --randomize-flows true --departspeed 10 --weights.random-factor 1.5 --seed 30



