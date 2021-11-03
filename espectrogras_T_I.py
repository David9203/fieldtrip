import os                           
import math                         
import numpy as np                  
from scipy import signal, stats     
from scipy.fft import fftshift    
import matplotlib.pyplot as plt    
import statistics                   
import time                         
import pickle                                 
import json                         
import datetime 
import warnings
warnings.filterwarnings('ignore')
import librosa
import soundfile as sf
from Indices import *
from Filtros import *
import pandas as pd



# ----------------------------------------- Funciones de Procesamiento -------------------------------------------------#
def algoritmo_espectrograma(avance, param, salida, cod_proc, fin_proc, promedioEsp, promedioEspDuracion, todoEsp, ruta_salida_esp):

    '''

    Esta función calcula los espectrogramas de las grabaciones.

    :param avance: recibe un Queue para indicar a la barra de progreso el avance del procedimiento
    :param param: recibe un Queue con parámetros necesarios para el siguiente proceso
    :param salida: recibe un Queue que guarda la salida del proceso
    :param cod_proc: recibe un entero con el código del proceso
    :param fin_proc: recibe un Event que indica si el proceso actual terminó
    :param promedioEsp: recibe un Event que indica si se calcula el espectrograma promedio horas de todos los audios
    :param promedioEspDuracion: recibe un Event que indica si se calcula el espectrograma promedio de la misma duracion de todos los audios
    :param todoEsp: recibe un Event que indica si se calcula el espectrograma de cada audio
    :param ruta_salida_esp: recibe un Event que indica la ruta donde se van a guartas los espectrogramas
    :return: None
    '''

    canal, indices, rec_std, tipo_ventana, tamano_ventana, sobreposicion, nfft, sinfiltro, lpf, bpf, hpf, fcl, fch, fmin, fmax, grabxdia, extension, cod_car = param.get(0)
    param.put((canal, indices, rec_std, tipo_ventana, tamano_ventana, sobreposicion, nfft, sinfiltro, lpf, bpf, hpf, fcl, fch, fmin, fmax, grabxdia, extension, cod_car))
    
    tamano_ventana = 512
    grabaciones = salida.get(0)
    n_grabs = len(grabaciones)
    
    arraymeanspect_aux = np.zeros(shape=(n_grabs,257))
    arraymeanspect_aux_duracion = np.zeros(shape=(n_grabs,257))
    carpeta_salida_esp = ruta_salida_esp.split('/')[-1]
    fecha = str(datetime.date.today())
    ahora = datetime.datetime.now()
    ahora_actual = (str(ahora.time()).split('.')[0]).split(':')
    ahora_actual = ahora_actual[0] + '-' + ahora_actual[1] + '-' + ahora_actual[2]
    milisegundos = str(ahora.time()).split('.')[-1]
    hora_genero_grab = [] 
    horas_grabaciones = []
    N_grab_misma_duracion = 0
    
    
    for i in range(n_grabs):

        try:
            x, Fs = sf.read(grabaciones[i])
        except RuntimeError:
            print('erroren grabacion:  ',i)
            continue

        if len(x.shape) == 1:
            audio = x
        else:
            audio = x[:, canal]

        #Filtrar la señal________________
        if sinfiltro:
            audio=audio
        if lpf:
            audio=filtro_lpf(fch,audio,Fs)
        if hpf:
            audio=filtro_hpf(fcl,audio,Fs)
        if bpf:
            audio=filtro_bpf(fcl,fch,audio,Fs)
        #Fin filtado señal____________________
    
        f, t, s = signal.spectrogram(audio, Fs, window=tipo_ventana,nfft=tamano_ventana, 
                                        mode="magnitude"
                                        )
        nombre_grab_esp = (grabaciones[i].split('/')[-1]).split('.')[0]
        if todoEsp:
            plt.figure(figsize=(15,7))
            ahora = datetime.datetime.now()
            ahora_actual = (str(ahora.time()).split('.')[0]).split(':')
            ahora_actual = ahora_actual[0] + '-' + ahora_actual[1] + '-' + ahora_actual[2]
            milisegundos = str(ahora.time()).split('.')[-1] 
            plt.pcolormesh(t, f, s,shading='auto', cmap="plasma") 
            plt.title(nombre_grab_esp,fontsize=18)
            plt.ylabel('Frequency [Hz]')
            plt.xlabel('tiempo [s]')
            plt.savefig(ruta_salida_esp + '/' + nombre_grab_esp + '_' + fecha + '_' + ahora_actual + '_' + milisegundos + '.png', dpi=300)  
        if promedioEsp:
            hora_genero_grab.append((nombre_grab_esp.split('_')[-1]))
            arraymeanspect_aux[i] = s.mean(axis=1)
        if promedioEspDuracion & (round(max(t))==60):
            arraymeanspect_aux_duracion[i] = s.mean(axis=1)
            N_grab_misma_duracion = N_grab_misma_duracion + 1 
        
        porcentaje = round(100 * (i + 1) / n_grabs, 2)
        print("Corriendo algoritmo espectrograma " + str(porcentaje) + "%")
        avance.put((cod_proc, i + 1))

    if promedioEspDuracion:

        h_igual_duracion=[]
        avance.put((cod_proc, 1))
        print("Generando espectrograma promedio (duracion de la grabación) " + str(10) + "%")
        for j in  range(N_grab_misma_duracion):
            h_igual_duracion.append(np.array(arraymeanspect_aux_duracion[j].tolist()))

        if N_grab_misma_duracion > 0:
            arraymeanspect_duracion = np.zeros(shape=(257,12857))
            espectrogra_igual_duracion = np.mean(h_igual_duracion, axis=0)

            for i in range(len(espectrogra_igual_duracion)):
                arraymeanspect_duracion[i]=espectrogra_igual_duracion[i]

            plt.figure(figsize=(15,7))
            f1=np.linspace(0, 24, num=257)
            t1=np.linspace(0, 60, num=12857)
            avance.put((cod_proc, n_grabs/2))
            print("Generando espectrograma promedio (duracion de la grabación) " + str(50) + "%")
            plt.pcolormesh(t1, f1, arraymeanspect_duracion,shading='auto', cmap="plasma")
            plt.title("Espectrograma promedio duracion",fontsize=18)
            plt.ylabel('Frequency [kHz]')
            plt.xlabel('Tiempo [s]')
            plt.savefig(ruta_salida_esp + '/' + carpeta_salida_esp + '_' + 'Duracion' + '_' + fecha + '_' + ahora_actual + '_' + milisegundos + '.png', dpi=300)
            avance.put((cod_proc, n_grabs))
            print("Generando espectrograma promedio (duracion de la grabación) " + str(100) + "%")

        else:
            avance.put((cod_proc, n_grabs))
            print("Generando espectrograma promedio (duracion de la grabación) " + str(100) + "%")
            print("No se encontraron grabaciones de la misma duracion")


    if promedioEsp:
        listhour=[]
        h=[]
        contador= 0
        numero_gab_misma_hora = 0
        contador_rango = 1

        avance.put((cod_proc, 0))
        listhour=np.array(hora_genero_grab)
        uniquehours=np.unique(listhour)

        arraymeanspect_aux1 = np.zeros(shape=(len(uniquehours),257))
        for ind, i in enumerate(uniquehours):
    
            hlist=[]
            for ind1, j in  enumerate(hora_genero_grab):
                if i==j:
                    hlist.append(np.array(arraymeanspect_aux[ind1].tolist()))
    
            arraymeanspect_aux1[ind]= np.mean(hlist, axis=0)
            horas_grabaciones.append(int((i)[0:2]))



        hora_max=max(horas_grabaciones)
        hora_min=min(horas_grabaciones)

        for rango_horas in range(hora_min,hora_max + 1):
            posicion_horas = (np.where(np.array(horas_grabaciones)==rango_horas))[0]
            long_pocision = len(posicion_horas)
            if long_pocision > numero_gab_misma_hora:
                numero_gab_misma_hora = long_pocision
        
        num_espectros_agenerar = (numero_gab_misma_hora*((hora_max + 1) - hora_min))

        if long_pocision < numero_gab_misma_hora:
            num_espectros_agenerar = num_espectros_agenerar -(numero_gab_misma_hora - long_pocision)

        arraymeanspect = np.zeros(shape=(num_espectros_agenerar,257))
        particiones_misma_hora = 1/numero_gab_misma_hora

        avance.put((cod_proc, 1))
        print("Generando espectrograma promedio (horas de las grabaciones) " + str(10) + "%")
        for rango_horas in range(hora_min,hora_max + 1):
            posicion_horas = (np.where(np.array(horas_grabaciones)==rango_horas))[0]
            h.append(rango_horas)
            if len(posicion_horas) > 0:
                for i in range(len(posicion_horas)):
                    arraymeanspect[contador] = arraymeanspect_aux1[posicion_horas[i]]
                    contador = contador + 1
                contador = contador_rango*numero_gab_misma_hora
            else:
                contador = contador + numero_gab_misma_hora  
            contador_rango = contador_rango + 1

            for i in range(numero_gab_misma_hora):
                if particiones_misma_hora < 1 & (i < (numero_gab_misma_hora-1)):
                    h.append(rango_horas + particiones_misma_hora*(i+1))
        del(h[num_espectros_agenerar:])

        plt.figure(figsize=(15,7))
        f=np.linspace(0, 24, num=257)
        avance.put((cod_proc, n_grabs/2))
        print("Generando espectrograma promedio (horas de las grabaciones) " + str(50) + "%")
        plt.pcolormesh(h, f, arraymeanspect.T,shading='auto', cmap="plasma")
        plt.title("Espectrograma promedio horas",fontsize=18)
        plt.ylabel('Frequency [kHz]')
        plt.xlabel('Hours')
        plt.xlim(hora_min - particiones_misma_hora/2, hora_max + particiones_misma_hora*(long_pocision-1) + particiones_misma_hora/2)
        plt.savefig(ruta_salida_esp + '/' + carpeta_salida_esp +  '_' + 'Horas' + '_'  + fecha + '_' + ahora_actual + '_' + milisegundos + '.png', dpi=300)
        avance.put((cod_proc, n_grabs))
        print("Generando espectrograma promedio (horas de las grabaciones) " + str(100) + "%")

    fin_proc.set()
    avance.put((cod_proc, 0))
