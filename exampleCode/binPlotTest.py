from PIL import Image
from io import BytesIO
import numpy as np
import cv2
#from matplotlib import pyplot as plt

with open("../img/test.png", 'rb') as f:
    f_bin = f.read()
    f.close()
    file_jpgdata = BytesIO(f_bin)
    dt = Image.open(file_jpgdata)
    #dt.show()

I = np.asarray(dt)
print(I.shape)
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

cv2.imshow("Shot", img_text)
cv2.waitKey()
cv2.destroyAllWindows()
