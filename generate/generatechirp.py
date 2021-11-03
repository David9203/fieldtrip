#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  2 21:14:59 2021

@author: nesdav
"""
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  2 21:02:26 2021

@author: nesdav
"""
import numpy as np
from scipy.signal import chirp
from scipy.io.wavfile import write

interval_length = 10 # in seconds
fs = 16000 # sampling of your signal
f0 = 100   # frequency 1
f1 = 7000   # frequency 2

t = np.linspace(0, interval_length, int(fs * interval_length))
w = chirp(t, f0=f0, f1=f1, t1=interval_length, method='linear') # check also other methods
write('test.wav', fs, w)