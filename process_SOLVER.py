#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 29 14:55:37 2019

@author: simona
"""

from mpi4py import MPI
comm_world = MPI.COMM_WORLD
rank_world = comm_world.Get_rank()

from configuration import Configuration
C = Configuration()
solver_init = C.full_solver_init
solver_parameters = C.full_solver_parameters
no_solvers = C.no_full_solvers
no_samplers = C.no_samplers
# solver_init ... initializes the object of the (full, surrogate) solver
# solver_parameters ... list of dictionaries with initialization parameters
# no_solvers ... number of solvers to be created
# no_samplers ... number of samplers that request solutions

import numpy as np
from collections import deque

Solvers = []
for i in range(no_solvers):
    Solvers.append(solver_init(**solver_parameters[i]))
samplers_rank = np.arange(no_samplers)
is_active_sampler = np.array([True] * len(samplers_rank))
occupied_by_source = [None] * no_solvers
occupied_by_tag = [None] * no_solvers
is_free = np.array([True] * no_solvers)
no_parameters = Solvers[0].no_parameters
status = MPI.Status()
received_data = np.zeros(no_parameters)
request_queue = deque()
#temp_received_data = [received_data] * no_solvers
while any(is_active_sampler): # while at least 1 sampling algorithm is active
#        print(is_active_sampler,"while at least 1 sampling algorithm is active - rank", rank_world)
    tmp = comm_world.Iprobe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
    # receive one message from one sampler
    if tmp: # if there is an incoming message from any source (not only from sampler)
        rank_source = status.Get_source()
        if rank_source in samplers_rank: # if source is sampler
            tag = status.Get_tag()
            comm_world.Recv(received_data, source=rank_source, tag=tag)
#            print('DEBUG - MANAGER Recv request FROM sampler', rank_source, 'TO:', rank_world, "TAG:", tag)
            if tag == 0: # if received message has tag 0, switch corresponding sampling alg. to inactive
                # assumes that there will be no other incoming message from that source 
                is_active_sampler[samplers_rank == rank_source] = False
            else: # put the request into queue (remember source and tag)
                request_queue.append([rank_source,tag,received_data.copy()])
    for i in range(no_solvers):
        if not is_free[i]: # check all busy solvers if they finished the request
            if Solvers[i].is_solved(): # if so, send solution to the sampling algorithm
                sent_data = Solvers[i].recv_observations()
                is_free[i] = True # mark the solver as free
                for j in range(len(occupied_by_source[i])):
                    comm_world.Send(sent_data[j,:].copy(), dest=occupied_by_source[i][j], tag=occupied_by_tag[i][j])
#                    print('DEBUG - MANAGER Send solution FROM', rank_world, 'TO:', occupied_by_source[i][j], "TAG:", occupied_by_tag[i][j])
        if is_free[i]:
            occupied_by_source[i] = []
            occupied_by_tag[i] = []
            temp_received_data = np.empty((0,no_parameters))
            len_queue = len(request_queue)
            if len_queue>0:
                for j in range(min(len_queue,Solvers[i].max_requests)):
                    rank_source, tag, received_data = request_queue.popleft()
                    temp_received_data = np.vstack((temp_received_data,received_data.copy()))
                    occupied_by_source[i].append(rank_source)
                    occupied_by_tag[i].append(tag)
                Solvers[i].send_parameters(temp_received_data)
                is_free[i] = False
    
for i in range(no_solvers):
    f = getattr(Solvers[i],"terminate",None)
    if callable(f):
        Solvers[i].terminate()
        
comm_world.Barrier()
print("MPI process", rank_world, "(MANAGER) terminated.")