#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  2 21:02:26 2021

@author: nesdav
"""
import numpy as np
from scipy.io import wavfile

samplerate = 44100
length = 10
chirplength = 3

f0 = 440
f1 = 880

total=np.zeros(10)
zeros=np.zeros(100)
for i in range(1,20):
    f0 = i*100
    f1 = 100*(i+1)
    signal = np.arange(chirplength*samplerate)/(chirplength*samplerate)
    signal = np.interp(signal, [0, 1], [f0, f1])
    signal = np.append(signal, np.repeat(f1, (length-chirplength)*samplerate))
    signal = np.sin(signal * 2 * np.pi * np.arange(length*samplerate)/samplerate)
    signal = np.float32(signal)
    newsignal=np.concatenate((signal,zeros))
    total=np.concatenate((total,newsignal))

wavfile.write("audio.wav", samplerate, total)