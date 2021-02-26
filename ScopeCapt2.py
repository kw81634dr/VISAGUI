from datetime import datetime # std library
import pyvisa as visa # https://pyvisa.readthedocs.org/en/stable/
import os

from tkinter import *
from tkinter import ttk
from tkinter import filedialog

class MainClass:

    def __init__(self, parent, *args, **kwargs):
        frame = Frame(parent)
        frame.pack()

        self.visa_addr = StringVar()
        self.save_path = StringVar()
        self.status_var = StringVar()
        self.IDNofScope = StringVar()

        self.visa_addr.set('GPIB::6::INSTR')
        self.status_var.set("Waiting for User")
        self.save_path.set(os.getcwd())
        self.IDNofScope.set('')

        self.dt = datetime.now()
        self.visa_timeout_duration = 8000    # in ms

        E = Entry(self, textvariable=self.save_path, width="50")
        E.grid(row=0, column=0)

        btn_prompt = ttk.Button(self, text="Prompt (P)", command=self.prompt_path())
        btn_prompt.grid(row=0, column=1, padx=5, pady=5, ipady=1)
        self.bind('p', lambda event: self.prompt_path())

        btn_capure = ttk.Button(self, text="Capture (Enter)", command=self.btn_clicked())
        btn_capure.grid(row=1, column=1, padx=1, pady=1, ipady=5)
        self.bind('<Return>', lambda event: self.get_shot_scope(self.save_path.get()))

        label = Label(self,
                      text="Prompt directory or leave it blank to save in current directory.\nMake sure the GPIB Address of your scope has set to 6.")
        label.grid(row=1, column=0, padx=1, pady=1, ipady=3)

        statusbar = Label(self, textvariable=self.status_var, bd=1, relief=SUNKEN, anchor=W)
        statusbar.grid(row=2, column=0, columnspan=2, sticky='we')

    def get_shot_scope(self):
        rm = visa.ResourceManager()
        scope = rm.open_resource(self.visa_addr)
        scope.timeout = self.visa_timeout_duration
        scopeIDN = scope.query('*IDN?')
        self.IDNofScope.set(scopeIDN)

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
        save_path_default =  self.save_path + self.dt.strftime("DSO_%Y%m%d_%H%M%S.png")
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
        self.save_path.set(folder_selected)
        folderGlobe = self.save_path.get()

    def btn_clicked(self):
        folder = self.save_path.get()
        print("Doing stuff with folder", folder)
        self.get_shot_scope()


def main():
    root = Tk()
    gui = MainClass(root)
    gui(root).geometry("450x100")
    gui(root).title("DPO Scope Screen Capture v0.2 (testOnly)")
    gui.update_idletasks()

    gui.mainloop()


if __name__ == "__main__":
    main()