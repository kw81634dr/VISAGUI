from datetime import datetime # std library
import pyvisa as visa # https://pyvisa.readthedocs.org/en/stable/
import os
from pathlib import Path

import tkinter as tk
from tkinter import ttk, Entry, filedialog

# https://pythonguides.com/python-tkinter-menu-bar/
# https://coderslegacy.com/python/list-of-tkinter-widgets/


class MenuBar(tk.Menu):
    def __init__(self, ws):
        tk.Menu.__init__(self, ws)

        file = tk.Menu(self, tearoff=False)
        file.add_command(label="New")
        file.add_command(label="Open")
        file.add_command(label="Save")
        file.add_command(label="Save as")
        file.add_separator()
        file.add_command(label="Exit", underline=1, command=self.quit)
        self.add_cascade(label="File", underline=0, menu=file)

        edit = tk.Menu(self, tearoff=0)
        edit.add_command(label="Undo")
        edit.add_separator()
        edit.add_command(label="Cut")
        edit.add_command(label="Copy")
        edit.add_command(label="Paste")
        self.add_cascade(label="Edit", menu=edit)

        help = tk.Menu(self, tearoff=0)
        help.add_command(label="About", command=self.about)
        self.add_cascade(label="Help", menu=help)

    def exit(self):
        self.exit

    def about(self):
        messagebox.showinfo('PythonGuides', 'Python Guides aims at providing best practical tutorials')


class App:
    # Define settings upon initialization.
    def __init__(self, master):
        self.master = master

        self.frame = tk.Frame(self.master)

        #self.master.geometry("+%d+%d" % (self.frame.window_start_x, self.frame.window_start_y))
        self.master.title("KW Scope Capture")

        self.target_gpib_address = tk.StringVar()
        self.status_var = tk.StringVar()
        self.path_var = tk.StringVar()
        self.filename_var = tk.StringVar()
        self.IDN_of_scope = tk.StringVar()

        # self.GPIB_list = ['GPIB::6::INSTR']

        self.target_gpib_address.set('GPIB::6::INSTR')
        self.status_var.set("Waiting for User")
        self.path_var.set(os.getcwd())
        self.IDN_of_scope.set('')

        self.dt = datetime.now()
        self.visa_timeout_duration = 5000    # in ms

        colum = 3
        row = 4


        # self.frame.columnconfigure(0, pad=3)
        # self.frame.columnconfigure(1, pad=3)
        # self.frame.columnconfigure(2, pad=3)
        # self.frame.columnconfigure(3, pad=3)
        #
        # self.frame.rowconfigure(0, pad=3)
        # self.frame.rowconfigure(1, pad=3)
        # self.frame.rowconfigure(2, pad=3)
        # self.frame.rowconfigure(3, pad=3)
        # self.frame.rowconfigure(4, pad=3)

        # row 0
        #label_GPIB_address = tk.Label(self.frame, text="GPIB Address")
        #label_GPIB_address.grid(row=0, column=0)
        #btn_scan_gpib = tk.Button(self.frame, text="Scan Scope", command=self.scan_gpib)
        #btn_scan_gpib.grid(row=0, column=0)
        #Combo = ttk.Combobox(self.frame, values=self.GPIB_list, width=35)
        #Combo.set("Pick an Option")
        #Combo.grid(row=0, column=1)
        # btn_connect_scope = tk.Button(self.frame, text="Get Scope info", command=self.get_scope_info)
        # btn_connect_scope.grid(row=0, column=2)

        # row 1
        label_entry_dir = tk.Label(self.frame, text="Save to Folder")
        label_entry_dir.grid(row=1, column=0)
        self.E_dir = tk.Entry(self.frame, textvariable=self.path_var, width=37)
        self.E_dir.grid(row=1, column=1)
        btn_prompt_dir = tk.Button(self.frame, text="Prompt(P)", command=self.prompt_path)
        btn_prompt_dir.grid(row=1, column=2)
        self.frame.bind('p', lambda event: self.prompt_path())

        # row 2
        label_entry_filename = tk.Label(self.frame, text="File Name")
        label_entry_filename.grid(row=2, column=0)
        self.E_filename = tk.Entry(self.frame, textvariable=self.filename_var, width=37)
        self.E_filename.grid(row=2, column=1)
        btn_use_time = tk.Button(self.frame, text="Time Stamp", command=self.get_default_filename)
        btn_use_time.grid(row=2, column=2)

        # row 3
        btn_capture = tk.Button(self.frame, text="Capture (Enter)", command=self.btn_capture_clicked)
        btn_capture.grid(row=3, column=1)
        self.frame.bind('<Return>', lambda event: self.get_shot_scope(self.path_var.get()))
        #label.grid(row=2, column=0, padx=1, pady=1, ipady=3)

        # status bar
        status_bar = tk.Label(self.frame, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=4, column=0, columnspan=4, sticky='we')

        self.frame.pack()
        self.get_scope_info()

    def client_exit(self):
        exit()

    # def scan_gpib(self):
    #     self.GPIB_list = ['a','b','c']
    #     try:
    #         rm = visa.ResourceManager()
    #         self.GPIB_list = rm.list_resources()
    #
    #     except ValueError:
    #         self.status_var.set("VISA driver Error")

    def get_scope_info(self):
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                status_text = "Device Found: " + scope.query('*IDN?')
                self.IDN_of_scope.set(status_text)
                scope.close()
                rm.close()
        except ValueError:
            self.status_var.set("VISA driver Error, Scope NOT Found")

    def get_default_filename(self):
        # Generate a filename based on the current Date & Time
        self.dt = datetime.now()
        time_now = self.dt.strftime("DSO_%Y%m%d_%H%M%S.png")
        print("Will Save Image to ", time_now)
        self.filename_var.set(time_now)
        self.status_var.set("Time Stamp Applied")

    # def start_n_stop_scope_accquisition(self):
    #     # try:
    #     #     rm = visa.ResourceManager()
    #     #     with rm.open_resource(self.target_gpib_address.get()) as scope:
    #     # #'ACQuire: STOPAfter:COUNt500'

    def get_shot_scope(self):
        self.status_var.set("Try Talking to Scope")
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                scope.timeout = self.visa_timeout_duration
                self.IDN_of_scope.set(scope.query('*IDN?'))
                self.status_var.set("Time Stamp Applied")
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

                save_path = Path(self.path_var.get()) / Path(self.filename_var.get())
                print("SAVE PATH:", save_path)
                with open(save_path, "wb") as imgFile:
                    imgFile.write(img_data)
                    imgFile.close()
                    print("Saved!")
                    self.status_var.set(save_path)

                scope.close()
                rm.close()
        except ValueError:
            self.status_var.set("CANNOT connect to Scope")

    def prompt_path(self):
        folder_prompted = filedialog.askdirectory()
        print("Prompt", folder_prompted)
        if folder_prompted == '':
            self.status_var.set("Did not prompt destination folder")
        else:
            self.path_var.set(folder_prompted)
            status_text_temp = "file will be saved to " + "\"" + str(folder_prompted) + "\""
            self.status_var.set(status_text_temp)

    def btn_capture_clicked(self):
        folder = self.path_var.get()
        print("Doing stuff with folder", folder)
        self.get_shot_scope()


def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
