from PIL import Image
from io import BytesIO
import numpy as np
import cv2
#from matplotlib import pyplot as plt

with open("test.png", 'rb') as f:
    f_bin = f.read()
    f.close()
    file_jpgdata = BytesIO(f_bin)
    dt = Image.open(file_jpgdata)
    #dt.show()

I = np.asarray(dt)
print(I.shape)
I_cv2 = cv2.cvtColor(I, cv2.COLOR_RGB2BGR)
cv2.imshow("Shot", I_cv2)
cv2.waitKey()
cv2.destroyAllWindows()
