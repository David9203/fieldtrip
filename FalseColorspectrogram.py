#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 31 15:33:53 2021

@author: nesdav
"""
import numpy as np
import matplotlib.pyplot as plt
from maad import sound, features
from maad.util import power2dB, plot2d
from skimage import transform
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import NMF

%cd /Users/nesdav/Documents/Salida de campo

#spectrograma 

s, fs = sound.load('grabacion10cm.wav')
Sxx, tn, fn, ext = sound.spectrogram(s, fs, nperseg=1024, noverlap=512)

Sxx_db = power2dB(Sxx, db_range=70)
Sxx_db = transform.rescale(Sxx_db, 0.5, anti_aliasing=True, multichannel=False)  # rescale for faster computation
plot2d(Sxx_db, figsize=(4,10), extent=ext)




shape_im, params = features.shape_features_raw(Sxx_db, resolution='low')

# Format the output as an array for decomposition
X = np.array(shape_im).reshape([len(shape_im), Sxx_db.size]).transpose()

# Decompose signal using non-negative matrix factorization
Y = NMF(n_components=3, init='random', random_state=0).fit_transform(X)



Y = MinMaxScaler(feature_range=(0,1)).fit_transform(Y)
intensity = 1 - (Sxx_db - Sxx_db.min()) / (Sxx_db.max() - Sxx_db.min())
plt_data = Y.reshape([Sxx_db.shape[0], Sxx_db.shape[1], 3])
plt_data = np.dstack((plt_data, intensity))


fig, axes = plt.subplots(3,1, figsize=(10,8))
for idx, ax in enumerate(axes):
    ax.imshow(plt_data[:,:,idx], origin='lower', aspect='auto',
              interpolation='bilinear')
    ax.set_axis_off()
    ax.set_title('Basis ' + str(idx+1))
    
    
    #The first basis spectrogram shows fine and rapid modulations of the signal. Both signals have these features and hence both are delineated in this basis. The second basis highlights the short calls on the background, and the third component highlights the longer vocalizations of the spinetail. The three components can be mixed up to compose a false-colour spectrogram where it can be easily distinguished the different sound sources by color.
    
fig, ax = plt.subplots(2,1, figsize=(10,6))
ax[0].imshow(Sxx_db, origin='lower', aspect='auto', interpolation='bilinear', cmap='gray')
ax[0].set_axis_off()
ax[0].set_title('Spectrogram')
ax[1].imshow(plt_data, origin='lower', aspect='auto', interpolation='bilinear')
ax[1].set_axis_off()
ax[1].set_title('False-color spectrogram')
    