import pyvisa as visa
from io import BytesIO
from PIL import Image
import sys, subprocess


def openImage(path):
    imageViewerFromCommandLine = {'linux':'xdg-open',
                                  'win32':'explorer',
                                  'darwin':'open'}[sys.platform]
    subprocess.run([imageViewerFromCommandLine, path])

visaResourceAddr = 'GPIB::6::INSTR'

is_useInkSaver = False
# Inksaver is for TDS2000, TDS1000B, TDS2000B, and TPS2000 Series Only.

# tested on TDS1002 with TDS2CMAX
rm = visa.ResourceManager()
scope = rm.open_resource(visaResourceAddr)
print(scope.query('*IDN?'))
# scope.write('AUTOSET EXEC')
print(scope.write("HARDCOPY:PORT GPIB"))

# if is_useInkSaver:
#     scope.write("HARDCopy:INKSaver ON")
# else:
#     scope.write("HARDCopy:INKSaver OFF")

scope.write("HARDCOPY START")
img_rawdata = scope.read_raw()
print(img_rawdata)

image_io = BytesIO(img_rawdata)
img = Image.open(image_io)
img.save('GotScreenShot.png')
openImage('GotScreenShot.png')