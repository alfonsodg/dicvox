import datetime
import logging
import sys
import PySimpleGUI as sg
import pickledb
import json
import csv
import os
from dateutil.relativedelta import relativedelta
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import generate_uid
from PIL import Image
import numpy as np
from pydicom import dcmread
from pynetdicom import AE, debug_logger


def get_platform():
    platforms = {
        'linux': 'Linux',
        'linux1': 'Linux',
        'linux2': 'Linux',
        'darwin': 'OS X',
        'win32': 'Windows'
    }
    if sys.platform not in platforms:
        return sys.platform

    return platforms[sys.platform]


logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG, filename='dicvox.log')

debug_logger()

SERVICES = {}
MODALITIES = {}
PUBLIC_IP = ''
BASE_IP = ''

with open('config.json') as json_data_file:
    data = json.load(json_data_file)

PUBLIC_IP = data["future1"]
BASE_IP = data["future2"]

with open('services.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        SERVICES[row[0]] = row[1]

with open('modalities.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        MODALITIES[row[0]] = row[1]

platform = get_platform()
if platform == 'Windows':
    DESTINATION_DIR = "C:\\studies\\"
    OS_SLASH = '\\'
else:
    DESTINATION_DIR = "/home/alfonsodg/testdicom/"
    OS_SLASH = "/"

INSTITUTION_NAME = 'CONRAD'
USER_NAME = 'Alfonso de la Guarda'
PACS_IP = '127.0.0.1'
PACS_AE = 'CONRAD'
PACS_PORT = '11112'
TODAY = datetime.datetime.now().date()

db = pickledb.load('dicvox.db', False)

tmp = db.get('INSTITUTION_NAME')
if tmp:
    INSTITUTION_NAME = tmp
else:
    db.set('INSTITUTION_NAME', INSTITUTION_NAME)
tmp = db.get('USER_NAME')
if tmp:
    USER_NAME = tmp
else:
    db.set('USER_NAME', USER_NAME)
tmp = db.get('DESTINATION_DIR')
if tmp:
    DESTINATION_DIR = tmp
else:
    db.set('DESTINATION_DIR', DESTINATION_DIR)
tmp = db.get('PACS_IP')
if tmp:
    PACS_IP = tmp
else:
    db.set('PACS_IP', PACS_IP)
tmp = db.get('PACS_AE')
if tmp:
    PACS_AE = tmp
else:
    db.set('PACS_AE', PACS_AE)
    print(PACS_AE)
tmp = db.get('PACS_PORT')
if tmp:
    PACS_PORT = tmp
else:
    db.set('PACS_PORT', PACS_PORT)
db.dump()


def settings_window():
    layout = [
        [sg.Text('Institution Name:')],
        [sg.InputText(
            default_text=INSTITUTION_NAME,
            key='-INSNAM-',
            # size=(100, 30),
            background_color='white',
            text_color='#2687FB',
            enable_events=True)],
        [sg.Text('User Name:')],
        [sg.InputText(
            default_text=USER_NAME,
            key='-USRN-',
            # size=(100, 30),
            background_color='white',
            text_color='#2687FB',
            enable_events=True)],
        [sg.Text('Destination Dir:')],
        [sg.InputText(
            default_text=DESTINATION_DIR,
            key='-DDIR-',
            # size=(200, 30),
            background_color='white',
            text_color='#2687FB',
            enable_events=True)],
        [sg.Text('PACS IP:')],
        [sg.InputText(
            default_text=PACS_IP,
            key='-PACSIP-',
            # size=(100, 30),
            background_color='white',
            text_color='#2687FB',
            enable_events=True)],
        [sg.Text('PACS AE:')],
        [sg.InputText(
            default_text=PACS_AE,
            key='-PACSAE-',
            # size=(100, 30),
            background_color='white',
            text_color='#2687FB',
            enable_events=True)],
        [sg.Text('PACS PORT:')],
        [sg.InputText(
            default_text=PACS_PORT,
            key='-PACSPORT-',
            # size=(100, 30),
            background_color='white',
            text_color='#2687FB',
            enable_events=True)],
        [sg.Button('Save'),
         sg.Button('Exit')]
    ]
    window = sg.Window('Settings', layout)

    while True:  # The Event Loop
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
        elif event == 'Save':
            insnam = values['-INSNAM-']
            username = values['-USRN-']
            ddir = values['-DDIR-']
            pacsip = values['-PACSIP-']
            pacsae = values['-PACSAE-']
            pacsport = values['-PACSPORT-']
            db.set('USER_NAME', username)
            db.set('DESTINATION_DIR', ddir)
            db.set('INSTITUTION_NAME', insnam)
            db.set('PACS_IP', pacsip)
            db.set('PACS_AE', pacsae)
            db.set('PACS_PORT', pacsport)
            db.dump()
            sg.popup("Configuration Saved!")
            break
    window.close()


def dicom_send(dicom_file, context):
    ae = AE()
    ae.ae_title = 'CONRADCL'
    ae.add_requested_context(context)
    ds = dcmread(dicom_file)
    assoc = ae.associate(PACS_IP, int(PACS_PORT), ae_title=PACS_AE)
    status = 0
    if assoc.is_established:
        status = assoc.send_c_store(ds)

        # Check the status of the storage request
        if status:
            # If the storage request succeeded this will be 0x0000
            print('C-STORE request status: 0x{0:04x}'.format(status.Status))
            status = 1
        else:
            print('Connection timed out, was aborted or received invalid response')

        # Release the association
        assoc.release()

    else:
        print('Association rejected, aborted or never connected')
    if status == 1:
        sg.popup("DICOM file sucessfully sended!")
    else:
        sg.popup("Error in the sending process, check the logs!")
    return status


def dicom_process(file_name, modality, filetype, patname, patid, gender, bdate):
    # https://dicom.nema.org/medical/dicom/current/output/chtml/part06/chapter_6.html
    # http://dicomlookup.com/default.asp
    dir_location = os.path.dirname(file_name)
    dicom_new_file = dir_location + OS_SLASH + str(generate_uid()) + '.dcm'
    dt = datetime.datetime.now()
    date_str = dt.strftime('%Y%m%d')
    time_str = dt.strftime('%H%M%S')
    jpg_image = Image.open(file_name)
    ds = Dataset()
    ds.file_meta = Dataset()
    ds.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
    ds.file_meta.MediaStorageSOPClassUID = SERVICES[filetype]
    ds.file_meta.MediaStorageSOPInstanceUID = generate_uid()
    ds.file_meta.ImplementationClassUID = generate_uid()
    ds.SOPClassUID = SERVICES[filetype]
    ds.SOPInstanceUID = ds.file_meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.PatientName = patname
    ds.PatientID = patid
    ds.add_new(0x00080060, 'CS', MODALITIES[modality])
    ds.add_new(0x00100030, 'DA', bdate)
    ds.add_new(0x00100040, 'CS', gender)
    ds.add_new(0x00080080, 'LO', INSTITUTION_NAME)
    ds.ContentDate = date_str
    ds.ContentTime = time_str
    ds.add_new(0x00080020, 'DA', date_str)
    ds.add_new(0x00080021, 'DA', date_str)
    ds.add_new(0x00080022, 'DA', date_str)
    ds.add_new(0x00080030, 'TM', time_str)
    ds.add_new(0x00080031, 'TM', time_str)
    ds.add_new(0x00080032, 'TM', time_str)
    ds.PlanarConfiguration = 0
    ds.NumberOfFrames = 1
    ds.is_little_endian = True
    ds.is_implicit_VR = False
    if jpg_image.mode == 'L':
        np_image = np.array(jpg_image.getdata(), dtype=np.uint8)
        ds.Rows = jpg_image.height
        ds.Columns = jpg_image.width
        ds.PhotometricInterpretation = "MONOCHROME1"
        ds.SamplesPerPixel = 1
        ds.BitsStored = 8
        ds.BitsAllocated = 8
        ds.HighBit = 7
        ds.PixelRepresentation = 0
        ds.PixelData = np_image.tobytes()
        ds.save_as(dicom_new_file, write_like_original=False)
    elif jpg_image.mode == 'RGBA' or jpg_image.mode == 'RGB':
        np_image = np.array(jpg_image.getdata(), dtype=np.uint8)[:, :3]
        ds.Rows = jpg_image.height
        ds.Columns = jpg_image.width
        ds.PhotometricInterpretation = "RGB"
        ds.SamplesPerPixel = 3
        ds.BitsStored = 8
        ds.BitsAllocated = 8
        ds.HighBit = 7
        ds.PixelRepresentation = 0
        ds.PixelData = np_image.tobytes()
        ds.save_as(dicom_new_file, write_like_original=False)
    else:
        sg.popup("No compatible Image File, Try with Another")
        return
    answer = sg.popup_yes_no('Send to PACS?')
    if answer == 'Yes':
        dicom_send(dicom_new_file, SERVICES[filetype])
    return


def select_file():
    storage = SERVICES.keys()
    modalities = MODALITIES.keys()
    gender = ['MALE', 'FEMALE']
    year = datetime.date.today().year
    current_time_date = datetime.datetime.now() - relativedelta(years=18)
    default_date = current_time_date.strftime('%Y-%m-%d')
    layout = [
        [sg.Text('Modality')],
        [sg.Input(size=(20, 1), enable_events=True, key='-MINPUT-')],
        [sg.Listbox(modalities, size=(80, 4), highlight_background_color="#FF0000", enable_events=True, key='-MODAL-')],
        [sg.Text('Media Storage UID')],
        [sg.Input(size=(20, 1), enable_events=True, key='-INPUT-')],
        [sg.Listbox(storage, size=(80, 4), highlight_background_color="#FF0000", enable_events=True, key='-LIST-')],
        [sg.Text('Image')],
        [sg.Combo(sg.user_settings_get_entry('-filenames-', []),
                  default_value=sg.user_settings_get_entry('-last filename-', ''), size=(80, 1),
                  key='-FILENAME-'),
         sg.FileBrowse(file_types=(("Image Files", "*.jpg"),))],
        [sg.Text('Patient Name:')],
        [sg.InputText(
            default_text='',
            key='-PATNAME-'
            # size=(100, 30),
        )],
        [sg.Text('Patient ID:')],
        [sg.InputText(
            default_text='',
            key='-PATID-'
            # size=(100, 30)
        )],
        [sg.Text('Gender:')],
        [sg.Listbox(gender, size=(10, 2), highlight_background_color="#FF0000",
                    key='-GENDER-')],
        [sg.Text('Birth Date:')],
        [sg.Input(key='-BDATE-', size=(20, 1), default_text=default_date),
         sg.CalendarButton('Format AAAA-MM-DD', target='-BDATE-', format='%Y-%m-%d',
                           default_date_m_d_y=(1, None, year - 18), )],
        [sg.Button('Go'),
         sg.Button('Exit')]]

    window = sg.Window('Dicvox', layout)
    modality = ''
    filetype = ''

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        if values['-LIST-'] != '':
            filetype = values['-LIST-']
        if values['-MODAL-'] != '':
            modality = values['-MODAL-']
        if values['-INPUT-'] != '':
            search = values['-INPUT-']
            new_values = [x for x in storage if search in x]
            window['-LIST-'].update(new_values)
            window['-LIST-'].set_value(filetype)
        else:
            window['-LIST-'].update(storage)
            if values['-LIST-'] != '':
                window['-LIST-'].set_value(filetype)
        if values['-MINPUT-'] != '':
            search = values['-MINPUT-']
            new_values = [x for x in modalities if search in x]
            window['-MODAL-'].update(new_values)
            window['-MODAL-'].set_value(modality)
        else:
            window['-MODAL-'].update(modalities)
            if values['-MODAL-'] != '':
                window['-MODAL-'].set_value(modality)
        if event == 'Go':
            sg.user_settings_set_entry('-filenames-',
                                       list(set(sg.user_settings_get_entry('-filenames-', []) + [
                                           values['-FILENAME-'], ])))
            sg.user_settings_set_entry('-last filename-', values['-FILENAME-'])
            modality = values['-MODAL-'][0]
            filetype = values['-LIST-'][0]
            filename = values['-FILENAME-']
            patname = values['-PATNAME-']
            patid = values['-PATID-']
            gender = values['-GENDER-'][0][0]
            bdate = values['-BDATE-'].replace('-', '')
            if filetype == '' or filename == '' or patname == '' or patid == '' or gender == '' or bdate == '' \
                    or modality == '':
                sg.popup("Please, Fill All the DATA Fields!!!!")
            dicom_process(filename, modality, filetype, patname, patid, gender, bdate)
    window.close()


def system_tray():
    layout = [
        [sg.Button('Query')],
        [sg.Button('Configuration')],
        [sg.Button('Exit')]]

    # Create the Window
    window = sg.Window('Dicvox', layout, size=(200, 250))

    while True:
        event, values = window.read()
        menu_item = event
        if menu_item == 'Exit':
            break
        if menu_item.startswith('Query'):
            select_file()
        elif menu_item == 'Configuration':
            settings_window()


system_tray()
