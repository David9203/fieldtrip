'''
Interfaz Gráfica y funciones para la extracción de descriptores de paisaje acústico.

modificaciones noviembre 2020 se agregan botones para seleccionar indices a calcular (No funcionales) y funcion que dice cuales se seleccionan
Modificaciones enero 2021 se hace funcional el frame de indices 
'''
from Indices_PSD import *
from espectrogras_T_I import *
from tkinter import *
from tkinter.filedialog import askdirectory
from tkinter.ttk import Progressbar
from tkinter import messagebox
from multiprocessing import Process, Queue, Event, freeze_support
from queue import Empty 
import os
import glob



salida = Queue()
param = Queue() 
avance = Queue()
malas = Queue()
fin_proc = Event()
leer_excel = Event()
leer_excel.set()
procesos = []
mensajes = []
opc_ind = []


#---------------------------------------Funciones de la Interfaz Gráfica-----------------------------------------------#

def admin_procesos(avance, param, salida, malas, procesos, mensajes, fin_proc, leer_excel):
    '''

    Esta función ejecuta secuencialmente los algoritmos de procesamiento y se encarga de que puedan comunicarse entre
    ellos

    :param avance: recibe un Queue para indicar a la barra de progreso el avance del procedimiento
    :param param: recibe un Queue con parámetros necesarios para el siguiente proceso
    :param salida: recibe un Queue que guarda la salida del proceso
    :param malas: recibe un Queue que guarda las grabaciones rechazadas durante el procesamiento
    :param procesos: recibe una lista con los procesos que van a ejecutarse (los algoritmos)
    :param mensajes: recibe una lista con cadenas de caracteres que describen cada paso del procesamiento
    :param fin_proc: recibe un Event que indica si el proceso actual terminó
    :param leer_excel: recibe un Event que indica que el archivo excel de salida está disponible para escribir
    :return: retorna None
    '''

    if fin_proc.is_set():

        p_actual, valor = avance.get()

        if p_actual == -2:
            mensaje_error("Cierre el archivo excel para continuar")
            fin_proc.clear()
            leer_excel.set()

        if p_actual == -1:
            prog_cont["text"] = "Progreso"
            prog_bar.stop()
            procesos.clear()
            mensajes.clear()
            fin_proc.clear()
            cor_bot["state"] = "normal"
            return

        p_actual += 1

        if p_actual == 1:
            global carpetas
            carpetas = salida.get(0)

            msj_ad = " 1/1"
            if len(carpetas) > 1:
                msj_ad = " 1/" + str(len(carpetas))

            canal, indices, rec_std,  tipo_ventana, tamano_ventana, sobreposicion, nfft, sinfiltro, lpf, bpf, hpf, fcl, fch, fmin, fmax, grabxdia, extension = param.get(
                0)
            param.put(
                (canal, indices, rec_std,  tipo_ventana, tamano_ventana, sobreposicion, nfft, sinfiltro, lpf, bpf, hpf, fcl, fch, fmin, fmax, grabxdia, extension, 0))
            
            extension_min = extension.lower()
            grabaciones = glob.glob(carpetas[0] + "/*" + extension)
            grabaciones_min = glob.glob(carpetas[0] + "/*" + extension_min)
            grabaciones = grabaciones + grabaciones_min
            salida.put(grabaciones)
            procesos[p_actual].start()
            fin_proc.clear()
            prog_bar.stop()
            prog_bar["mode"] = "determinate"
            prog_bar["value"] = 0
            prog_bar["maximum"] = len(grabaciones)
            prog_cont["text"] = mensajes[p_actual] + msj_ad

        elif p_actual == 2:
            canal, indices, rec_std, tipo_ventana, tamano_ventana, sobreposicion, nfft, sinfiltro, lpf, bpf, hpf, fcl, fch, fmin, fmax, grabxdia, extension, \
            cod_car = param.get(0)
            param.put((canal, indices, rec_std, tipo_ventana, tamano_ventana, sobreposicion, nfft, sinfiltro, lpf, bpf, hpf, fcl, fch, fmin, fmax, grabxdia,
                       extension, cod_car))

            msj_ad = " " + str(cod_car + 1) + "/" + str(len(carpetas))

            sal = salida.get()
            salida.put(sal)
            procesos[p_actual].start()
            fin_proc.clear()
            prog_bar.stop()
            prog_bar["mode"] = "determinate"
            prog_bar["value"] = 0
            prog_bar["maximum"] = len(sal)
            prog_cont["text"] = mensajes[p_actual] + msj_ad

        elif p_actual == 3:
            canal, indices, rec_std, tipo_ventana, tamano_ventana, sobreposicion, nfft, sinfiltro, lpf, bpf, hpf, fcl, fch, fmin, fmax, grabxdia, extension, cod_car = param.get(
                0)
            param.put((canal, indices, rec_std, tipo_ventana, tamano_ventana, sobreposicion, nfft, sinfiltro, lpf, bpf, hpf, fcl, fch, fmin, fmax, grabxdia,
                       extension, cod_car))

            msj_ad = " " + str(cod_car + 1) + "/" + str(len(carpetas))

            procesos[p_actual].start()
            fin_proc.clear()
            prog_bar.stop()
            prog_bar["value"] = 0
            prog_bar["maximum"] = 100
            prog_bar["mode"] = "indeterminate"
            prog_cont["text"] = mensajes[p_actual] + msj_ad
            prog_bar.start()

        elif p_actual in range(4, len(procesos)):
            procesos[p_actual].start()
            fin_proc.clear()
            prog_bar.stop()
            prog_bar["value"] = 0
            prog_bar["maximum"] = 100
            prog_bar["mode"] = "indeterminate"
            prog_cont["text"] = mensajes[p_actual]
            prog_bar.start()

        else:
            prog_bar.stop()
            prog_cont["text"] = "Progreso"
            cor_bot["state"] = "normal"
            mensaje_error("Descriptores guardados correctamente")
            procesos.clear()
            mensajes.clear()
            fin_proc.clear()
            return

    else:

        try:
            p_actual, valor = avance.get(0)
            prog_bar["value"] = valor

        except Empty:
            pass

    ven_pri.after(100, lambda: admin_procesos(avance, param, salida, malas, procesos, mensajes, fin_proc, leer_excel))

def admin_procesos_esp(avance, param, salida, procesos, mensajes, fin_proc):
    '''

    Esta función ejecuta secuencialmente los algoritmos de procesamiento y se encarga de que puedan comunicarse entre
    ellos

    :param avance: recibe un Queue para indicar a la barra de progreso el avance del procedimiento
    :param param: recibe un Queue con parámetros necesarios para el siguiente proceso
    :param salida: recibe un Queue que guarda la salida del proceso
    :param malas: recibe un Queue que guarda las grabaciones rechazadas durante el procesamiento
    :param procesos: recibe una lista con los procesos que van a ejecutarse (los algoritmos)
    :param mensajes: recibe una lista con cadenas de caracteres que describen cada paso del procesamiento
    :param fin_proc: recibe un Event que indica si el proceso actual terminó
    :param leer_excel: recibe un Event que indica que el archivo excel de salida está disponible para escribir
    :return: retorna None
    '''

    if fin_proc.is_set():

        p_actual, valor = avance.get()
        
        p_actual += 1
        if p_actual == 1:
            global carpetas
            carpetas = salida.get(0)

            msj_ad = " 1/1"
            if len(carpetas) > 1:
                msj_ad = " 1/" + str(len(carpetas))

            canal, indices, rec_std,  tipo_ventana, tamano_ventana, sobreposicion, nfft, sinfiltro, lpf, bpf, hpf, fcl, fch, fmin, fmax, grabxdia, extension = param.get(
                0)
            param.put(
                (canal, indices, rec_std,  tipo_ventana, tamano_ventana, sobreposicion, nfft, sinfiltro, lpf, bpf, hpf, fcl, fch, fmin, fmax, grabxdia, extension, 0))
            
            extension_min = extension.lower()
            grabaciones = glob.glob(carpetas[0] + "/*" + extension)
            grabaciones_min = glob.glob(carpetas[0] + "/*" + extension_min)
            grabaciones = grabaciones + grabaciones_min
            salida.put(grabaciones)
            procesos[p_actual].start()
            fin_proc.clear()
            prog_bar.stop()
            prog_bar["mode"] = "determinate"
            prog_bar["value"] = 0
            prog_bar["maximum"] = len(grabaciones)
            prog_cont["text"] = mensajes[p_actual] + msj_ad
        else:
            prog_bar.stop()
            prog_cont["text"] = "Progreso"
            cor_bot["state"] = "normal"
            mensaje_error("espectrogramas guardados correctamente")
            procesos.clear()
            mensajes.clear()
            fin_proc.clear()
            return

    else:

        try:
            p_actual, valor = avance.get(0)
            prog_bar["value"] = valor

        except Empty:
            pass

    ven_pri.after(100, lambda: admin_procesos_esp(avance, param, salida, procesos, mensajes, fin_proc))


def cambio_descriptor(*args):
    '''

    Esta función activa los controles correspondientes al tipo de descriptor seleccionado y desactiva los controles
    del otro tipo de descriptor

    :param args: Recibe unos argumentos por defecto de la interfaz
    :return: retorna None
    '''

    if ftip_var.get() == "PSD":
        todos_check['state'] = "disabled"
        acift_check['state'] = "disabled"
        acitf_check['state'] = "disabled"
        adi_check['state'] = "disabled"
        bnf_check['state'] = "disabled"
        bnt_check['state'] = "disabled"
        beta_check['state'] = "disabled"
        cf_check['state'] = "disabled"
        fm_check['state'] = "disabled"
        sc_check['state'] = "disabled"
        m_check['state'] = "disabled"
        mid_check['state'] = "disabled"
        md_check['state'] = "disabled"
        ndsi_check['state'] = "disabled"
        p_check['state'] = "disabled"
        snr_check['state'] = "disabled"
        esm_check['state'] = "disabled"
        sve_check['state'] = "disabled"
        te_check['state'] = "disabled"
        sf_check['state'] = "disabled"
        np_check['state'] = "disabled"
        sb_check['state'] = "disabled"
        ton_check['state'] = "disabled"
        btnselect['state'] = "disabled"
        promediEsp_check['state'] = "disabled" 
        promediEspDuracion_check['state'] = "disabled"
        todoEsp_check['state'] = "disabled"
        filtro_menu['state'] = "disabled"
        filtro_var.set("NAN")
        fcl_entry['state'] = "disabled"
        fch_entry['state'] = "disabled"
        todo_check['state'] = "normal"            
        win_entry['state'] = "normal"
        fmin_entry['state'] = "normal"
        fmax_entry['state'] = "normal"
  

    elif ftip_var.get() == "Espectrogramas":    
        todos_check['state'] = "disabled"
        acift_check['state'] = "disabled"
        acitf_check['state'] = "disabled"
        adi_check['state'] = "disabled"
        bnf_check['state'] = "disabled"
        bnt_check['state'] = "disabled"
        beta_check['state'] = "disabled"
        cf_check['state'] = "disabled"
        fm_check['state'] = "disabled"
        sc_check['state'] = "disabled"
        m_check['state'] = "disabled"
        mid_check['state'] = "disabled"
        md_check['state'] = "disabled"
        ndsi_check['state'] = "disabled"
        p_check['state'] = "disabled"
        snr_check['state'] = "disabled"
        esm_check['state'] = "disabled"
        sve_check['state'] = "disabled"
        te_check['state'] = "disabled"
        sf_check['state'] = "disabled"
        np_check['state'] = "disabled"
        sb_check['state'] = "disabled"
        ton_check['state'] = "disabled"
        btnselect['state'] = "disabled"
        promediEsp_check['state'] = "normal"
        promediEspDuracion_check['state'] = "normal"
        todoEsp_check['state'] = "normal"
        filtro_menu['state'] = "normal"
        todo_check['state'] = "disabled"
        win_entry['state'] = "disabled"
        fmin_entry['state'] = "disabled"
        fmax_entry['state'] = "disabled"


    else:
        todos_check['state'] = "normal"
        acift_check['state'] = "normal"
        acitf_check['state'] = "normal"
        adi_check['state'] = "normal"
        bnf_check['state'] = "normal"
        bnt_check['state'] = "normal"
        beta_check['state'] = "normal"
        cf_check['state'] = "normal"
        fm_check['state'] = "normal"
        sc_check['state'] = "normal"
        m_check['state'] = "normal"
        mid_check['state'] = "normal"
        md_check['state'] = "normal"
        ndsi_check['state'] = "normal"
        p_check['state'] = "normal"
        snr_check['state'] = "normal"
        esm_check['state'] = "normal"
        sve_check['state'] = "normal"
        te_check['state'] = "normal"
        sf_check['state'] = "normal"
        np_check['state'] = "normal"
        sb_check['state'] = "normal"
        ton_check['state'] = "normal"
        btnselect['state'] = "normal"
        promediEsp_check['state'] = "disabled" 
        promediEspDuracion_check['state'] = "disabled"    
        todoEsp_check['state'] = "disabled"
        filtro_menu['state'] = "normal"
        todo_check['state'] = "normal"             
        win_entry['state'] = "disabled"
        fmin_entry['state'] = "disabled"
        fmax_entry['state'] = "disabled"
    
    
def seleccionar_filtro(*args):
    '''
        Esta función activa los controles correspondientes al tipo de filtro seleccionado y desactiva los controles
        de los otros tipos de Filtro

        :param args: Recibe unos argumentos por defecto de la interfaz
        :return: retorna None
    '''

    if filtro_var.get() == "HPF":
        fcl_entry['state'] = "normal"
        fch_entry['state'] = 'disabled'
    if filtro_var.get() == "LPF":
        fcl_entry['state'] = "disabled"
        fch_entry['state'] = 'normal'
    if filtro_var.get() == "BPF":
        fcl_entry['state'] = "normal"
        fch_entry['state'] = 'normal'
    if filtro_var.get() == "NAN":
        fcl_entry['state'] = "disabled"
        fch_entry['state'] = 'disabled'

def ejecutar_programa(avance, param, salida, malas, fin_proc, read_excel, procesos, mensajes):

    '''

    Esta función se ejecuta cuando se inicia el procesamiento. Crea los procesos y llama admin_procesos para que regule
    el funcionamiento de los algoritmos.

    :param avance: recibe un Queue para indicar a la barra de progreso el avance del procedimiento
    :param param: recibe un Queue con parámetros necesarios para el siguiente proceso
    :param salida: recibe un Queue que guarda la salida del proceso
    :param malas: recibe un Queue que guarda las grabaciones rechazadas durante el procesamiento
    :param fin_proc: recibe un Event que indica si el proceso actual terminó
    :param leer_excel: recibe un Event que indica que el archivo excel de salida está disponible para escribir
    :param procesos: recibe una lista con los procesos que van a ejecutarse (los algoritmos)
    :param mensajes: recibe una lista con cadenas de caracteres que describen cada paso del procesamiento
    :return: None
    '''

    cor_bot["state"] = "disabled"
    espectrogramaOpc = False                      
    carpeta_grabaciones = ruta_entry.get()
    extension = '.' + ext_var.get()
    #extension_min = '.' + ext_var.get().lower()
    canal_str = can_entry.get()

    if ftip_var.get() == "Índices":
        indices = True
    elif ftip_var.get() == "Espectrogramas": 
        espectrogramaOpc = True
        indices = False 
    else:
        indices = False
    #Determinar filtro___________
    if filtro_var.get() == "NAN":
        sinfiltro = True
        lpf= False
        hpf= False
        bpf= False
    if filtro_var.get() == "LPF":
        sinfiltro = False
        lpf= True
        hpf= False
        bpf= False
    if filtro_var.get() == "BPF":
        sinfiltro = False
        lpf= False
        hpf= False
        bpf= True
    if filtro_var.get() == "HPF":
        sinfiltro = False
        lpf= False
        hpf= True
        bpf= False
    #Fin determinar filtro__________________

    fmin_str = fmin_entry.get()
    fmax_str = fmax_entry.get()
    tamano_ventana_str = win_entry.get()
    fcl_str = fcl_entry.get()
    fch_str = fch_entry.get()
    rec_std = bool(todo_var.get())
    grabxdia_str = "144"  #  ngrab_entry.get() ya no se utiliza
    carpeta_salida = sal_entry.get()
    nombre_salida = nom_entry.get()
    subcarpetas = bool(sub_var.get())
    promedioEsp = bool(promediEsp_var.get())
    promedioEspDuracion = bool(promediEspDuracion_var.get())  
    todoEsp = bool(todoEsp_var.get())    

    ruta_salida = carpeta_salida + '/' + nombre_salida

    param.put((subcarpetas,rec_std, carpeta_grabaciones, extension, canal_str, indices, sinfiltro, lpf, bpf, hpf, fcl_str, fch_str,fmin_str, fmax_str, tamano_ventana_str,
               carpeta_salida, grabxdia_str))

    nproc = 0

    val_proc =  Process(target=validar_entradas, args=(avance, param, salida, nproc, fin_proc))
    val_proc.start()
    procesos.append(val_proc)
    prog_cont["text"] = "Verificando entradas"
    mensajes.append("Verificando entradas")
    prog_bar.start()
    nproc += 1

    if espectrogramaOpc:
        fecha_proc = Process(target=algoritmo_espectrograma, args=(avance, param, salida, nproc, fin_proc, promedioEsp, promedioEspDuracion, todoEsp, carpeta_salida))
        procesos.append(fecha_proc)
        mensajes.append("Corriendo algoritmo de espectroframa...")
        admin_procesos_esp(avance, param, salida, procesos, mensajes, fin_proc)

    else:
        lluvia_proc = Process(target=algoritmo_lluvia, args=(avance, param, salida, malas, nproc, fin_proc))
        procesos.append(lluvia_proc)
        mensajes.append("Corriendo algoritmo de lluvia...")
        nproc += 1

        opc_ind= select_index()
        desc_proc = Process(target=calcular_descriptores, args=(avance, param, salida, malas, nproc, fin_proc, ruta_salida,opc_ind))
        procesos.append(desc_proc)
        mensajes.append("Calculando descriptores...")
        nproc += 1

        esc_proc = Process(target=escribir_salida, args=(avance, salida, malas, ruta_salida, nproc, fin_proc, read_excel))
        procesos.append(esc_proc)
        mensajes.append("Escribiendo archivos de salida...")

        admin_procesos(avance, param, salida, malas, procesos, mensajes, fin_proc, read_excel)


def escoger_carpeta(boton):

    '''

    Esta función es invocada cuando se quiere seleccionar una carpeta

    :param boton: Indica el botón que llamó la función (puede ser el botón de la carpeta de entrada o la carpeta de salida
    :return: None
    '''

    ruta = askdirectory()

    if boton == buscar_bot:
        ruta_entry.delete(0, END)
        ruta_entry.insert(0, ruta)

    elif boton == buscars_bot:
        sal_entry.delete(0, END)
        sal_entry.insert(0, ruta)

def mensaje_error(mensaje):

    '''
    Esta función es invocada cuando se presenta un error en el programa. Muestra una ventana con el mensaje de error

    :param mensaje: Str con el mensaje de error a mostrar
    :return: None
    '''

    error_ven = Tk()
    error_ven.withdraw()
    messagebox.showinfo("Aviso", mensaje)
    error_ven.destroy()

def salir(procesos):

    '''

    Esta función es invocada cuando el programa es cerrado por el usuario.

    :param procesos: recibe una lista con los procesos
    :return: None
    '''

    for process in procesos:
        if process.is_alive():
            process.terminate()
    ven_pri.destroy()

def validar_entradas(avance, param, salida, cod_proc, fin_proc):

    '''
    Esta función verifica que los valores ingresados en la interfaz sean correctos

    :param avance: recibe un Queue para indicar a la barra de progreso el avance del procedimiento
    :param param: recibe un Queue con parámetros necesarios para el siguiente proceso
    :param salida: recibe un Queue que guarda la salida del proceso
    :param cod_proc: recibe un entero con el código del proceso
    :param fin_proc: recibe un Event que indica si el proceso actual terminó
    :return: retorna None
    '''

    subcarpetas, rec_std,  carpeta_grabaciones, extension, canal_str, indices, sinfiltro, lpf, bpf, hpf, fcl_str, fch_str, fmin_str, fmax_str, tamano_ventana_str, carpeta_salida, grabxdia_str = param.get(0)

    extension_min = extension.lower()

    if not subcarpetas:
        grabaciones = glob.glob(carpeta_grabaciones + "/*" + extension)
        grabaciones_min = glob.glob(carpeta_grabaciones + "/*" + extension_min)
        grabaciones = grabaciones + grabaciones_min
        if len(grabaciones) == 0:
            mensaje_error("No se encontraron grabaciones")
            fin_proc.set()
            avance.put((-1, None))
            return

        carpetas = [carpeta_grabaciones]

    else:

        carpetas = []

        for root, dirs, files in os.walk(carpeta_grabaciones):
            for file in files:
                if extension in file:
                    carpetas.append(root)
                    break

    if len(carpetas) == 0:
        mensaje_error("No se encontraron grabaciones")
        fin_proc.set()
        avance.put((-1, None))
        return

    grabaciones = glob.glob(carpetas[0] + "/*" + extension)
    grabaciones_min = glob.glob(carpetas[0] + "/*" + extension_min)
    grabaciones = grabaciones + grabaciones_min

    for grab in grabaciones:
        try:
            x, Fs = sf.read(grab)
            break
        except:
            pass

    if not (canal_str+grabxdia_str+fcl_str+ fch_str+fmin_str+fmax_str+tamano_ventana_str).isnumeric():
        mensaje_error("Ingrese valores numéricos")
        fin_proc.set()
        avance.put((-1, None))
        return

    canal = int(canal_str) - 1

    if len(x.shape) <= canal:
        mensaje_error("No existe el canal " + str(canal + 1))
        fin_proc.set()
        avance.put((-1, None))
        return

    tipo_ventana = "hann"
    sobreposicion = 0
    tamano_ventana = int(tamano_ventana_str)
    fmin = int(fmin_str)
    fmax = int(fmax_str)
    fcl=   int(fcl_str)
    fch=   int(fch_str)

    if indices:
        tamano_ventana = 1024

    else:
        if tamano_ventana > Fs // 2:
            mensaje_error("Ventana demasiado grande")
            fin_proc.set()
            avance.put((-1, None))
            return

    nfft = tamano_ventana

    if not os.path.isdir(carpeta_salida):
        mensaje_error("Ingrese un directorio de salida válido")
        fin_proc.set()
        avance.put((-1, None))

        return

    grabxdia = int(grabxdia_str)

    salida.put(carpetas)
    param.put((canal, indices, rec_std, tipo_ventana, tamano_ventana, sobreposicion, nfft, sinfiltro, lpf, bpf, hpf, fcl, fch, fmin, fmax, grabxdia, extension))
    fin_proc.set()
    avance.put((cod_proc, None))

def select_index():
    index=[]
    if (acift.get()==1):
        index.append('ACIft')
    if (acitf.get()==1):
        index.append('ACItf')
    if (adi.get()==1):
        index.append('ADI')
    if (bnf.get()==1):
        index.append('BNF')
    if (bnt.get()==1):
        index.append('BNT')
    if (beta.get()==1):
        index.append('BETA')
    if (cf.get()==1):
        index.append('CF')
    if (fm.get()==1):
        index.append('FM')
    if (m.get()==1):
        index.append('M')
    if (np.get()==1):
        index.append('NP')
    if (mid.get()==1):
        index.append('MID')
    if (md.get()==1):
        index.append('MD')
    if (ndsi.get()==1):
        index.append('NDSI')
    if (rho.get()==1):
        index.append('P')
    if (esm.get()==1):
        index.append('ESM')
    if (sve.get()==1):
        index.append('SVE')
    if (te.get()==1):
        index.append('HT')
    if (sf1.get()==1):
        index.append('SF')
    if (snr.get()==1):
        index.append('SNR')
    if (sc.get()==1):
        index.append('SC')
    if (sb.get()==1):
        index.append('SB')
    if (tonnets.get()==1):
        index.append('Tonnets')

    if (todos.get()==1):
        index=["ACIft", "ADI", "ACItf", "BETA", "TE", "ESM", "NDSI", "P", "M", "NP", "MID", "BNF", "BNT", "MD",
                       "FM", "SF", "RMS", "CF", "SC","SB","Tonnets", "SVE", "SNR", "ADIm1", "ADIm2", "ADIm3", "ADIm4", "ADIm5", "ADIm6", "ADIm7", "ADIm8",
                       "ADIm9", "ADIm10", "ADIm11"]
        return(index)
        
    else:
        return(index)
    

#------------------------------------- Fin Funciones de la Interfaz Gráfica -------------------------------------------#

# --------------------------------------------- Interfaz Gráfica ------------------------------------------------------#

if __name__ == '__main__': #Se utiliza este if para poder usar varios procesos. (Son necesarios varios procesos para actualizar la barra de progreso)

    freeze_support() #Para correr el programa sin problemas como ejecutable

    ANCHO = 720
    ALTO = 600
    PAD = 7

    # Ventana principal
    ven_pri = Tk()
    ven_pri.geometry(str(ANCHO) + 'x' + str(ALTO))
    ven_pri.title("Descriptores del Paisaje Acústico")
    ven_pri.resizable(width=False, height=False)

    # Frame para selección de carpeta
    carp_cont = LabelFrame(ven_pri, text=" Carpeta con Grabaciones ")
    carp_cont.pack(fill=X, padx=PAD, pady=PAD)
    ruta_entry = Entry(carp_cont, width=45)
    ruta_entry.pack(side=LEFT)
    sub_var = IntVar()
    sub_check = Checkbutton(carp_cont, text="Contiene subcarpetas", justify=CENTER, variable=sub_var, state="normal")
    sub_check.pack(side=LEFT)
    buscar_bot = Button(carp_cont, text="Buscar...", command=lambda: escoger_carpeta(buscar_bot))
    buscar_bot.pack(expand=True)

    # Frame para configuración de grabaciones
    par_cont = LabelFrame(ven_pri, text=" Parámetros ")
    par_cont.pack(fill=X, padx=PAD, pady=PAD)
    can_lab = Label(par_cont, text="  Canal:", width=5)
    can_lab.pack(side=LEFT)
    can_entry = Entry(par_cont, width=3, justify=CENTER)
    can_entry.insert(END, "1")
    can_entry.pack(side=LEFT)
    ext_lab = Label(par_cont, text="Formato:", width=8)
    ext_lab.pack(side=LEFT)
    ext_var = StringVar(ven_pri)
    ext_var.set("WAV")
    ext_menu = OptionMenu(par_cont, ext_var, "WAV","8SVX", "AIFF", "AU", "FLAC", "IFF", "MOGG", "OGA", "OGG", "RAW")
    ext_menu.pack(side=LEFT)
    ftip_lab = Label(par_cont, text="Descriptores:", width=10)
    ftip_lab.pack(side=LEFT)
    ftip_var = StringVar(ven_pri)
    ftip_var.set("Índices")
    ftip_var.trace('w', cambio_descriptor)
    ext_menu = OptionMenu(par_cont, ftip_var, "Índices", "PSD", "Espectrogramas")
    ext_menu.pack(side=LEFT)
    filtro_lab=Label(par_cont, text="Filtro:", width=8)
    filtro_lab.pack(side=LEFT)
    filtro_var = StringVar(ven_pri)
    filtro_var.set("NAN")
    filtro_var.trace('w', seleccionar_filtro)
    filtro_menu=OptionMenu(par_cont, filtro_var, "NAN", "LPF","BPF","HPF")
    filtro_menu.pack(side=LEFT)

    #----------------------- Grabaciones diarias ya no se esta utilizando ----------------·#
    #ngrab_lab = Label(par_cont, text="Grabaciones\n diarias:", width=10)
    #ngrab_lab.pack(side=LEFT)
    #ngrab_entry = Entry(par_cont, width=5, justify=CENTER)
    #ngrab_entry.insert(0, "144")
    #ngrab_entry.pack(side=LEFT)
    #-------------------------------------------------------------------------------------·#

    # Frame Configuración que contiene otros frames
    conf_cont = LabelFrame(ven_pri, text=" Configuración de Descriptores ")
    conf_cont.pack(fill=X, padx=PAD, pady=PAD)

    #Frame para configuración de Espectogramas  
    espGrab_cont = LabelFrame(conf_cont)                                                            
    espGrab_cont.pack(padx=PAD, pady=PAD, side=LEFT)                                                                                                  
    esp_cont = LabelFrame(espGrab_cont, text=" Espectogramas ")                                     
    esp_cont.pack(padx=PAD, pady=PAD, side=BOTTOM)                                                  
    todoEsp_var = IntVar()                                                                         
    promediEsp_var = IntVar()
    promediEsp_var.set(True)
    promediEspDuracion_var = IntVar()
    promediEsp_check = Checkbutton(esp_cont, text="Espectrograma promedio (horas de las grabaciones)", justify=LEFT, \
                                 variable=promediEsp_var, state="normal")                          
    promediEsp_check.pack()
    promediEspDuracion_check = Checkbutton(esp_cont, text="Espectrograma promedio (duracion de la grabación)", justify=LEFT, \
                                 variable=promediEspDuracion_var, state="normal")                              
    promediEspDuracion_check.pack()                                                                        
    todoEsp_check = Checkbutton(esp_cont, text="Espectrogramas por grabación                     ", justify=LEFT, \
                                 variable=todoEsp_var, state="normal")                              
    todoEsp_check.pack()                                                                                                                                                      
    
    #Frame para configuración de índices                                                       
    ind_cont = LabelFrame(espGrab_cont, text=" índices ")                                     
    ind_cont.pack(side=BOTTOM, padx=PAD, pady=PAD)                                                 
    todo_var = IntVar()                                                                             
    todo_check = Checkbutton(ind_cont, text="Calcular todas las grabaciones                   ", justify=LEFT, \
                                 variable=todo_var, state="normal")                                 
    todo_check.pack() 

    #Frame para seleccionar indices________________________
    select_cont = LabelFrame(ven_pri, text=" Seleccionar indices ")
    select_cont.pack(fill=X, padx=PAD, pady=PAD)
    
    #frame funcione
    c_cont = LabelFrame(select_cont)
    c_cont.pack(padx=PAD, pady=PAD, side=LEFT)
    acift = IntVar()
    acitf = IntVar()
    adi = IntVar()
    bnf = IntVar()
    bnt = IntVar()
    acift_check= Checkbutton(c_cont, text="ACIft", justify=LEFT, variable=acift, state="normal")
    acift_check.pack()
    acitf_check= Checkbutton(c_cont, text="ACItf", justify=LEFT, variable=acitf, state="normal")
    acitf_check.pack()
    adi_check= Checkbutton(c_cont, text="ADI  ", justify=LEFT, variable=adi, state="normal")
    adi_check.pack()
    bnf_check= Checkbutton(c_cont, text="BNF  ", justify=LEFT, variable=bnf, state="normal")
    bnf_check.pack()     
    bnt_check= Checkbutton(c_cont, text="BNT  ", justify=LEFT,variable=bnt, state="normal")
    bnt_check.pack()

    c_cont1 = LabelFrame(select_cont)
    c_cont1.pack(padx=PAD, pady=PAD, side=LEFT)
    beta = IntVar()
    cf = IntVar()
    fm = IntVar()
    m = IntVar()
    sc = IntVar()
    beta_check= Checkbutton(c_cont1, text="BETA ", justify=LEFT, variable=beta, state="normal")
    beta_check.pack()
    cf_check= Checkbutton(c_cont1, text="CF   ", justify=LEFT, variable=cf, state="normal")
    cf_check.pack()
    fm_check= Checkbutton(c_cont1, text="FM   ", justify=RIGHT, variable=fm, state="normal")
    fm_check.pack()
    sc_check= Checkbutton(c_cont1, text="SC   ", justify=RIGHT, variable=sc, state="normal")
    sc_check.pack()
    m_check= Checkbutton(c_cont1, text="M    ", justify=RIGHT, variable=m, state="normal")
    m_check.pack()    
        
    c_cont2 = LabelFrame(select_cont)
    c_cont2.pack(padx=PAD, pady=PAD, side=LEFT)
    mid = IntVar()
    md = IntVar()
    ndsi = IntVar()
    rho = IntVar()
    snr = IntVar()
    mid_check= Checkbutton(c_cont2, text="MID  ", justify=RIGHT,variable=mid, state="normal")
    mid_check.pack()
    md_check= Checkbutton(c_cont2, text="MD   ", justify=RIGHT, variable=md, state="normal")
    md_check.pack()
    ndsi_check= Checkbutton(c_cont2, text="NDSI ", justify=RIGHT, variable=ndsi, state="normal")
    ndsi_check.pack()
    p_check= Checkbutton(c_cont2, text="  P  ", justify=RIGHT, variable=rho, state="normal")
    p_check.pack()
    snr_check= Checkbutton(c_cont2, text="SNR  ", justify=RIGHT, variable=snr, state="normal")
    snr_check.pack()
    
    c_cont3 = LabelFrame(select_cont)
    c_cont3.pack(padx=PAD, pady=PAD, side=LEFT)
    esm = IntVar()
    sve = IntVar()
    te = IntVar()
    sf1 = IntVar()
    np = IntVar()
    esm_check= Checkbutton(c_cont3, text="ESM ", justify=RIGHT, variable=esm, state="normal",)
    esm_check.pack()
    sve_check= Checkbutton(c_cont3, text="SVE ", justify=RIGHT,variable=sve, state="normal")
    sve_check.pack()
    te_check= Checkbutton(c_cont3, text="TE  ", justify=RIGHT, variable=te, state="normal")
    te_check.pack()
    sf_check= Checkbutton(c_cont3, text="SF  ", justify=RIGHT, variable=sf1, state="normal",)
    sf_check.pack()
    np_check= Checkbutton(c_cont3, text="NP  ", justify=RIGHT, variable=np, state="normal",)
    np_check.pack()
       
    c_cont4 = LabelFrame(select_cont)
    c_cont4.pack(padx=PAD, pady=PAD, side=LEFT)
      
    sb = IntVar()
    tonnets = IntVar()
    todos = BooleanVar()

    sb_check= Checkbutton(c_cont4, text="SB          ", justify=RIGHT, variable=sb, state="normal")
    sb_check.pack()
    ton_check= Checkbutton(c_cont4, text="Tonnets     ", justify=RIGHT, variable=tonnets, state="normal")
    ton_check.pack()
    todos_check= Checkbutton(c_cont4, text="Todos       ", justify=RIGHT, variable=todos, state="normal")
    todos_check.pack()
    espacio_lab = Label(c_cont4)  
    espacio_lab.pack()            
    btnselect= Button(c_cont4, text="Seleccionar", command=select_index)
    btnselect.pack()
    indices1= select_index()

    c_cont5 = LabelFrame(select_cont)              #-------------------------
    c_cont5.pack(padx=PAD, pady=PAD, side=LEFT)
    ADIm5_lab = Label(c_cont5, text="ADIm5  ")
    ADIm5_lab.pack(side=BOTTOM)
    ADIm4_lab = Label(c_cont5, text="ADIm4  ")
    ADIm4_lab.pack(side=BOTTOM)
    ADIm3_lab = Label(c_cont5, text="ADIm3  ")
    ADIm3_lab.pack(side=BOTTOM)
    ADIm2_lab = Label(c_cont5, text="ADIm2  ")
    ADIm2_lab.pack(side=BOTTOM)
    ADIm1_lab = Label(c_cont5, text="ADIm1  ")
    ADIm1_lab.pack(side=BOTTOM)
    RMS_lab = Label(c_cont5, text="RMS     ")
    RMS_lab.pack(side=BOTTOM)                    #-------------------------

    c_cont6 = LabelFrame(select_cont)            #-------------------------
    c_cont6.pack(padx=PAD, pady=PAD, side=LEFT)
    ADIm11_lab = Label(c_cont6, text="ADIm11")
    ADIm11_lab.pack(side=BOTTOM)
    ADIm10_lab = Label(c_cont6, text="ADIm10")
    ADIm10_lab.pack(side=BOTTOM)
    ADIm9_lab = Label(c_cont6, text="ADIm9")
    ADIm9_lab.pack(side=BOTTOM)
    ADIm8_lab = Label(c_cont6, text="ADIm8")
    ADIm8_lab.pack(side=BOTTOM)
    ADIm7_lab = Label(c_cont6, text="ADIm7")
    ADIm7_lab.pack(side=BOTTOM)
    ADIm6_lab = Label(c_cont6, text="ADIm6")
    ADIm6_lab.pack(side=BOTTOM)                  #-------------------------

    # Frame para configuración de PSD
    psd_cont = LabelFrame(conf_cont, text=" PSD ")
    psd_cont.pack(padx=PAD, pady=PAD,side=LEFT)
    espaciador_cont = LabelFrame(psd_cont)                                                            
    espaciador_cont.pack(padx=PAD, pady=PAD, side=BOTTOM) 
    filt_cont = LabelFrame(psd_cont, text=" Aplicar filtro (Hz) ")
    filt_cont.pack(side=BOTTOM, padx=PAD, pady=PAD)
    fmin_lab = Label(filt_cont, text=" Fmin:   ")
    fmin_lab.grid()
    fmin_entry = Entry(filt_cont, width=12, justify=CENTER)
    fmin_entry.insert(0, "1000")
    fmin_entry.grid(row=0, column=1)
    fmax_lab = Label(filt_cont, text=" Fmax:   ")
    fmax_lab.grid(row=1, column=0)
    fmax_entry = Entry(filt_cont, width=12, justify=CENTER)
    fmax_entry.insert(0, "11250")
    fmax_entry.grid(row=1, column=1)
    espaciador1_cont = LabelFrame(psd_cont)                                                            
    espaciador1_cont.pack(padx=PAD, pady=PAD, side=BOTTOM) 
    filtrosPSD_cont = LabelFrame(psd_cont)                                                            
    filtrosPSD_cont.pack(padx=PAD, pady=PAD, side=BOTTOM) 
    win_lab = Label(filtrosPSD_cont, text="Tamaño ventana:")
    win_lab.pack(side=LEFT)
    win_entry = Entry(filtrosPSD_cont, width=6, justify=CENTER)
    win_entry.insert(0, "512")
    win_entry.pack(side=LEFT) 
   

    cambio_descriptor()

    # Frame para configuración de Filtros
    filter_cont = LabelFrame(conf_cont, text="Filtros (Hz)")
    filter_cont.pack(side=LEFT, padx=PAD, pady=PAD)
    fcl_lab = Label(filter_cont, text="Fcl:")
    fcl_lab.grid()
    fcl_entry = Entry(filter_cont, width=8, justify=CENTER)
    fcl_entry.insert(0, "500")
    fcl_entry.grid(row=0, column=1)
    fch_lab = Label(filter_cont, text="Fch:")
    fch_lab.grid(row=1, column=0)
    fch_entry = Entry(filter_cont, width=8, justify=CENTER)
    fch_entry.insert(0, "12000")
    fch_entry.grid(row=1, column=1)

    seleccionar_filtro()
    
    #Frame ver
    lblindex=Label(select_cont)
    lblindex.pack()
    
    # Frame para carpeta de salida
    scarp_cont = LabelFrame(ven_pri, text=" Carpeta de Salida ")
    scarp_cont.pack(fill=X, side=TOP, padx=PAD, pady=PAD)
    sal_entry = Entry(scarp_cont, width=65)
    sal_entry.pack(side=LEFT)
    buscars_bot = Button(scarp_cont, text="Buscar...", command=lambda: escoger_carpeta(buscars_bot))
    buscars_bot.pack(expand=True)

    # Parámetros de Salida
    sal_cont = LabelFrame(ven_pri)
    sal_cont.pack(fill=X, padx=PAD, pady=PAD)
    nom_lab = Label(sal_cont, text="Nombre de las Salidas:")
    nom_lab.pack(side=LEFT)
    nom_entry = Entry(sal_cont, justify=CENTER)
    nom_entry.insert(0, "Salida")
    nom_entry.pack(side=LEFT)
    cor_bot = Button(sal_cont, text="Iniciar", width=30,
                     command= lambda : ejecutar_programa(avance, param, salida, malas, fin_proc, leer_excel, procesos, mensajes))
    cor_bot.pack(expand=True)

    # Label de Progreso
    prog_cont = LabelFrame(ven_pri, text="Progreso")
    prog_cont.pack(fill=X, padx=PAD, pady=PAD, ipady=PAD)
    prog_bar = Progressbar(prog_cont, orient="horizontal", mode="indeterminate")
    prog_bar.pack(fill=X, padx=PAD)
    ven_pri.protocol("WM_DELETE_WINDOW", lambda : salir(procesos))
    ven_pri.mainloop()

#--------------------------------------------- Fin Interfaz Gráfica ---------------------------------------------------#
