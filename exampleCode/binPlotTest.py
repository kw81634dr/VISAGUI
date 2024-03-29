from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from io import BytesIO
import numpy as np
import cv2
import webbrowser

import sys
import subprocess

#from matplotlib import pyplot as plt

def openImage(path):
    imageViewerFromCommandLine = {'linux':'xdg-open',
                                  'win32':'explorer',
                                  'darwin':'open'}[sys.platform]
    subprocess.run([imageViewerFromCommandLine, path])

with open("../img/scrshot/P1V0.png", 'rb') as f:
    f_bin = f.read()
    f.close()
    file_jpgdata = BytesIO(f_bin)
    # print(file_jpgdata.getvalue())
    # print(file_jpgdata.getvalue()[2 + 9:])
    dt = Image.open(file_jpgdata)
    I = np.asarray(dt)


use_OpenCV = True

if use_OpenCV:
    # print(I.shape)
    I_cv2 = cv2.cvtColor(I, cv2.COLOR_RGB2BGR)

    font = cv2.FONT_HERSHEY_DUPLEX
    font_size = 0.44
    font_color = (255, 255, 255)
    font_thickness = 1
    text = 'Jitter_CPU1_ABCD_Default_20%Load'
    height, width, depth = I_cv2.shape
    cv2.rectangle(I_cv2, (width-width+677, height-height), (width, height-height+31), (0, 0, 0), -1)
    img_text = cv2.putText(I_cv2, text, (width-width+677, height-height+20), font, font_size, font_color, font_thickness,
                           cv2.LINE_AA)

    # cv2.imshow("Shot", img_text)
    # cv2.waitKey()
    # cv2.destroyAllWindows()
    cv2.imwrite('sample-out.png', img_text)
    openImage('sample-out.png')


else:
    img = Image.fromarray(I)
    draw = ImageDraw.Draw(img)
    # font = ImageFont.truetype(<font-file>, <font-size>)
    font = ImageFont.load_default()
    # font = ImageFont.truetype("/Users/kevin/Downloads/Space_Mono/SpaceMono-Bold.ttf", 16)
    # draw.text((x, y),"Sample Text",(r,g,b))
    # draw.rectangle((0, 0, 1023, 31), fill=(84, 104, 168))   #Tek Blue
    draw.rectangle((0, 0, 900, 32), fill=(37, 37, 37))
    text_to_overlay = "Kp=44 Kd=50 Jitter Ontime CPU1 2 VDDQ ABCD2 Default 20%Load"
    draw.text((11, 4), text_to_overlay, fill=(255, 165, 55), font=font)
    # img.show()
    img.save('sample-out.png')
    openImage('sample-out.png')

