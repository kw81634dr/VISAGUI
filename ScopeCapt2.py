from datetime import datetime # std library
import pyvisa as visa # https://pyvisa.readthedocs.org/en/stable/
import os
from pathlib import Path

import tkinter as tk
from tkinter import Entry

# https://pythonguides.com/python-tkinter-menu-bar/
# https://zetcode.com/tkinter/layout/
# https://www.pythontutorial.net/tkinter/tkinter-grid/


class App:
    # Define settings upon initialization.
    def __init__(self, master):
        self.master = master
        self.frame = tk.Frame(self.master)


        self.master.title("KW Scope Capture")

        self.visa_address = tk.StringVar()
        self.status_var = tk.StringVar()
        self.path_var = tk.StringVar()
        self.IDN_of_scope = tk.StringVar()

        self.visa_address.set('GPIB::6::INSTR')
        self.status_var.set("Waiting for User")
        self.path_var.set(os.getcwd())
        self.IDN_of_scope.set('')

        self.dt = datetime.now()
        self.visa_timeout_duration = 8000    # in ms


        self.E = tk.Entry(self.frame, textvariable=self.path_var, width="50")
        self.E.grid(row=0, column=0)

        btn_prompt = tk.Button(self.frame, text="Prompt (P)", command=self.prompt_path)
        btn_prompt.grid(row=0, column=1, padx=5, pady=5, ipady=1)
        # self.bind('p', lambda event: self.prompt_path())

        btn_capure = tk.Button(self.frame, text="Capture (Enter)", command=self.btn_clicked)
        btn_capure.grid(row=1, column=1, padx=1, pady=1, ipady=5)
        # self.bind('<Return>', lambda event: self.get_shot_scope(self.path_var.get()))

        label = tk.Label(self.frame,
                      text="Prompt directory or leave it blank to save in current directory.\nMake sure the GPIB Address of your scope has set to 6.")
        label.grid(row=1, column=0, padx=1, pady=1, ipady=3)

        statusbar = tk.Label(self.frame, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        statusbar.grid(row=2, column=0, columnspan=2, sticky='we')

        self.frame.pack()


    def client_exit(self):
        exit()

    def get_shot_scope(self):
        rm = visa.ResourceManager()
        scope = rm.open_resource(self.visa_address.get())
        scope.timeout = self.visa_timeout_duration
        self.IDN_of_scope.set(scope.query('*IDN?'))

        scope.write("HARDCopy:PORT FILE")
        scope.write("HARDCOPY:PALETTE COLOR")
        scope.write("SAVe:IMAGe:FILEFormat PNG")
        scope.write("SAVe:IMAGe:INKSaver OFF")

        # Notice: CANNOT access C Drive root directly
        scope.write('FILESystem:READFile \'C:\Temp\KWScrShot.png\'')
        scope.write('HARDCopy:FILEName  \'C:\Temp\KWScrShot.png\'')
        scope.write("HARDCopy STARt")
        scope.write('*OPC?')
        scope.write('FILES:READF \'C:\Temp\KWScrShot.png\'')

        img_data = scope.read_raw()

        scope.write('FILESystem:DELEte \'C:\Temp\KWScrShot.png\'')

        # Generate a filename based on the current Date & Time
        save_path_default =  self.path_var.get() + self.dt.strftime("DSO_%Y%m%d_%H%M%S.png")
        print("Save Image to ", save_path_default)

        with open(save_path_default, "wb") as imgFile:
            imgFile.write(img_data)
            imgFile.close()
            self.status_var.set(save_path_default)

        scope.close()
        rm.close()

        #plt.imshow(imgData)
        #plt.show()
        #plt.imsave('filename.png', np.array(imgData).reshape(1024,1024))

    def prompt_path(self):
        folder_selected = filedialog.askdirectory()
        self.path_var.set(folder_selected)
        folderGlobe = self.path_var.get()

    def btn_clicked(self):
        folder = self.path_var.get()
        print("Doing stuff with folder", folder)
        self.get_shot_scope()


def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == '__main__':
    main()