#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 29 11:26:57 2020

@author: simona
"""

from modules import autocorr_analysis as aa
import numpy as np
import matplotlib.pyplot as plt

from configuration import Configuration
C = Configuration()
problem_name = C.problem_name
#problem_name =  "my_prob01"

S = aa.Samples()
#m = int(1e5)
#length = [10*m, 6*m, 8*m, 10*m, 6*m]

#no_parameters = 3
#S.generate_samples_rand(no_parameters, length)
#length_disp = [100] * no_parameters

#S.generate_samples_celerite(length, [-6.0, -2.0, -2.0], [-6.0, -2.0, -1.0])
##S.generate_samples_celerite(length, [-6.0, -2.0], [-6.0, -2.0])
#length_disp = list(np.multiply(S.autocorr_time_true,5))
#length_disp = list(int(i) for i in length_disp)

S.load_MH('saved_samples/' + problem_name)
S.calculate_properties()
length_disp = [1000] * S.no_parameters

S.calculate_properties()
S.print_properties()
S.calculate_autocorr_function()
S.plot_segment(length_disp)
S.plot_hist()
S.calculate_autocorr_time()
S.calculate_autocorr_function_mean()
S.plot_autocorr_function(length_disp,plot_mean=True)
S.calculate_autocorr_time_mean()
print(S.autocorr_time)
print(S.autocorr_time_mean)
print(S.autocorr_time_mean_beta)

from modules import FEM_wrapper
G = FEM_wrapper.FEM(no_parameters = S.no_parameters, no_observations = 6, n = 50)
G.pass_parameters(S.mean[3])
print("observation:",G.get_solution())

from modules import grf_eigenfunctions as grf
grf_instance = grf.GRF('modules/unit50.pckl', truncate=S.no_parameters)
eta = S.mean[2]
print("mean:",eta)
z = grf_instance.realization_grid_new(eta,np.linspace(0,1,50),np.linspace(0,1,50))
plt.show()
plt.imshow(z)
plt.show()

# generate material shample and calculate observation:
#no_parame = 5
#grf_instance = grf.GRF('modules/unit50.pckl', truncate=no_parame)
#eta = np.random.randn(no_parame)*0.1
#z = grf_instance.realization_grid_new(eta,np.linspace(0,1,50),np.linspace(0,1,50))
#plt.imshow(z)
#plt.show()
#G = FEM_wrapper.FEM(no_parameters = no_parame, no_observations = 6, n = 50)
#G.pass_parameters(eta)
#print("observation:",G.get_solution())

#error for higher max_samples:
#  File "/home/ber0061/Repositories_dom0015/MCMC-Bayes-python/modules/classes_communication.py", line 162, in receive_update_if_ready
#    r = self.request_recv.wait()
#  File "mpi4py/MPI/Request.pyx", line 235, in mpi4py.MPI.Request.wait
#  File "mpi4py/MPI/msgpickle.pxi", line 411, in mpi4py.MPI.PyMPI_wait
#mpi4py.MPI.Exception: MPI_ERR_TRUNCATE: message truncated
#double free or corruption (!prev)
