from datetime import datetime  # std library
import pyvisa as visa  # https://pyvisa.readthedocs.org/en/stable/
import os
from pathlib import Path

from PIL import Image
from io import BytesIO
import numpy as np
import cv2
import base64
import imgBase64 as myIcon

import tkinter as tk
from tkinter import ttk, Entry, messagebox, filedialog, IntVar, Menu, PhotoImage
# https://pythonguides.com/python-tkinter-menu-bar/
# https://coderslegacy.com/python/list-of-tkinter-widgets/

import json


class App:
    # Define settings upon initialization.
    def __init__(self, master):
        self.master = master
        self.frame = tk.Frame(self.master)

        self.app_version = " V1.4"
        # self.master.geometry("+%d+%d" % (self.frame.window_start_x, self.frame.window_start_y))
        self.appTitleText = "KW Scope Capture" + self.app_version
        self.master.title(self.appTitleText)

        self.user_pref_filename = Path(os.getcwd()) / Path('user_pref.json')
        print("self.user_pref_filename=", self.user_pref_filename)
        self.target_gpib_address = tk.StringVar()
        self.target_gpib_address.set('GPIB::6::INSTR')
        self.status_var = tk.StringVar()
        self.status_var.set("Waiting for User")
        self.filename_var = tk.StringVar()
        self.IDN_of_scope = tk.StringVar()

        # scope menu var
        self.sel_ch1_var_bool = IntVar()
        self.sel_ch2_var_bool = IntVar()
        self.sel_ch3_var_bool = IntVar()
        self.sel_ch4_var_bool = IntVar()
        self.persistence_var_bool = IntVar()
        self.fastacq_var_bool = IntVar()
        self.acq_state_var_bool = IntVar()

        # User Preference var
        self.imshow_var_bool = IntVar()
        self.add_timestamp_var_bool = IntVar(value=1)
        self.stopAfterAcq_var = IntVar(value=500)
        self.addTextOverlay_var_bool = IntVar(value=0)
        self.path_var = tk.StringVar()
        self.path_var.set(os.getcwd())
        self.filename_var.set('DPO')

        self.overwrite_bool = True
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

        # --------------row 1
        label_entry_dir = tk.Label(self.frame, text="Save to Folder")
        label_entry_dir.grid(row=1, column=0, sticky='W')
        self.E_dir = tk.Entry(self.frame, textvariable=self.path_var)
        self.E_dir.grid(row=1, column=1, columnspan=4, sticky='we')
        btn_prompt_dir = tk.Button(self.frame, text="Prompt", command=self.prompt_path)
        btn_prompt_dir.grid(row=1, column=6, padx=10)
        # self.frame.bind('p', lambda event: self.prompt_path())

        # --------------row 2
        label_entry_filename = tk.Label(self.frame, text="File Name")
        label_entry_filename.grid(row=2, column=0, sticky='W')
        self.E_filename = tk.Entry(self.frame, textvariable=self.filename_var)
        self.E_filename.grid(row=2, column=1, columnspan=4, sticky='we')
        # btn_use_time = tk.Button(self.frame, text="Add TimeStamp", command=self.get_default_filename)
        # btn_use_time.grid(row=2, column=2)

        # chkbox_addTimeStamp = tk.Checkbutton(self.frame, text='Add Time', variable=self.add_timestamp_var_bool,
        #                                      onvalue=1, offvalue=0,
        #                                      command=None)
        # chkbox_addTimeStamp.grid(row=2, column=6)

        # --------------row3


        # --------------row 4
        self.btn_capture = tk.Button(self.frame, text="ScreenShot(↵)", command=self.btn_capture_clicked)
        self.btn_capture.grid(row=4, column=1, padx=2)
        self.btn_RunStop = tk.Button(self.frame, text="Run/Stop(Ctrl+↵)", command=self.btn_runstop_clicked)
        self.btn_RunStop.grid(row=4, column=2, padx=2)
        btn_Single = tk.Button(self.frame, text="Single", command=self.btn_single_clicked)
        btn_Single.grid(row=4, column=3, padx=2)
        btn_Clear = tk.Button(self.frame, text="Clear(Ctrl+Del)", command=self.btn_clear_clicked)
        btn_Clear.grid(row=4, column=4, padx=2)

        # btn_exit = tk.Button(self.frame, text="Exit", command=self.client_exit)
        # btn_exit.grid(row=4, column=4)

        # --------------row 5, status bar
        status_bar = tk.Label(self.frame, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=5, column=0, columnspan=7, sticky='we')

        self.frame.pack()

        self.get_acq_state()

        self.get_scope_info()
        # self.get_default_filename()
        self.closest_index = 0
        self.scaleList = [1e-9, 2e-9, 5e-9,
                          1e-8, 2e-8, 5e-8,
                          1e-7, 2e-7, 5e-7,
                          1e-6, 2e-6, 5e-6,
                          1e-5, 2e-5, 5e-5,
                          1e-4, 2e-4, 5e-4,
                          1e-3, 2e-3, 5e-3,
                          1e-2, 2e-2, 5e-2,
                          1e-1, 2e-1, 5e-1,
                          1e0, 2e0, 5e0,
                          1e1, 2e1, 5e1]

        # --------------MenuBar
        menubar = Menu(self.master)
        self.master.config(menu=menubar)

        filemenu = Menu(menubar, tearoff=False)
        scopemenu = Menu(menubar, tearoff=False)
        miscmenu = Menu(menubar, tearoff=False)
        toolmenu = Menu(menubar, tearoff=False)
        helpmenu = Menu(menubar, tearoff=False)

        file_submenu = Menu(filemenu)
        file_submenu.add_command(label="Future Implement 1")
        file_submenu.add_command(label="Future Implement 2")
        file_submenu.add_command(label="Future Implement 3")
        filemenu.add_cascade(label='Import', menu=file_submenu, underline=0)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", underline=0, command=self.on_exit)

        miscmenu.add_checkbutton(label="Add Time", onvalue=1, offvalue=0, variable=self.add_timestamp_var_bool)
        miscmenu.add_checkbutton(label="Show Image after ScreenShot", onvalue=1, offvalue=0, variable=self.imshow_var_bool)
        miscmenu.add_checkbutton(label="Add Text overlay on ScreenShot", onvalue=1, offvalue=0, variable=self.addTextOverlay_var_bool)

        scope_submenu = Menu(scopemenu)

        scope_submenu.add_checkbutton(label="CH 1", onvalue=1, offvalue=0, variable=self.sel_ch1_var_bool,
                                      command=self.scope_channel_select)
        scope_submenu.add_checkbutton(label="CH 2", onvalue=1, offvalue=0, variable=self.sel_ch2_var_bool,
                                      command=self.scope_channel_select)
        scope_submenu.add_checkbutton(label="CH 3", onvalue=1, offvalue=0, variable=self.sel_ch3_var_bool,
                                      command=self.scope_channel_select)
        scope_submenu.add_checkbutton(label="CH 4", onvalue=1, offvalue=0, variable=self.sel_ch4_var_bool,
                                      command=self.scope_channel_select)

        scopemenu.add_cascade(label='Enable CH', menu=scope_submenu, underline=0)
        scopemenu.add_checkbutton(label="Use DPX", onvalue=1, offvalue=0, variable=self.fastacq_var_bool,
                                  command=self.trigger_fstacq)
        scopemenu.add_checkbutton(label="Use Persistence", onvalue=1, offvalue=0, variable=self.persistence_var_bool,
                                  command=self.set_persistence)
        scopemenu.add_command(label="Exec. AutoSet", command=self.scope_execute_autoset)
        scopemenu.add_command(label="Recall Default Settings", command=self.scope_factory_reset)

        helpmenu.add_command(label="tips", underline=0, command=lambda: self.status_var.set(
            " tip: Use <Control> key + <Left> or <Right> arrow key to scale time division"))

        helpmenu.add_command(label="About", underline=0, command=lambda:
            messagebox.showinfo("KW ScopeCapt", "Version:" + self.app_version
                                +"\nIcons made by [smashicons.com]"
                                +"\n'OpenCV' is licensed under the [Apache 2 License]."
                                +"\n'numpy' is licensed under the [NumPy license]."
                                +"\n'pyvisa' is licensed under the [MIT License]."
                                +"\n'PIL' is licensed under open the [source HPND License]."))

        menubar.add_cascade(label="File", underline=0, menu=filemenu)
        menubar.add_cascade(label="Scope", underline=0, menu=scopemenu)
        menubar.add_cascade(label="Misc.", underline=0, menu=miscmenu)
        menubar.add_cascade(label="Tool", underline=0, menu=toolmenu)
        menubar.add_cascade(label="Help", underline=0, menu=helpmenu)

        self.read_user_pref()

    def on_exit(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.write_user_pref()
            self.frame.destroy()
            self.frame.quit()
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

    def read_user_pref(self):
        if self.user_pref_filename.exists():
            with open(self.user_pref_filename, 'r') as f:
                config = json.load(f)
            # edit the data
            self.imshow_var_bool.set(config['imshow_var_bool'])
            self.add_timestamp_var_bool.set(config['add_timestamp_var_bool'])
            self.addTextOverlay_var_bool.set(config['addTextOverlay_var_bool'])
            self.path_var.set(config['path_var'])
            self.filename_var.set(config['filename_var'])
        else:
            self.write_user_pref()

    def write_user_pref(self):
        with open(self.user_pref_filename, 'w') as f:
            config = {"imshow_var_bool": self.imshow_var_bool.get(),
                      "add_timestamp_var_bool": self.add_timestamp_var_bool.get(),
                      "addTextOverlay_var_bool": self.addTextOverlay_var_bool.get(),
                      "path_var": self.path_var.get(),
                      "filename_var": self.filename_var.get()
                      }
            json.dump(config, f)

    def get_acq_state(self):
        try:
            rm = visa.ResourceManager()
            try:
                scope = rm.open_resource(self.target_gpib_address.get())
                self.sel_ch1_var_bool.set(value=int(scope.query('SELect:CH1?')[:-1]))
                self.sel_ch2_var_bool.set(value=int(scope.query('SELect:CH2?')[:-1]))
                self.sel_ch3_var_bool.set(value=int(scope.query('SELect:CH3?')[:-1]))
                self.sel_ch4_var_bool.set(value=int(scope.query('SELect:CH4?')[:-1]))
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
            except Exception:
                print("VISA IO Error")
                self.status_var.set("ERROR: Oscilloscope Not Found, "
                                    "Set GPIB address to 6 and \"Talk/Listen\" mode!")
            rm.close()
        except ValueError:
            print("Cannot get Acq status-VISA driver Error")

    def get_scope_info(self):
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                idn_text = ("  Found : " + scope.query('*IDN?'))[:-1]
                print(idn_text)
                self.status_var.set(" tip: Use <Control> key + <Left> or <Right> arrow key to scale time division")
                self.IDN_of_scope.set(idn_text)
                # print("IDN VAR get", self.IDN_of_scope.get())
                idn_text_title = idn_text.split(",")[0] + " " + idn_text.split(",")[1]
                self.appTitleText = self.appTitleText + " " + idn_text_title
                self.master.title(self.appTitleText)
                scope.close()
            rm.close()
        except ValueError:
            self.appTitleText = self.appTitleText + "No Device Found on GPIB Bus"
            self.master.title(self.appTitleText)
            print("Cannot get scope info-VISA driver Error")

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
                self.status_var.set(self.IDN_of_scope.get()[:-1])
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


                file_png_data = BytesIO(img_data)
                dt = Image.open(file_png_data)
                I = np.asarray(dt)
                I_cv2 = cv2.cvtColor(I, cv2.COLOR_RGB2BGR)
                print("cv2 image shape:", I.shape)

                if self.addTextOverlay_var_bool.get():
                    font = cv2.FONT_HERSHEY_DUPLEX
                    font_size = 0.44
                    font_color = (255, 255, 255)
                    font_thickness = 1
                    text = self.filename_var.get()
                    height, width, depth = I_cv2.shape
                    cv2.rectangle(I_cv2, (width - width + 677, height - height), (width, height - height + 31),
                                  (0, 0, 0), -1)
                    img_text = cv2.putText(I_cv2, text, (width - width + 677, height - height + 20), font,
                                           font_size, font_color, font_thickness,
                                           cv2.LINE_AA)
                    outputImage = img_text
                else:
                    outputImage = I_cv2

                # # Image show (OpenCV)
                if self.imshow_var_bool.get():
                    cv2.imshow("Captured, Press Any Key to Dismiss", outputImage)
                    cv2.waitKey()
                    cv2.destroyAllWindows()

                # create directory if doesn't exist
                if not Path(self.path_var.get()).exists():
                    try:
                        Path(self.path_var.get()).mkdir(parents=True, exist_ok=False)
                    except Exception as E:
                        messagebox.showerror("Oops! Error occurred!",
                                             "Please Choose available folder to save file.\n" + "Error:\n" + str(E))
                        self.status_var.set(str(E))
                # Image save
                save_path = Path(self.path_var.get()) / Path(self.savefilename)
                # NEED minor FIX HERE
                save_path = str(save_path) + '.png'
                print("SAVE PATH:", save_path)

                # overwrite protection
                if Path(save_path).is_file():
                    answer = messagebox.askokcancel("Oops!",
                                                    "File already exists, Overwrite ?")
                    self.overwrite_bool = answer
                    print("Overwrite", self.overwrite_bool)
                else:
                    self.overwrite_bool = True
                try:
                    if self.overwrite_bool is True:
                        if self.addTextOverlay_var_bool.get():
                            try:
                                cv2.imwrite(save_path, outputImage)
                            except IOError:
                                print("cv2 save Failed")
                                self.status_var.set("Cannot save file, check folder and filename")
                        else:
                            with open(save_path, "wb") as imgFile:
                                imgFile.write(img_data)
                                imgFile.close()
                                print("Saved!")
                                self.status_var.set("Saved: "+self.savefilename+'.png')
                    else:
                        files = [('PNG Image', '*.png')]
                        filepath = filedialog.asksaveasfilename(filetypes=files, defaultextension=files)
                        if filepath is None:
                            print("saving action canceled!")
                            self.status_var.set("saving action canceled!")
                        else:
                            if self.addTextOverlay_var_bool.get():
                                try:
                                    cv2.imwrite(filepath, outputImage)
                                except IOError:
                                    print("cv2 save Failed")
                                    self.status_var.set("Cannot save file, check folder and filename")
                            else:
                                with open(Path(filepath), "wb") as imgFile:
                                    print("filepath", Path(filepath))
                                    imgFile.write(img_data)
                                    imgFile.close()
                                    print("Saved!")
                        self.status_var.set("Saved: " + str(Path(filepath).name))

                except IOError:
                    self.status_var.set("Cannot save file, check folder and filename")
                scope.close()
                rm.close()
        except ValueError:
            print("Cannot get scope shot-VISA driver Error")
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

    def scope_execute_autoset(self):
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                scope.write('AUTOSet EXECute')
                scope.close()
            rm.close()
        except ValueError:
            print("Autoset Failed")
            self.status_var.set("AutoSet Failed, VISA ERROR")

    def scope_factory_reset(self):
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                scope.write('*RST')
                scope.close()
            rm.close()
        except ValueError:
            print("Factory Reset Failed")
            self.status_var.set("Factory Reset, VISA ERROR")

    def scope_channel_select(self):
        print("Into --scope_channel_select--")
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                if self.sel_ch1_var_bool.get():
                    scope.write('SELect:CH1 ON')
                else:
                    scope.write('SELect:CH1 OFF')
                if self.sel_ch2_var_bool.get():
                    scope.write('SELect:CH2 ON')
                else:
                    scope.write('SELect:CH2 OFF')
                if self.sel_ch3_var_bool.get():
                    scope.write('SELect:CH3 ON')
                else:
                    scope.write('SELect:CH3 OFF')
                if self.sel_ch4_var_bool.get():
                    scope.write('SELect:CH4 ON')
                else:
                    scope.write('SELect:CH4 OFF')
                scope.close()
            rm.close()
        except ValueError:
            print("Sel CH Failed")
            self.status_var.set("Sel CH Failed, VISA ERROR")

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
            print("cannot trigger FastAcq-VISA driver Error")
            self.status_var.set("VISA driver Error")

    def set_persistence(self):
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                if self.persistence_var_bool.get():
                    scope.write('DISplay:PERSistence INFPersist')
                else:
                    scope.write('DISplay:PERSistence OFF')
                scope.close()
            rm.close()
        except ValueError:
            print("cannot set Persistence")
            self.status_var.set("VISA driver Error")

    def btn_single_clicked(self):
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                scope.write('ACQuire:STOPAFTER SEQUENCE')
                scope.write('ACQ:STATE ON')
            scope.close()
            rm.close()
        except ValueError:
            print("cannot do Single shot")
            self.status_var.set("VISA driver Error")

    def btn_clear_clicked(self, *args):
        ScopeModel = self.IDN_of_scope.get().split(",")
        # print(ScopeModel)
        isCModel = False
        try:
            if ScopeModel[1][-1] == 'C':
                isCModel = True
                print('isCModel=', isCModel)
            else:
                isCModel = False
        except IndexError:
            print("var \"self.IDN_of_scope[1][-1]\" did not exist.")
        print("Clear Btn clicked")
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                if isCModel:
                    scope.write('CLEAR ALL')
                    print("Send \"CLEAR ALL\"")
                    self.status_var.set("\"CLEAR ALL\" sent, Cleared")
                else:
                    scope.write('ACQuire:STOPAFTER SEQUENCE')
                    scope.write('DISplay:PERSistence:RESET')
                    scope.write('ACQ:STATE ON')
                    scope.write('ACQ:STOPA RUNST')
                    print("Send Alter Cmd for CLEAR ALL")
                    self.status_var.set("Cleared")
                scope.close()
            rm.close()
        except ValueError:
            print("cannot clear scope-VISA driver Error")
            self.status_var.set("VISA driver Error")

    def btn_runstop_clicked(self, *args):
        print("Run/Stop Btn clicked")
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                if self.acq_state_var_bool.get() == True:
                    scope.write('ACQuire:STATE OFF')
                else:
                    scope.write('ACQ:STOPA RUNST')
                    scope.write('ACQuire:STATE ON')
                scope.close()
            rm.close()
        except ValueError:
            print("cannot RunStop-VISA driver Error")
            self.status_var.set("VISA driver Error")
            self.btn_RunStop.configure(fg="red")
        self.get_acq_state()

    def btn_capture_clicked(self, *args):
        folder = self.path_var.get()
        print("Capture Btn clicked, save folder", folder)
        self.get_shot_scope()

    # def btn_countdown_capture_clicked(self):
    #     folder = self.path_var.get()
    #     print("Capture Btn clicked, save folder", folder)
    #     self.get_shot_scope()

    def horizontal_scale(self, event):
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                scale = float(scope.query('HORizontal:MAIn:SCAle?'))
                print("Scale = ", scale)
                # get the index of closest value
                self.closest_index = min(range(len(self.scaleList)), key=lambda i: abs(self.scaleList[i]-scale))
                print("closetstIndex=", self.closest_index)
                self.target_index = self.closest_index
                if event.keysym == 'Left':
                    if self.closest_index < (len(self.scaleList)-1):
                        self.target_index = self.closest_index + 1
                        scope.write('HORizontal:MAIn:SCAle ' + str(self.scaleList[self.target_index]))
                        scope.write('HORizontal:RESOlution 5e5')
                elif event.keysym == 'Right':
                    if self.closest_index > 1:
                        self.target_index = self.closest_index - 1
                        scope.write('HORizontal:MAIn:SCAle ' + str(self.scaleList[self.target_index]))
                        scope.write('HORizontal:RESOlution 5e5')
                else:
                    pass
                scope.write('HORizontal:MODE AUTO')
            rm.close()
        except ValueError:
            self.status_var.set("VISA driver Error")
            self.btn_RunStop.configure(fg="red")

    # scope.write('CURSOR: FUNCTION SCREEN')


def center(win):
    """
    centers a tkinter window
    :param win: the main window or Toplevel window to center
    """
    win.update_idletasks()
    width = win.winfo_width()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = width + 2 * frm_width
    height = win.winfo_height()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + frm_width
    x = win.winfo_screenwidth() // 2 - win_width // 2
    y = win.winfo_screenheight() // 2 - win_height // 2
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    win.deiconify()


def splash():
    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.title("Splash!")
    width = splash.winfo_screenwidth()
    height = splash.winfo_screenheight()
    # splash.geometry('%dx%d+%d+%d' % (width*0.2, height*0.2, width*0.1, height*0.1))
    # splash.geometry("800x750+128+128")
    splash_img = myIcon.splash_base64_128px
    splash_img = base64.b64decode(splash_img)
    splash_img = PhotoImage(data=splash_img)
    # highlightthickness=0 -> remove frame
    canvas = tk.Canvas(splash, height=256, width=256, bg='black', highlightthickness=0)
    canvas.create_image(128, 128, image=splash_img)
    canvas.pack(fill='both')
    splash.after(2700, splash.destroy)
    splash.wm_attributes('-transparentcolor', 'black')
    center(splash)
    splash.mainloop()


def mainApp():
    root = tk.Tk()
    app = App(root)
    img = myIcon.icon_base64_32px
    img = base64.b64decode(img)
    img = PhotoImage(data=img)
    root.wm_iconphoto(True, img)
    # root.iconbitmap(r'img/ico32.ico')

    # NEED a better way to fix the delete of filename and cannot Paste by Ctrl+V bug.
    # root.bind("<Control_L>", lambda i: app.frame.focus_set())
    root.bind("<Control_R>", lambda i: app.frame.focus_set())
    root.bind("<Return>", app.btn_capture_clicked)
    root.bind("<Control-Return>", app.btn_runstop_clicked)
    root.bind("<Control-Delete>", app.btn_clear_clicked)
    root.bind("<Control-Left>", app.horizontal_scale)
    root.bind("<Control-Right>", app.horizontal_scale)
    center(root)
    root.protocol("WM_DELETE_WINDOW", app.on_exit)
    root.mainloop()


if __name__ == '__main__':
    mainApp()
