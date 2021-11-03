#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 31 16:02:06 2021

@author: nesdav
"""
import numpy as np
import matplotlib.pyplot as plt
import maad as maad
from maad import sound, features
from maad.util import power2dB, plot2d
from skimage import transform
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import NMF

%cd /Users/nesdav/Documents/Salida de campo

#spectrograma 

'''Convert an audio signal amplitude to Volts.

Parameters
wavendarray-like or scalar
wave should already be normalized between -1 to 1 (depending on the number of bits) take the output of the function sound.load of maad module ndarray-like or scalar containing the raw sound waveform

Vadcscalar, optional, default is 2Vpp (=>+/-1V)
Maximal voltage (peak to peak) converted by the analog to digital convertor ADC

Returns
voltndarray-like or scalar
ndarray-like or scalar containing the sound waveform in volt
'''


w, fs = maad.sound.load('grabacion10cm.wav') 
volt=maad.spl.wav2volt(wave=w, Vadc=2)
len(volt)
