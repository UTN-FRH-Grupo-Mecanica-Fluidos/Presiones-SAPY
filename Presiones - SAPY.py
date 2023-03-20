import os
import base64
from functions import *

# Carga de logo e icono
from logo import *
from icono import *

# -----------Icono-----------
icon_bytes = base64.b64decode(icon)

# -------------Layout-------------
# Theme
sg.theme('SystemDefaultForReal')

# Layout
# Armado del frame del la configuracion CSV
frame = [[sg.Radio("Automatico (solo Windows)", "grupo-CSV")],
         [sg.Radio("Separador de listas: COMA - Simbolo decimal: PUNTO", "grupo-CSV", default=True)],
         [sg.Radio("Separador de listas: PUNTO Y COMA - Simbolo decimal: COMA", "grupo-CSV")]]

# Armado del logo junto al nivel de confianza.
cola = [[sg.Image(source=logo, subsample=3, tooltip='Laboratorio de Aerodinamica y Fluidos')]]
colb = [[sg.Text('Nivel de confianza:'),
         sg.Combo(values=['68%', '95%', '99%'], key='-CONF-', default_value=['95%'], s=(5, 1),
                  readonly=True, background_color='white')]]

# Armado del frame del autozero
frama_a = [[sg.Combo(values=[], key='-CERO-', enable_events=True, expand_x=True)],
           [sg.Checkbox('Informar el resultado del autozero', key='-INFAUTOZERO-')]]

# Coluna izquierda
col1 = [[sg.Text("Ingresar carpeta de trabajo")],
        [sg.Input(key='-FOLDER-', enable_events=True, size=(50, 1)), sg.FolderBrowse(button_text='Buscar')],
        [sg.Frame('Elegir archivo de referencia del cero (Autozero)', frama_a, vertical_alignment='center',
                  pad=(0, (8, 4)), expand_x=True)],
        [sg.Frame('Formato de salida del CSV', frame, vertical_alignment='center', expand_y=True)],
        [sg.Column(cola), sg.Column(colb, vertical_alignment='top')]]

# Coluna derecha
col2 = [[sg.Text('Seleccione los archivos a procesar')], [sg.Button('Todos', key='-TODOS-', size=(7, 1)),
                                                          sg.Button('Ninguno', key='-NINGUNO-', size=(7, 1))],
        [sg.Listbox(values=['No hay archivos CSV'], key='-FILE LIST-', size=(35, 16), enable_events=True,
                    select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED)],
        [sg.Button('Procesar', key='-PROCESS-', enable_events=True, font=("Arial", 13), size=(9, 1),
                   pad=(10, (10, 5))), sg.Button('Salir', font=("Arial", 13), size=(9, 1), pad=(10, (10, 5))),
         sg.Push()]]

layout = [[sg.Column(col1), sg.Column(col2)]]

# Crear la interfaz
window = sg.Window("Procesamiento de presiones – SAPY - Version 1.0", layout, resizable=False, icon=icon_bytes)

# Inicializacion de variables. Evita errores en el loop.
fnames = ['No hay archivos CSV']
vref = []

# -------------Loop de evento-------------
while True:
    event, values = window.read()
    # Lectura de la carpeta de trabajo.
    if event == '-FOLDER-':
        folder = values['-FOLDER-']
        try:  # Existe la carpeta sino devuelve listado vacio de archivos
            file_list = os.listdir(folder)
        except Exception as e:
            print(e)
            file_list = []
        # Busca en la carpeta de trabajo los archivos que sean solo CSV.
        fnames = [f for f in file_list if os.path.isfile(
            os.path.join(folder, f)) and f.lower().endswith(".csv")]
        # Eliminar del analisis los archivos de salida.
        if "presiones.csv" in fnames:
            fnames.remove("presiones.csv")
        if "incertidumbre.csv" in file_list:
            fnames.remove("incertidumbre.csv")
        # Si mo hay archivos CSV en la carpeta devuelve advertencia en el ListBox.
        if not fnames:
            fnames = ['No hay archivos CSV']
        # Actualiza los nombres de los archivos al ListBox y al Combo.
        window['-FILE LIST-'].update(fnames)
        window['-CERO-'].update(values=fnames)

    # Selecciona todos los archivos del listado.
    if event == '-TODOS-':
        window['-FILE LIST-'].update(set_to_index=[i for i in range(len(fnames))])

    # Deselecciona todos los archivos del listado
    if event == '-NINGUNO-':
        window['-FILE LIST-'].update(set_to_index=[])

    # Boton Procesar
    if event == '-PROCESS-':
        can_process = True  # Flag de que no existen errores.
        # Ingreso de datos desde la interfaz grafica.
        # Nombre de la carpeta de trabajo
        path_folder = values['-FOLDER-']
        # Nombre del archivo del cero referencia
        cero_file = values['-CERO-']
        # Formato de salida CSV
        if values[0]:
            option = 0
        elif values[1]:
            option = 1
        else:
            option = 2
        seplist, decsep = formato_csv(option)
        # Nivel de Confianza. Se eligio 68.27%, 95% y 99%. Los que se suelen usar.
        conf_level = values['-CONF-']
        if conf_level == '68%':
            conf_level = float(0.6827)
        elif conf_level == '95%':
            conf_level = float(0.95)
        elif conf_level == '99%':
            conf_level = float(0.99)

        # Comprobacióm de errores
        #  La carpeta no existe
        if not os.path.exists(path_folder):
            error_popup('La carpeta seleccionada no existe')
            can_process = False
        #  No se seleccionaron archivos. Que no sea vacio ni con el mensaje del listbox.
        if (values['-FILE LIST-'] == [] or values['-FILE LIST-'] == ['No hay archivos CSV']) and can_process:
            error_popup('No se selecciono ningun archivo')
            can_process = False
        if cero_file == '' and can_process:
            error_popup('No se selecciono el archivo de referencia')
            can_process = False

        # Calculo de los voltajes de referencia. Ante falla da aviso.
        if can_process:  # Si no hubo errores se continua. Similar a can_process==True.
            try:  # Prueba procesar el archivo sino genera mensaje de error.
                path = path_folder + '/' + cero_file
                vref = reference_voltage(path)
            except Exception as e:
                print(e)
                # Aviso de cero no procesable
                error_popup('El archivo de referencia cero no es procesable')
                can_process = False

        # Avisa sino es posible grabar los archivos de salida.
        if can_process:
            try:  # Prueba grabar el archivo sino genera mensaje de error.
                with open(path_folder + '/incertidumbre.csv', "w", newline='') as f:
                    writer = csv.writer(f, delimiter=seplist)
            except Exception as e:
                print(e)
                if can_process:
                    error_popup('El archivo incertidumbre.csv se encuentra abierto, cierrelo e intente de nuevo')
                    can_process = False
            try:  # Prueba grabar el archivo sino genera mensaje de error.
                with open(path_folder + '/presiones.csv', "w", newline='') as f:
                    writer = csv.writer(f, delimiter=seplist)
            except Exception as e:
                print(e)
                if can_process:  # Evita que se generen dos popup de error de ambos archivos fallidos.
                    error_popup('El archivo presiones.csv se encuentra abierto, cierrelo e intente de nuevo')
                    can_process = False

        # Si no hay errores se prosigue
        if can_process:
            # Armado listado de archivos seleccionados
            file_list = values['-FILE LIST-']
            file_path_list = []
            for i in file_list:
                file_path_list.append(path_folder + '/' + i)

            # Procesamiento de los archivos
            save_pressure = []  # Inicializo variable donde se guardan los datos de presion.
            save_uncert = []  # Inicializo variable donde se guardan los datos de incertidumbre.
            error_files_list = []  # Inicializo variable donde se guardan los archivos con fallas.
            for i in range(len(file_path_list)):
                data = []  # Reinicio de la variable donde se guardan los datos del CSV.
                # Se abre cada archivo que figura en el listado.
                with open(file_path_list[i]) as csv_file:
                    csv_reader = csv.reader(csv_file, delimiter=';')
                    # Extraigo todas las filas de un archivo y se lo procesa.
                    for csv_row in csv_reader:
                        data.append(csv_row)
                    try:
                        # Variable buffer que evita informacion redundante en "save_uncert"
                        save_buffer_pressure, save_buffer_uncert = data_process(data, vref, file_list[i], conf_level)
                        save_pressure.extend(save_buffer_pressure)  # Union de los datos procesados de cada archivo.
                        save_uncert.extend(save_buffer_uncert)  # Procesamiento de la incertidumbre de las presiones.
                    except Exception as e:
                        print(e)
                        error_files_list.append(file_list[i])

            # Guardado de los archivos
            save_csv_pressure(save_pressure, path_folder, seplist, decsep)
            save_csv_incert(save_uncert, conf_level, path_folder, seplist, decsep)
            info_popup('Los archivos de salida presiones.csv y incertidumbre.csv se guardaron con exito')

            # Listado de los valores de voltaje del autozero. Se activa for el checkbox.
            if values['-INFAUTOZERO-'] == True:
                values_vref = []
                for toma_volt, value in vref.items():
                    values_vref.append(str(toma_volt) + ': {}'.format(round(value, 4)))
                autozero_popup('\n'.join(values_vref))

            if error_files_list:
                # Aviso de archivos no procesados
                error_files_popup('\n'.join(error_files_list))

    # Salida del programa
    if event == "Salir" or event == sg.WIN_CLOSED:
        break

window.close()