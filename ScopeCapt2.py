from datetime import datetime  # std library
import pyvisa as visa  # https://pyvisa.readthedocs.org/en/stable/
import os
from pathlib import Path

from PIL import Image
from io import BytesIO
import numpy as np
import cv2

import tkinter as tk
from tkinter import ttk, Entry, messagebox, filedialog, IntVar, Menu


# https://pythonguides.com/python-tkinter-menu-bar/
# https://coderslegacy.com/python/list-of-tkinter-widgets/

class App:
    # Define settings upon initialization.
    def __init__(self, master):
        self.master = master
        self.frame = tk.Frame(self.master)

        # self.master.geometry("+%d+%d" % (self.frame.window_start_x, self.frame.window_start_y))
        self.master.title("KW Scope Capture")

        self.target_gpib_address = tk.StringVar()
        self.status_var = tk.StringVar()
        self.path_var = tk.StringVar()
        self.filename_var = tk.StringVar()
        self.IDN_of_scope = tk.StringVar()

        self.imshow_var_bool = IntVar()
        self.fastacq_var_bool = IntVar()
        self.acq_state_var_bool = IntVar()
        self.add_timestamp_var_bool = IntVar(value=1)

        self.overwrite_bool = True
        self.filename_var.set('DPO')
        self.save＿filename = ''
        self.target_gpib_address.set('GPIB::6::INSTR')
        self.status_var.set("Waiting for User")
        self.path_var.set(os.getcwd())
        self.IDN_of_scope.set('')

        self.dt = datetime.now()
        self.visa_timeout_duration = 5000  # in ms



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

        self.GPIB_list = []

        # row 0
        # label_GPIB_address = tk.Label(self.frame, text="Target")
        # label_GPIB_address.grid(row=0, column=0)
        #
        # Combo = ttk.Combobox(self.frame, values=self.GPIB_list)
        # Combo.set("Pick your device")
        # Combo.grid(row=0, column=1, columnspan=2)
        #
        # btn_scan_gpib = tk.Button(self.frame, text="Scan", command=None)
        # btn_scan_gpib.grid(row=0, column=3)
        # btn_connect_gpib = tk.Button(self.frame, text="Connect", command=None)
        # btn_connect_gpib.grid(row=0, column=4)

        # btn_connect_scope = tk.Button(self.frame, text="Get Scope info", command=self.get_scope_info)
        # btn_connect_scope.grid(row=0, column=4)

        # row 1
        label_entry_dir = tk.Label(self.frame, text="Save to Folder")
        label_entry_dir.grid(row=1, column=0)
        self.E_dir = tk.Entry(self.frame, textvariable=self.path_var, width=37)
        self.E_dir.grid(row=1, column=1, columnspan=2)
        btn_prompt_dir = tk.Button(self.frame, text="Prompt", command=self.prompt_path)
        btn_prompt_dir.grid(row=1, column=3)
        # self.frame.bind('p', lambda event: self.prompt_path())

        # row 2
        label_entry_filename = tk.Label(self.frame, text="File Name")
        label_entry_filename.grid(row=2, column=0)
        self.E_filename = tk.Entry(self.frame, textvariable=self.filename_var, width=37)
        self.E_filename.grid(row=2, column=1, columnspan=2)
        # btn_use_time = tk.Button(self.frame, text="Add TimeStamp", command=self.get_default_filename)
        # btn_use_time.grid(row=2, column=2)

        chkbox_addTimeStamp = tk.Checkbutton(self.frame, text='Add Time', variable=self.add_timestamp_var_bool,
                                             onvalue=1, offvalue=0,
                                             command=None)
        chkbox_addTimeStamp.grid(row=2, column=3)

        # row3
        chkbox_imshow = tk.Checkbutton(self.frame, text='ShowImage', variable=self.imshow_var_bool, onvalue=1, offvalue=0,
                                       command=None)
        chkbox_imshow.grid(row=3, column=1)
        chkbox_Fstacq = tk.Checkbutton(self.frame, text='FastAcq', variable=self.fastacq_var_bool, onvalue=1,
                                           offvalue=0, command=self.trigger_fstacq)
        chkbox_Fstacq.grid(row=3, column=2)

        # row 4
        self.btn_RunStop = tk.Button(self.frame, text="Run/Stop(Ctrl+⏎)", command=self.btn_runstop_clicked)
        self.btn_RunStop.grid(row=4, column=1, columnspan=2)
        # btn_Stop = tk.Button(self.frame, text="Stop", command=self.btn_stop_clicked)
        # btn_Stop.grid(row=4, column=1)
        btn_Clear = tk.Button(self.frame, text="Clear(Ctrl+Del)", command=self.btn_clear_clicked)
        btn_Clear.grid(row=4, column=3)
        btn_capture = tk.Button(self.frame, text="Capture(⏎)", command=self.btn_capture_clicked)
        btn_capture.grid(row=4, column=0)

        # btn_exit = tk.Button(self.frame, text="Exit", command=self.client_exit)
        # btn_exit.grid(row=4, column=4)

        # row 5, status bar
        status_bar = tk.Label(self.frame, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=5, column=0, columnspan=5, sticky='we')

        self.frame.pack()

        self.get_acq_state()

        # self.get_scope_info()
        # self.get_default_filename()
        # self.get_scope_info()

    def client_exit(self):
        self.frame.destroy()
        exit()

    def onKey(self, event):
        print("On key")

    # def scan_gpib(self):
    #     self.GPIB_list = ['a','b','c']
    #     try:
    #         rm = visa.ResourceManager()
    #         self.GPIB_list = rm.list_resources()
    #
    #     except ValueError:
    #         self.status_var.set("VISA driver Error")

    def get_acq_state(self):
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                acq_state = int(scope.query('ACQuire:STATE?')[:-1])
                print(acq_state)
                self.acq_state_var_bool.set(acq_state)
                if self.acq_state_var_bool.get() == True:
                    self.btn_RunStop.configure(fg="green")
                elif self.acq_state_var_bool.get() == False:
                    self.btn_RunStop.configure(fg="black")
                else:
                    print("Cannot get Acq state")
                    self.status_var.set("Cannot get Acq state")
                scope.close()
            rm.close()
        except ValueError:
            print("VISA driver Error")

    def get_scope_info(self):
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                status_text = "Device Found: " + scope.query('*IDN?')
                print(status_text)
                self.status_var.set(status_text[:-1])
                self.IDN_of_scope.set(status_text)
                scope.close()
            rm.close()
        except ValueError:
            print("VISA driver Error")

    def get_default_filename(self):
        # Generate a filename based on the current Date & Time
        self.dt = datetime.now()
        time_now = self.dt.strftime("%H%M%S")
        # time_now = self.dt.strftime("_%Y%m%d_%H%M%S.png")
        # get_exist_text = self.filename_var.get()

        if self.add_timestamp_var_bool.get() == 1:
            self.savefilename = self.filename_var.get() + '_' + time_now
        else:
            if self.filename_var.get() == '':
                self.filename_var.set('DPO')
            self.savefilename = self.filename_var.get()
        # self.status_var.set("Time Stamp Applied")

    def get_shot_scope(self):
        self.status_var.set("Try Talking to Scope")
        self.get_default_filename()
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

                # # Image show (OpenCV)
                if self.imshow_var_bool.get():
                    file_png_data = BytesIO(img_data)
                    dt = Image.open(file_png_data)
                    I = np.asarray(dt)
                    print("Got image, shape:", I.shape)
                    I_cv2 = cv2.cvtColor(I, cv2.COLOR_RGB2BGR)
                    cv2.imshow(" Captured, Press Any Key to Dismiss", I_cv2)
                    cv2.waitKey()
                    cv2.destroyAllWindows()

                # # Image show (PIL)
                # if self.imshow_var_bool.get():
                #     file_png_data = BytesIO(img_data)
                #     img = Image.open(file_png_data)
                #     img.show()

                    # I = np.asarray(dt)
                    # print("Got image, shape:", I.shape)

                    # I_cv2 = cv2.cvtColor(I, cv2.COLOR_RGB2BGR)
                    # cv2.imshow(" Captured, Press Any Key to Dismiss", I_cv2)
                    # cv2.waitKey()
                    # cv2.destroyAllWindows()

                # Image save
                save_path = Path(self.path_var.get()) / Path(self.savefilename)
                # NEED minor FIX HERE
                save_path = str(save_path) + '.png'
                print("SAVE PATH:", save_path)

                # overwrite protection
                if Path(save_path).is_file():
                    answer = messagebox.askokcancel("Overwrite Protection",
                                                    "file name already exist, would you like to overwrite ?")
                    self.overwrite_bool = answer
                    print("Overwrite", self.overwrite_bool)
                try:
                    if self.overwrite_bool is True:
                        with open(save_path, "wb") as imgFile:
                            imgFile.write(img_data)
                            imgFile.close()
                            print("Saved!")
                            self.status_var.set(save_path)
                    else:
                        print("saving action canceled!")
                        self.status_var.set("saving action canceled!")
                except IOError:
                    self.status_var.set("Cannot save file, check folder and filename")
                scope.close()
                rm.close()
        except ValueError:
            print("VISA driver Error")
            self.status_var.set("VISA driver Error")
        self.get_default_filename()

    def prompt_path(self):
        folder_prompted = filedialog.askdirectory()
        print("Prompt", folder_prompted)
        if folder_prompted == '':
            self.status_var.set("Did not prompt destination folder")
        else:
            self.path_var.set(folder_prompted)
            status_text_temp = "file will be saved to " + "\"" + str(folder_prompted) + "\""
            self.status_var.set(status_text_temp)

    def trigger_fstacq(self):
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                if self.fastacq_var_bool.get():
                    scope.write('FASTAcq:STATE ON')
                else:
                    scope.write('FASTAcq:STATE OFF')
                scope.close()
            rm.close()
        except ValueError:
            print("VISA driver Error")
            self.status_var.set("VISA driver Error")

    def btn_clear_clicked(self, *args):
        print("Clear Btn clicked")
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                scope.write('CLEAR ALL')
                scope.close()
            rm.close()
        except ValueError:
            print("VISA driver Error")
            self.status_var.set("VISA driver Error")

    def btn_runstop_clicked(self, *args):
        print("Run/Stop Btn clicked")
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                if self.acq_state_var_bool.get() == True:
                    scope.write('ACQuire:STATE OFF')
                else:
                    scope.write('ACQuire:STATE ON')
                scope.close()
            rm.close()
        except ValueError:
            print("VISA driver Error")
            self.status_var.set("VISA driver Error")
            self.btn_RunStop.configure(fg="red")
        self.get_acq_state()

    # def btn_stop_clicked(self):
    #     try:
    #         rm = visa.ResourceManager()
    #         with rm.open_resource(self.target_gpib_address.get()) as scope:
    #             scope.write('ACQuire:STATE OFF')
    #             scope.close()
    #         rm.close()
    #     except ValueError:
    #         print("VISA driver Error")
    #         self.status_var.set("VISA driver Error")

    def btn_capture_clicked(self, *args):
        folder = self.path_var.get()
        print("Capture Btn clicked, save folder", folder)
        self.get_shot_scope()

    # def btn_countdown_capture_clicked(self):
    #     folder = self.path_var.get()
    #     print("Capture Btn clicked, save folder", folder)
    #     self.get_shot_scope()


def main():
    root = tk.Tk()
    app = App(root)

    root.bind("<Return>", app.btn_capture_clicked)
    root.bind("<Control-Return>", app.btn_runstop_clicked)
    root.bind("<Control-Delete>", app.btn_clear_clicked)

    root.mainloop()


if __name__ == '__main__':
    main()
