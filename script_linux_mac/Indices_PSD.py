'''

Contiene los pasos del procesamiento para la extracción de características del paisaje acústico. Este módulo es invocado
por GUI_paisaje.py

Modificaciones realizadas noviembre 2020, Se añadieron los indices SC, SB, Tonnets
Modificaciones enero 2021 Se recibe de la interfaz los indices que se deben calcular y a los demas se les pone N/A. se quita función estandarizar y promedio
Modificaciones  marzo 2021, se permite escoger si se calculan todas las grabaciones o solo las no ruidosas, se agregan filtros pasa bajas, pasa altas y pasabanda
Modificaciones octubre 2021, se verifico que la deteccion de lluvia con PSD promedio, sin analisis SNR (Modificacion Bedoya,2017) etiqueta como lluvia grabaciones 
con niveles de lluvia mas altos que  Metodo intensidad del espectrograma promedio. Si se quiere etiquetar grabaciones con niveles de lluvia bajos utilizar el metodo de intensidad.
Modificaciones octubre 2021, Metodo (Bedoya,2017) promedio presenta bajo desempeño para carpetas con grabaciones con mucha lluvia.
'''


import warnings
warnings.filterwarnings('ignore')
import librosa
import soundfile as sf
from Indices import *
from Filtros import *
import pandas as pd


# ----------------------------------------- Funciones de Procesamiento -------------------------------------------------#

def algoritmo_lluvia(avance, param, salida, malas, cod_proc, fin_proc):
    '''

    Esta función filtra las grabaciones con altos niveles de ruido, según la publicación [1]

    Además se genera un umbral automático para el reconocimiento de las grabaciones más ruidosas.

    :param avance: recibe un Queue para indicar a la barra de progreso el avance del procedimiento
    :param param: recibe un Queue con parámetros necesarios para el siguiente proceso
    :param salida: recibe un Queue que guarda la salida del proceso
    :param malas: recibe un Queue que guarda las grabaciones rechazadas durante el procesamiento
    :param cod_proc: recibe un entero con el código del proceso
    :param fin_proc: recibe un Event que indica si el proceso actual terminó
    :return: None
    '''

    # Variables compartidas no se dejan en comentario
    canal, indices, rec_std, tipo_ventana, tamano_ventana, sobreposicion, nfft, sinfiltro, lpf, bpf, hpf, fcl, fch, fmin, fmax, grabxdia, extension, cod_car = param.get(0)
    param.put((canal, indices, rec_std, tipo_ventana, tamano_ventana, sobreposicion, nfft, sinfiltro, lpf, bpf, hpf, fcl, fch, fmin, fmax, grabxdia, extension, cod_car))


    ############################ Metodo aplicativo PSD promedio ###############################
    ############################ Modificacion de Bedoya,2017 (No se incluye SNR) ###############################

    grabaciones = salida.get(0)                      # se obtienen las grabaciones 
    banda_lluvia = (600, 1200)                       # banda de frecuencias
    n_grabs = len(grabaciones)
    PSD_medio = np.zeros((n_grabs,))
    grab_malas_df = pd.DataFrame(columns=["Grabaciones rechazadas", "Motivo"])

    # se procesan todas las grabaciones
    for i in range(n_grabs):
        
        try:
            x, Fs = sf.read(grabaciones[i])                 # se obtiene la informacion de cada una de las grabaciones
        except RuntimeError:
            grab_malas_df.append({"Grabaciones rechazadas":grabaciones[i].split('/')[-1], "Motivo":"Archivo corrupto"},
                                ignore_index=True)
            continue

        # se escoge el canal con que se quiere trabajar la grabacion
        if len(x.shape) == 1:
            audio = x
        else:
            audio = x[:, canal]

        puntos_minuto = Fs * 60   # se obtiene el numero de puntos por minuto de la grabacion
        npuntos = len(audio)
        banda = []

        # se obtiene el el welch por minuto de cada grabacion y luego se concatena de la variable (banda)
        for seg in range(0, npuntos, puntos_minuto):
            f, p = signal.welch(audio[seg:puntos_minuto+seg], Fs, nperseg=tamano_ventana, window=tipo_ventana,
                                nfft=nfft, noverlap=sobreposicion)
            banda.append(p[np.logical_and(f >= banda_lluvia[0], f <= banda_lluvia[1])])     # la informacion obtenida solo se limita al rando de frecuencia banda_lluvia

        try:
            banda = np.concatenate(banda)
        except ValueError:
            grab_malas_df.append({"Grabaciones rechazadas":grabaciones[i].split('/')[-1], "Motivo":"Archivo corrupto"},
                                ignore_index=True)
            continue

        PSD_medio[i] = np.mean(banda)                                       # se guarda la PSD promedio de cada grabacion
        porcentaje = round(100 * (i + 1) / n_grabs, 2)
        print("Corriendo algoritmo de lluvia " + str(porcentaje) + "%")     # se muestra por consola el porcentaje de las grabaciones procesadas
        avance.put((cod_proc, i + 1))

    PSD_medio = np.array(PSD_medio)
    PSD_medio_sin_ceros = PSD_medio[PSD_medio > 0]
    umbral = (np.mean(PSD_medio_sin_ceros) + stats.mstats.gmean(PSD_medio_sin_ceros)) / 2     # se halla el umbral de decision
    cond_buenas = np.logical_and(PSD_medio < umbral, PSD_medio != 0)            
    cond_malas = np.logical_and(PSD_medio >= umbral, PSD_medio != 0)
    grabaciones = np.array(grabaciones)
    if rec_std==1:
        grab_buenas = grabaciones                                                                           # se guardan todas las grabaciones como buenas
    else:
        grab_buenas = grabaciones[cond_buenas]                                                              # se guardan las grabaciones buenas
    grab_malas = np.array([[grab.split('/')[-1] for grab in grabaciones[cond_malas]]]).T                    # se guardan las grabaciones malas
    motivos = np.array([["Ruido Fuerte"]*grab_malas.shape[0]]).T
    # se genera  un df con todas las grabaciones malas
    grab_malas_df=pd.concat([grab_malas_df, pd.DataFrame(np.hstack((grab_malas, motivos)),
                                                         columns=["Grabaciones rechazadas", "Motivo"])],
                            ignore_index=True)
    
    

    ############################ Metodo (Bedoya,2017) promedio ###############################
    ############################ Utiliza PSD promdio y SNR promedio para estimar nivales de lluvia #######################
    '''
    banda_lluvia = (600, 1200)                       # banda de frecuencias
    Tmean = 0.0002
    Tsnr = 3.3
    canal = 1

    grabaciones = salida.get(0)                      # se obtienen las grabaciones 
    uniquehours=np.unique(grabaciones)               # se ordenan las grabaciones
    n_grabs = len(uniquehours)
    PSD_medio = np.zeros((n_grabs,))
    SNR_medio = np.zeros((n_grabs,))
    print(n_grabs)

    grab_malas_df = pd.DataFrame(columns=["Grabaciones rechazadas", "Motivo"])

    # se procesan todas las grabaciones
    for i in range(n_grabs):

        try:
            x, Fs = sf.read(uniquehours[i])             # se obtiene la informacion de cada una de las grabaciones
        except RuntimeError:
            grab_malas_df.append({"Grabaciones rechazadas":uniquehours[i].split('/')[-1], "Motivo":"Archivo corrupto"},
                                ignore_index=True)
            continue

        # se escoge el canal con que se quiere trabajar la grabacion
        if len(x.shape) == 1:
            audio = x
        else:
            audio = x[:, canal]

        puntos_minuto = Fs * 60          # se obtiene el numero de puntos por minuto de la grabacion
        npuntos = len(audio)
        banda = []

        # se obtiene el el welch por minuto de cada grabacion y luego se concatena de la variable (banda)
        for seg in range(0, npuntos, puntos_minuto):
            f, p = signal.welch(audio[seg:puntos_minuto+seg], Fs, nperseg=tamano_ventana, window=tipo_ventana,
                                nfft=nfft, noverlap=sobreposicion)
            banda.append(p[np.logical_and(f >= banda_lluvia[0], f <= banda_lluvia[1])])                 # la informacion obtenida solo se limita al rando de frecuencia banda_lluvia

        try:
            banda = np.concatenate(banda)
        except ValueError:
            grab_malas_df.append({"Grabaciones rechazadas":uniquehours[i].split('/')[-1], "Motivo":"Archivo corrupto"},
                                ignore_index=True)
            continue

        mean_a = np.mean(banda)         
        std_a = np.std(banda)

        c = mean_a/std_a

        PSD_medio[i] = mean_a                                                # se guarda la PSD promedio de cada grabacion
        SNR_medio[i] = c                                                     # se guarda la SNR de cada grabacion
        porcentaje = round(100 * (i + 1) / n_grabs, 2)
        print("Corriendo algoritmo de lluvia " + str(porcentaje) + "%")      # se muestra por consola el porcentaje de las grabaciones procesadas
        avance.put((cod_proc, i + 1))

    PSD_medio = np.array(PSD_medio)
    SNR_medio = np.array(SNR_medio)
    PSD_medio_sin_ceros = PSD_medio[PSD_medio > 0]
    Tmean = (np.mean(PSD_medio_sin_ceros) + stats.mstats.gmean(PSD_medio_sin_ceros)) / 2          # se halla el umbral Tmean
    Tsnr = np.mean(SNR_medio)

    cond_malas = np.logical_and((PSD_medio > Tmean) & (SNR_medio > Tsnr), PSD_medio != 0)
    cond_buenas = np.logical_and((PSD_medio <= Tmean) | (SNR_medio <= Tsnr), PSD_medio != 0)

    uniquehours = np.array(uniquehours)
    if rec_std==1:
        grab_buenas = uniquehours                                                                           # se guardan todas las grabaciones como buenas 
    else:
        grab_buenas = uniquehours[cond_buenas]                                                              # se guardan las grabaciones buenas
    grab_malas = np.array([[grab.split('/')[-1] for grab in uniquehours[cond_malas]]]).T                    # se guardan las grabaciones malas
    motivos = np.array([["Ruido Fuerte"]*grab_malas.shape[0]]).T
    # se genera  un df con todas las grabaciones malas
    grab_malas_df=pd.concat([grab_malas_df, pd.DataFrame(np.hstack((grab_malas, motivos)),
                                                         columns=["Grabaciones rechazadas", "Motivo"])],
                            ignore_index=True)
    '''

    ############################ Metodo intensidad del espectrograma promedio ###############################
    ############################ Implementado por Edison Ramirez Garcia Julio 28 2021   ###############################
    '''

    grabaciones = salida.get(0)                         # se obtienen las grabaciones          
    uniquehours=np.unique(grabaciones)                  # se ordenan las grabaciones 
    n_grabs = len(uniquehours)
    arraymeanspect_aux = np.zeros(shape=(n_grabs,257))  
    cond_buenas = np.full((n_grabs,1),False)
    cond_malas = np.full((n_grabs,1),False)
    canal = 1

    grab_malas_df = pd.DataFrame(columns=["Grabaciones rechazadas", "Motivo"])

    # se procesan todas las grabaciones
    for i in range(n_grabs):

        try:
            x, Fs = sf.read(uniquehours[i])         # se obtiene la informacion de cada una de las grabaciones
        except RuntimeError:
            grab_malas_df.append({"Grabaciones rechazadas":uniquehours[i].split('/')[-1], "Motivo":"Archivo corrupto"},
                                ignore_index=True)
            continue
        
        # se escoge el canal con que se quiere trabajar la grabacion
        if len(x.shape) == 1:
            audio = x
        else:
            audio = x[:, canal]

        # se obtiene el espectrograma de la grabacion
        f, t, s = signal.spectrogram(audio, Fs, window=tipo_ventana,nfft=512, 
                                        mode="magnitude"
                                        )

        arraymeanspect_aux[i] = (s.mean(axis=1))                         # se guarda el espectrograma promedio de cada grabacion
        porcentaje = round(100 * (i + 1) / n_grabs, 2)                   
        print("Corriendo algoritmo de lluvia " + str(porcentaje) + "%")  # se muestra por consola el porcentaje de las grabaciones procesadas
        avance.put((cod_proc, i + 1))
    
    nivel_actual = np.median(arraymeanspect_aux[:,43:65])                # se halla la mediana de todo el grupo de espectrogramas promedio de todas las grabaciones
    nivle_Normalizacion = 3.814165176863326e-05                          # mediana ideal de todo el grupo de grabaciones
    
    diferencia_escala = nivel_actual/nivle_Normalizacion
    arraymeanspect_aux = arraymeanspect_aux/diferencia_escala            # se lleva todo el grupo de espectrogramas promedio de todas las grabaciones a la escala ideal
    
    # se procesa cada grabacion para identificar cuales contiene lluvia
    for i in range(n_grabs):

        max_0_1500hz = max(arraymeanspect_aux[i,0:17])
        des_0_24000hz =  np.std(arraymeanspect_aux[i])
        max_9000_24000hz = max(arraymeanspect_aux[i,96:258])
        des_9000_24000hz = np.std(arraymeanspect_aux[i,96:258])
        min_1781_2343hz = min(arraymeanspect_aux[i,19:26])

        if max_0_1500hz > 0.0001:
            cond_malas[i] = True
        elif  max_9000_24000hz >= 0.0002:
            cond_buenas[i] = True
        elif des_9000_24000hz > 0.00001:
            cond_buenas[i] = True
        elif ((des_0_24000hz <= 2.3e-06) | (des_0_24000hz >= 4e-5)):
            cond_buenas[i] = True
        elif min_1781_2343hz < 0.00001:
            cond_buenas[i] = True
        else:
            cond_malas[i] = True
    
    uniquehours = np.array(uniquehours)
    if rec_std==1:
        grab_buenas = uniquehours                                                               # se guardan todas las grabaciones como buenas
    else:
        grab_buenas = uniquehours[cond_buenas[:,0]]                                             # se guardan las grabaciones buenas
    grab_malas = np.array([[grab.split('/')[-1] for grab in uniquehours[cond_malas[:,0]]]]).T   # se guardan las grabaciones malas
    motivos = np.array([["Ruido Fuerte"]*grab_malas.shape[0]]).T
    # se genera  un df con todas las grabaciones malas
    grab_malas_df=pd.concat([grab_malas_df, pd.DataFrame(np.hstack((grab_malas, motivos)),
                                                         columns=["Grabaciones rechazadas", "Motivo"])],
                            ignore_index=True)
    '''

    malas.put(grab_malas_df)        # se guarda el df con las grabaciones malas en la variable compartida (malas)
    salida.put(grab_buenas)         # se guarda todoas las grabaciones buenas en la variable compartida (salida)
    fin_proc.set()                  # se indica que se termino el proceso de esta funcion
    avance.put((cod_proc, 0))       # se manda el codigo que indica el siguinte proceso a iniciar

def calcular_descriptores(avance, param, salida, malas, cod_proc, fin_proc,ruta_salida,opc_ind):

    '''

    Este algoritmo calcula los descriptores.

    :param avance: recibe un Queue para indicar a la barra de progreso el avance del procedimiento
    :param param: recibe un Queue con parámetros necesarios para el siguiente proceso
    :param salida: recibe un Queue que guarda la salida del proceso
    :param malas: recibe un Queue que guarda las grabaciones rechazadas durante el procesamiento
    :param cod_proc: recibe un entero con el código del proceso
    :param fin_proc: recibe un Event que indica si el proceso actual terminó
    :return: None
    '''

    canal, indices, rec_std, tipo_ventana, tamano_ventana, sobreposicion, nfft, sinfiltro, lpf, bpf, hpf, fcl, fch, fmin, fmax, grabxdia, extension, cod_car = param.get(0)
    param.put((canal, indices, rec_std, tipo_ventana, tamano_ventana, sobreposicion, nfft, sinfiltro, lpf, bpf, hpf, fcl, fch, fmin, fmax, grabxdia, extension, cod_car))
    grab_buenas = salida.get(0)
    valores = []
    nombres_archivo = []
    ngrab_buenas = len(grab_buenas)
    grab_malas_df = malas.get(0)

    for i in range(ngrab_buenas):

        ruta_archivo = grab_buenas[i]
        x, Fs = sf.read(ruta_archivo)

        if len(x.shape) == 2:
            audio = x[:, canal]
        else:
            audio = x

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

        feats = []
        if indices:

            titulos = ["ACIft", "ADI", "ACItf", "BETA", "TE", "ESM", "NDSI", "P", "M", "NP", "MID", "BNF", "BNT", "MD",
                       "FM", "SF", "RMS", "CF", "SC","SB","Tonnets", "SVE", "SNR", "ADIm1", "ADIm2", "ADIm3", "ADIm4", "ADIm5", "ADIm6", "ADIm7", "ADIm8",
                       "ADIm9", "ADIm10", "ADIm11"]
            
            nmin = round(len(audio) / (60 * Fs))
            bio_band = (2000, 8000)
            tech_band = (200, 1500)
            f, t, s = signal.spectrogram(audio, Fs, window=tipo_ventana, nperseg=nmin * tamano_ventana, mode="magnitude", \
                                         noverlap=sobreposicion, nfft=nmin * nfft)

            ACIf = ACIft(s)

            if np.isnan(ACIf):
                grab_malas_df.append({"Grabaciones rechazadas":grab_buenas[i].split('/')[-1], "Motivo" : "Archivo discontinuo"},
                                     ignore_index=True)
                continue
            
            
            sin_select= "N/A"
            step_av = 1 / 34
            if 'ACIft' in opc_ind:
                feats.append(ACIf)
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + step_av))


            if 'ADI' in opc_ind:
                feats.append(ADI(s, 10000, 1000, -50))
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 2 * step_av))

            
            if 'ACItf' in opc_ind:
                feats.append(ACItf(audio, Fs, 5, s))
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 3 * step_av))


            if 'BETA' in opc_ind:
                feats.append(beta(s, f, bio_band) / nmin)
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 4 * step_av))


            if 'TE' in opc_ind: 
                feats.append(temporal_entropy(audio, Fs))
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 5 * step_av))


            if 'ESM' in opc_ind:
                feats.append(spectral_maxima_entropy(s, f, 482, 8820))
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 6 * step_av))


            if 'NDSI' in opc_ind:
                feats.append(NDSI(s, f, bio_band, tech_band))
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 7 * step_av))


            if 'P' in opc_ind:
                feats.append(rho(s, f, bio_band, tech_band))
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 8 * step_av))


            if 'M' in opc_ind:
                feats.append(median_envelope(audio, Fs, 16))
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 9 * step_av))


            if 'NP' in opc_ind:
                feats.append(number_of_peaks(s, f, 10 * nmin))
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 10 * step_av))


            if 'MID' in opc_ind:
                feats.append(mid_band_activity(s, f, 450, 3500))
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 11 * step_av))


            if 'BNF' in opc_ind:
                feats.append(np.mean(background_noise_freq(s)))
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 12 * step_av))


            if 'BNT' in opc_ind:
                feats.append(background_noise_time(wav2SPL(audio, -11, 9, 0.707), 5))
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 13 * step_av))


            if 'MD' in opc_ind:
                feats.append(musicality_degree(audio, Fs, tamano_ventana, nfft, tipo_ventana, sobreposicion))
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 14 * step_av))


            if 'FM' in opc_ind:
                feats.append(frequency_modulation(s))
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 15 * step_av))


            if 'SF' in opc_ind:
                feats.append(wiener_entropy(audio, tamano_ventana, nfft, tipo_ventana, sobreposicion))
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 16 * step_av))


            feats.append(rms(audio))  
            avance.put((cod_proc, i + 17 * step_av))


            if 'CF' in opc_ind:
                feats.append(crest_factor(audio, feats[16]))
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 18 * step_av))


            if 'SC' in opc_ind:
                feats.append(np.mean(librosa.feature.spectral_centroid(y=audio, sr=Fs)))
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 19 * step_av))


            if 'SB' in opc_ind:
                feats.append(np.mean(librosa.feature.spectral_bandwidth(y=audio, sr=Fs)))
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 20 * step_av))


            if 'Tonnets' in opc_ind:
                feats.append(np.mean(librosa.feature.tonnetz(audio,Fs)))
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 21 * step_av))


            if 'SVE' in opc_ind:
                feats.append(spectral_variance_entropy(s, f, 482, 8820))
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 22 * step_av))


            if 'SNR' in opc_ind:
                feats.append(signaltonoise(audio))
            else:
                feats.append(sin_select)
            avance.put((cod_proc, i + 23 * step_av))

            feats.extend(list(ADIm(s, Fs, 1000)[:11]))

        else:
            f, mspec = meanspec(audio, Fs, tipo_ventana, sobreposicion, tamano_ventana, nfft)
            feats = list(mspec[np.logical_and(f > fmin, f < fmax)])
            titulos = ["mPSD" + str(feat) for feat in range(len(feats))]

        porcentaje = round(100 * (i + 1) / ngrab_buenas, 2)
        valores.append(feats)
        nombres_archivo.append(ruta_archivo.split('/')[-1])
        print("Calculando descriptores", str(porcentaje) + "%")  # mensaje en consola
        avance.put((cod_proc, i + 1))

    valores = np.array(valores)
    valores_df = pd.DataFrame(valores, index=nombres_archivo, columns=titulos)
    
    
    malas.put(grab_malas_df)
    salida.put((valores_df,))
    fin_proc.set()
    avance.put((cod_proc, 0))

def escribir_salida(avance, salida, malas, ruta_salida, cod_proc, fin_proc, leer_excel):

    '''
    Esta función escribe los resultados en dos archivos:

    -Un excel que contiene además de los valores resultantes, una hoja con la lista de las grabaciones "dañadas"
    -Un archivo .dat que es utilizado por SALSA para el reconocimiento automático.

    :param avance: recibe un Queue para indicar a la barra de progreso el avance del procedimiento
    :param salida: recibe un Queue que guarda la salida del proceso
    :param malas: recibe un Queue que guarda las grabaciones rechazadas durante el procesamiento
    :param ruta_salida: recibe un str con la ruta absoluta de salida, en donde serán guardados los archivos resultantes
    :param cod_proc: recibe un entero con el código del proceso
    :param fin_proc: recibe un Event que indica si el proceso actual terminó
    :param leer_excel: recibe un Event que indica que el archivo excel de salida está disponible para escribir
    :return: None
    '''

    grab_malas_df = malas.get(0)
    salida = salida.get(0)
    ispsd = len(salida) == 1

    if ispsd:
        valores_df = salida[0]
    else:
        sin_std = salida[0]

    ruta_salida_excel = ruta_salida + ".xlsx"

    writer = pd.ExcelWriter(ruta_salida_excel)

    if ispsd:
        valores_df.to_excel(writer, index_label="Dia", sheet_name="descriptores")

    else:
        sin_std.to_excel(writer, index_label="Dia", sheet_name="descriptores")
       
    grab_malas_df.to_excel(writer, sheet_name="rechazadas")

    excel_abierto = True

    while excel_abierto and leer_excel.wait():
        try:
            writer.close()
            excel_abierto = False
        except PermissionError:
            leer_excel.clear()
            fin_proc.set()
            avance.put((-2, None))

    fin_proc.set()
    avance.put((cod_proc, 0))


# --------------------------------------- Fin Funciones de Procesamiento -----------------------------------------------#
'''
Referencias:

[1] Bedoya, C., Isaza, C., Daza, J. M., & López, J. D. (2017). Automatic identification of rainfall in acoustic
    recordings. Ecological Indicators, 75, 95–100. http://doi.org/10.1016/j.ecolind.2016.12.018

'''