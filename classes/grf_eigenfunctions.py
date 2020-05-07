#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  6 09:19:41 2020

@author: simona
"""

import numpy as np
import scipy.linalg
import scipy.sparse.linalg
import scipy.interpolate
import matplotlib.pyplot as plt
import time

def cov_function(r,sigma,lam):
    return np.power(sigma,2)*np.exp(-r/lam)

def calculate_dist(nx, ny, lx, ly):
    x = np.linspace(0,lx,nx)
    y = np.linspace(0,ly,ny)
    X,Y = np.meshgrid(x,y)
    return np.sqrt(np.power(X,2)+np.power(Y,2))

def calculate_Cov(nx, ny, lx, ly, sigma, lam,show=False):
    distances = calculate_dist(nx, ny, lx, ly)
    cov_dist = cov_function(distances, sigma, lam)
    blocks = list(scipy.linalg.toeplitz(cov_dist[i,:]) for i in range(ny))
    structure = scipy.linalg.toeplitz(range(ny))
    blocks_list = [None] * ny
    for i in range(ny):
        blocks_list[i] = list(blocks[j] for j in structure[i,:])
    Cov = np.block(blocks_list)
    if show:
        plt.imshow(Cov)
        plt.show()
    return Cov

def calculate_Cholesky_factor(Cov):
    t = time.time()
    L = scipy.linalg.cholesky(Cov)
    print('Chol factorization time:',time.time() - t)
    return L

def sample_using_Cholesky(L,seed=None,show=True,nx=None):
    if not seed is None: 
        np.random.seed(seed)
    nxny = L.shape[0]
    grf = np.matmul(np.transpose(L),np.random.randn(nxny))
    if show:
        if nx is None:
            nx = int(np.sqrt(nxny))
            ny = nx
        else:
            ny = int(nxny/nx)
        plt.imshow(grf.reshape((ny,nx)))
        plt.show()
    return grf

def calculate_eig(Cov):
    t = time.time()
    D,V = np.linalg.eigh(Cov)
    print('eigh factorization time:',time.time() - t)
    # sort eigenvalues and eigenvectors
    indices = np.flip(np.argsort(D))
    Dsorted = D[indices]
    Vsorted = V[:,indices]
    return Dsorted,Vsorted
    
def eigenfunctions(V,indices,nx,ny,lx,ly,lam_new=None,lam_orig=None):
    # TO DO: lambda
    if lam_new is None:      
        x = np.linspace(0,lx,nx)
        y = np.linspace(0,ly,ny)
    else:
        coef = lam_orig/lam_new
        x = np.linspace(lx/2*(1-1/coef),lx/2*(1+1/coef),nx) # cut form middle
        y = np.linspace(ly/2*(1-1/coef),ly/2*(1+1/coef),ny) # cut from middle
#        x = np.linspace(0,lx/coef,nx) # cut from (0,0)
#        y = np.linspace(0,ly/coef,ny) # cut from (0,0)
    f = [None] * len(indices)
    for i,index in enumerate(indices):
        f[i] = scipy.interpolate.interp2d(x,y,V[:,index].reshape((ny,nx)),kind='cubic')
    return f

def evaluate_eigenfunctions(f,x,y,show=False,indices=None):
    n = len(f)
    z = list(f[i](x,y) for i in range(n))
    if show:
        plot_multiple_imshow(z,indices)
    return z
    
def evaluate_engenvalues(D,indices,sigma_new=None,sigma_orig=None):
    if sigma_new is None:
        return D[indices]
    else:
        return D[indices]/sigma_orig/sigma_orig*sigma_new*sigma_new

def plot_eigenvectors(V,indices,nx=None):
    # indices ... columns of V to be visualized on the grid
    if nx is None:
        nx = int(np.sqrt(V.shape[0]))
        ny = nx
    else:
        ny = int(V.shape[0]/nx)
    IMG = list(V[:,i].reshape((ny,nx)) for i in indices)
    plot_multiple_imshow(IMG,indices)

def plot_eigenvalues(D,indices):
    plt.plot(D[indices])
    plt.show()
    
def plot_multiple_imshow(IMG,indices):
    if indices is None:
        indices = range(len(IMG))
    fig, axes = plt.subplots(1, len(indices), figsize=(12, 3))
    for i,index in enumerate(indices):
        axes[i].imshow(IMG[i])
        axes[i].set_xlabel("$i={0}$".format(index))
    plt.show()

def save_eig(filename, D, V, Cov, nx, ny, lx, ly, sigma, lam):
    import pickle
    f = open(filename, 'wb')
    pickle.dump([D, V, Cov, nx, ny, lx, ly, sigma, lam],f)
    f.close()

def load_eig(filename):
    import pickle
    f = open(filename,'rb')
    obj = pickle.load(f)
    f.close()
    return obj

def realization(D,V,nx,ny,lx,ly,seed=None,truncate=None,show=False):
    if truncate is None:
        truncate=len(D)
    D = D[:truncate]
    V = V[:,:truncate]
    np.random.seed(seed)
    eta = np.random.randn(truncate)
    M = np.matmul(V,eta*np.sqrt(D)).reshape((ny,nx))
    x = np.linspace(0,lx,nx)
    y = np.linspace(0,ly,ny)
    f = scipy.interpolate.interp2d(x,y,M,kind='cubic')
    if show:
        fig, axes = plt.subplots(1, 2)
        axes[0].imshow(M)
        axes[0].set_xlabel("$seed={0},truncate={1}$".format(seed,truncate))
        x2 = np.linspace(0,lx,2*nx)
        y2 = np.linspace(0,ly,2*ny)
        z = f(x2,y2)
        axes[1].imshow(z)
        axes[1].set_xlabel('smooth')
        plt.show()
    return M,f

def demo_generate_and_save():
    # rectangular domain
    # points are uniformly spaced on a rectangular grid
    nx = 50 # number of grid points in x direction
    ny = 50 # number of grid points in y direction
    lx = 10 # length of the domain in x direction
    ly = 10 # length of the domain in y direction
    sigma = 1 # std
    lam = 1 # autocorrelation length
    Cov = calculate_Cov(nx,ny,lx,ly,sigma,lam,show=False)
    D,V = calculate_eig(Cov)
    filename = 'demo.pckl'
    save_eig(filename,D, V, Cov, nx, ny, lx, ly, sigma, lam)
    indices = [0,1,3,4,5]#,6,8,10,11,12,13,15,17,19]
    plot_eigenvectors(V,indices,nx)

def demo_load_and_show():
    indices = [0,1,3,4,5]#,6,8,10,11,12,13,15,17,19]
    filename='demo.pckl'
    D, V, Cov, nx, ny, lx, ly, sigma, lam = load_eig(filename)
#    plot_eigenvectors(V,indices,nx)
    f = eigenfunctions(V,indices,nx,ny,lx,ly)
    x = np.linspace(0,lx,120)
    y = np.linspace(0,ly,120)
    z = evaluate_eigenfunctions(f,x,y,show=True,indices=indices)
    # correlation length lam higher than original:
    f = eigenfunctions(V,indices,nx,ny,lx,ly,lam_new=2,lam_orig=lam)
    z = evaluate_eigenfunctions(f,x,y,show=True,indices=indices)

demo_generate_and_save()
demo_load_and_show()

filename='demo.pckl'
D, V, Cov, nx, ny, lx, ly, sigma, lam = load_eig(filename)
for i in [10,20,100,1000,None]:
    realization(D,V,nx,ny,lx,ly,2,i,show=True)