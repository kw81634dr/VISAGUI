import pyvisa as visa
from io import BytesIO
from PIL import Image
import sys, subprocess


def openImage(path):
    imageViewerFromCommandLine = {'linux':'xdg-open',
                                  'win32':'explorer',
                                  'darwin':'open'}[sys.platform]
    subprocess.run([imageViewerFromCommandLine, path])

# visaResourceAddr = 'GPIB::6::INSTR'
visaResourceAddr = "USB0::0x0957::0x17A6::MY54310518::INSTR"

is_useInkSaver = False

# tested on TDS1002 with TDS2CMAX
rm = visa.ResourceManager()
scope = rm.open_resource(visaResourceAddr)
scope.timeout = 10000 # in ms, very important, or get VISA_TIMEOUT ERROR
# print(scope.query('*IDN?'))
# scope.write('AUTOSET EXEC')

# configure ink saver (black background as seen on screen)
# scope.write(':STOP; *WAI')

# byteImage = scope.query_binary_values(":DISP:DATA? PNG", datatype='B', container=bytearray)

img_data = scope.query_binary_values(':DISPlay:DATA? PNG', datatype='B', container=bytearray)
print(img_data)

file_png_data = BytesIO(img_data)
I = Image.open(file_png_data)
I.save('GotScreenShot_Key.png')
openImage('GotScreenShot_Key.png')