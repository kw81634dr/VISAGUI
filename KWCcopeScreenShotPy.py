from datetime import datetime # std library
import pyvisa as visa # https://pyvisa.readthedocs.org/en/stable/
import os
from pathlib import Path
from tkinter import *
from tkinter import ttk
from tkinter import filedialog

gui = Tk()
gui.geometry("450x100")
gui.title("DPO Scope Screen Capture v0.2 (testOnly)")


def getScreenShotFromScope(path):
    # Modify the following lines to configure this script for your instrument
    #==============================================
    visaResourceAddr = 'GPIB::6::INSTR'
    if path == '':
        fileSavePathonPC = Path(os.getcwd())
    else:
        fileSavePathonPC = Path(path)
    #==============================================
    dt = datetime.now()

    rm = visa.ResourceManager()
    scope = rm.open_resource(visaResourceAddr)
    scope.timeout = 8000
    print(scope.query('*IDN?'))
    scope.write("HARDCopy:PORT FILE")
    scope.write("HARDCOPY:PALETTE COLOR")
    scope.write("SAVe:IMAGe:FILEFormat PNG")
    scope.write("SAVe:IMAGe:INKSaver OFF")
    ## Notice: CANNOT access C root directly
    scope.write('FILESystem:READFile \'C:\Temp\KW.png\'')
    scope.write('HARDCopy:FILEName  \'C:\Temp\KW.png\'')
    scope.write("HARDCopy STARt")
    #scope.write('*OPC?')
    scope.write('FILES:READF \'C:\Temp\KW.png\'')
    imgData = scope.read_raw(1024*1024)
    print(imgData)
    scope.write('FILESystem:DELEte \'C:\Temp\KW.png\'')

    # Generate a filename based on the current Date & Time
    fileName = dt.strftime("DSO_%Y%m%d_%H%M%S.png")
    print(fileSavePathonPC + fileName)
    imgFile = open(fileSavePathonPC + fileName, "wb")
    imgFile.write(imgData)
    imgFile.close()
    scope.close()
    rm.close()
    text = str(fileSavePathonPC + fileName)
    status_var.set(text)


    #plt.imshow(imgData)
    #plt.show()
    #plt.imsave('filename.png', np.array(imgData).reshape(1024,1024))


def getFolderPath():
    folder_selected = filedialog.askdirectory()
    folderPath.set(folder_selected)
    folderGlobe = folderPath.get()

def getFilePath():
    filename_prompt = filedialog.asksaveasfilename()
    finlename_prompt.set(filename_prompt)


def doStuff():
    folder = folderPath.get()
    print("Doing stuff with folder", folder)
    getScreenShotFromScope(folder)

finlename_prompt = StringVar()
folderPath = StringVar()
status_var = StringVar()
status_var.set("Waiting for User")
#a = Label(gui ,text="Destination Folder")
#a.grid(row=0,column = 0)

E = Entry(gui,textvariable=folderPath,width="50")
E.grid(row=0,column=0)

btnFind = ttk.Button(gui, text="Prompt (P)",command=getFolderPath)
btnFind.grid(row=0,column=1,padx=5,pady=5,ipady=1)
gui.bind('p', lambda event: getFolderPath())

c = ttk.Button(gui ,text="Capture (Enter)", command=doStuff)
c.grid(row=1,column=1,padx=1,pady=1,ipady=5)
gui.bind('<Return>', lambda event: getScreenShotFromScope(folderPath.get()))

label = Label(gui, text = "Prompt directory or leave it blank to save in current directory.\nMake sure the GPIB Address of your scope has set to 6.")
label.grid(row=1,column=0,padx=1,pady=1,ipady=3)

statusbar = Label(gui, textvariable=status_var, bd=1, relief=SUNKEN, anchor=W)
statusbar.grid(row=2, column=0, columnspan=2, sticky='we')
gui.update_idletasks()


gui.mainloop()


