from datetime import datetime  # std library
import pyvisa as visa  # https://pyvisa.readthedocs.org/en/stable/
import os
from pathlib import Path
import atexit
from PIL import Image
from io import BytesIO
import numpy as np
import cv2
import base64
import imgBase64 as myIcon
import time
import tkinter as tk
from tkinter import ttk, Entry, messagebox, filedialog, IntVar, Menu, PhotoImage
# https://pythonguides.com/python-tkinter-menu-bar/
# https://coderslegacy.com/python/list-of-tkinter-widgets/
import threading
import json


class WindowGPIBScanner:
    isOktoUpdateState = False
    def __init__(self, master):
        self.master = master
        self.frame = tk.Frame(self.master)
        self.master.title("GPIB Scanner")
        self.master.geometry('440x300')
        self.listbox = tk.Listbox(self.frame)
        self.btn_scan_text_var = tk.StringVar()
        self.btn_scan_text_var.set("Scan")
        # Inserting the listbox items
        self.listbox.insert(0, "Click on [Scan] button, this usually takes about 30 seconds...")
        self.scanButton = tk.Button(self.frame, text=self.btn_scan_text_var.get(), width=25,
                                    command=self.btn_scan_click)
        self.btn = tk.Button(self.frame, text='Set Selected as target device', width=25, command=self.selected_item)
        # self.quitButton = tk.Button(self.frame, text='Quit', width=25, command=self.close_window)
        self.scanButton.pack()
        # self.quitButton.pack()

        self.btn.pack(side='bottom', pady=3)
        self.listbox.pack(fill=tk.BOTH, expand=True, pady=3)
        self.frame.pack(fill=tk.BOTH, expand=True, pady=3)
        self.found_device_with_name = []
        self.selected_device_addr = ""
        atexit.register(self.close_window)

    def selected_item(self):
        # Traverse the tuple returned by
        # curselection method and print
        # corresponding value(s) in the listbox
        for i in self.listbox.curselection():
            selected_item = self.listbox.get(i)
            self.selected_device_addr = self.found_device_with_name[i][1]
            # print("Selected", i, selected_item)
            # print("selected Device Addr=", selected_device_addr)
            # print("")
        App.cls_var = self.selected_device_addr
        return self.close_window()

    def close_window(self):
        # self.worker.join()
        # self.frame.destroy()
        self.master.destroy()

    def btn_scan_click(self):
        self.scanthread = threading.Thread(target=self.scan_gpib)
        self.scanthread.start()

    def update_device_listbox(self):
        print("update_device_listbox")
        self.listbox.delete('0', 'end')
        print(self.found_device_with_name)
        for i in range(0, len(self.found_device_with_name)):
            addr = ''
            try:
                vendor = self.found_device_with_name[i][0].split(',')[0]
                model_name = self.found_device_with_name[i][0].split(',')[1]
                addr = self.found_device_with_name[i][1]
            except:
                vendor = "Unknown"
                model_name = "Unknown"
            if len(addr) > 1:
                list_item_text = (vendor + ", " + model_name + ", address: " + addr)
                self.listbox.insert(i, list_item_text)

    def scan_gpib(self):
        WindowGPIBScanner.isOktoUpdateState = False
        self.scanButton["state"] = "disabled"
        print("scan_gpib")
        """
        list name & address of found GPIB devices, get user prompt device
        """
        self.found_device_with_name = []
        try:
            rm = visa.ResourceManager()
            ls_res = rm.list_resources()    # query='?*'
            for addr in ls_res:
                title = "Scanning: " + str(int(((ls_res.index(addr)+1) / (len(ls_res)))*100)) + "%"
                title = title + "  Please Wait..."
                self.master.title(title)
                idn = ''
                try:
                    with rm.open_resource(addr, open_timeout=2) as de:
                        idn_temp = de.query("*IDN?").rstrip()
                        if idn_temp == "":
                            idn = "Unknown"
                        else:
                            idn = idn_temp
                        self.found_device_with_name.append((idn, addr))
                        de.close()
                except visa.VisaIOError:
                    idn = "Unknown_TimeOut"
                    self.found_device_with_name.append((idn, addr))
                except Exception as e:
                    pass
                print("gotoupdate")
                self.update_device_listbox()
        except ValueError:
            print("Scan gpib Error")
        self.scanButton["state"] = "normal"
        self.master.title("GPIB Scanner [finished!]")
        WindowGPIBScanner.isOktoUpdateState = True


class App:
    cls_var = ""
    # Define settings upon initialization.
    def __init__(self, master):
        self.master = master
        self.frame = tk.Frame(self.master)

        self.app_version = " V1.5"
        # self.master.geometry("+%d+%d" % (self.frame.window_start_x, self.frame.window_start_y))
        self.appTitleText = "KW Scope Capture" + self.app_version
        self.master.title(self.appTitleText)

        self.user_pref_filename = Path(os.getcwd()) / Path('user_pref.json')
        print("self.user_pref_filename=", self.user_pref_filename)

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
        self.imshow_var_bool = IntVar(value=0)
        self.add_timestamp_var_bool = IntVar(value=1)
        self.addTextOverlay_var_bool = IntVar(value=0)
        self.path_var = tk.StringVar()
        self.path_var.set(os.getcwd())
        self.filename_var.set('DPO')
        self.scopeUseExtDrv_var_bool = IntVar(value=0)
        self.use_inkSaver_var_bool = IntVar(value=0)

        self.overwrite_bool = True
        self.IDN_of_scope.set('')
        self.dt = datetime.now()
        self.visa_timeout_duration = 10000  # in ms

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
        btn_prompt_dir = tk.Button(self.frame, text="Prompt ", command=self.prompt_path)
        btn_prompt_dir.grid(row=1, column=6, padx=10, pady=2)
        # self.frame.bind('p', lambda event: self.prompt_path())

        # --------------row 2
        label_entry_filename = tk.Label(self.frame, text="File Name")
        label_entry_filename.grid(row=2, column=0, sticky='W')
        self.E_filename = tk.Entry(self.frame, textvariable=self.filename_var)
        self.E_filename.grid(row=2, column=1, columnspan=4, sticky='we')
        self.btn_capture = tk.Button(self.frame, text="Trig 50%", command=self.scope_set_trigger_a)
        self.btn_capture.grid(row=2, column=6, padx=10, pady=2)
        # btn_use_time = tk.Button(self.frame, text="Add TimeStamp", command=self.get_default_filename)
        # btn_use_time.grid(row=2, column=2)

        #

        # --------------row3
        self.chkbox_persistence = tk.Checkbutton(self.frame, text='Persistence',
                                                 variable=self.persistence_var_bool,
                                                 onvalue=1, offvalue=0, command=self.set_persistence)
        self.chkbox_persistence.grid(row=3, column=1, padx=2, pady=2)
        self.chkbox_fastacq = tk.Checkbutton(self.frame, text='FastAcq',
                                                 variable=self.fastacq_var_bool,
                                                 onvalue=1, offvalue=0, command=self.trigger_fstacq)
        self.chkbox_fastacq.grid(row=3, column=2, padx=2, pady=2)
        # self.l = tk.Button(self.frame, text="(<-)", command=self.horizontal_scale(direction='Left'))
        # self.l.grid(row=3, column=3, padx=2)
        # self.r = tk.Button(self.frame, text="(->)", command=None)
        # self.r.grid(row=3, column=4, padx=2)


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
        filemenu.add_command(label="Exit", underline=0, command=self.ask_quit)

        miscmenu.add_checkbutton(label="Add Time", onvalue=1, offvalue=0, variable=self.add_timestamp_var_bool)
        miscmenu.add_checkbutton(label="Show Image after ScreenShot", onvalue=1, offvalue=0,
                                 variable=self.imshow_var_bool)
        miscmenu.add_checkbutton(label="Add Text overlay on ScreenShot", onvalue=1, offvalue=0,
                                 variable=self.addTextOverlay_var_bool)
        miscmenu.add_checkbutton(label="Use Ink Saver", onvalue=1, offvalue=0,
                                 variable=self.use_inkSaver_var_bool)
        miscmenu.add_checkbutton(label="2,3,4 series ScreenShot", onvalue=1, offvalue=0,
                                 variable=self.scopeUseExtDrv_var_bool)

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
        scopemenu.add_checkbutton(label="Use FastAcq", onvalue=1, offvalue=0, variable=self.fastacq_var_bool,
                                  command=self.trigger_fstacq)
        scopemenu.add_checkbutton(label="Use Persistence", onvalue=1, offvalue=0, variable=self.persistence_var_bool,
                                  command=self.set_persistence)
        scopemenu.add_command(label="Exec. AutoSet", command=self.scope_execute_autoset)
        scopemenu.add_command(label="Recall Default Settings", command=self.scope_factory_reset)

        toolmenu.add_command(label="GPIB Scanner", command=self.create_frame_gpib_scanner)

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

        atexit.register(self.at_exit)
        self.frame.pack()

        self.target_gpib_address = tk.StringVar()
        self.read_user_pref()
        self.update_addr_inApp()

        if len(self.target_gpib_address.get()) > 3:
            self.update_addr_inApp()
            print("ReadOut_target-addr=", self.target_gpib_address.get())
            self.get_scope_info()
            # self.get_acq_state()
        else:
            messagebox.showinfo("First time Huh?",
                                "Target device record not found\nUse Tool>GPIB Scanner to Set target Device.")
            # self.create_frame_gpib_scanner()

        updatehread = threading.Thread(target=self.task_update_device_state)
        updatehread.start()

    def task_update_device_state(self):
        while 1:
            if WindowGPIBScanner.isOktoUpdateState:
                try:
                    print("check for upfates")
                    self.update_addr_inApp()
                    self.get_acq_state()
                    self.master.update_idletasks()
                    time.sleep(0.1)
                except:
                    pass

    def update_addr_inApp(self):
        print(self.__class__.cls_var)
        self.target_gpib_address.set(self.__class__.cls_var)

    def ask_quit(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            # self.updatehread.join()
            self.frame.destroy()
            self.master.destroy()
            exit()

    def at_exit(self):
        try:
            self.write_user_pref()
        except:
            pass

    def onKey(self, event):
        print("On key")

    def read_user_pref(self):
        # self.update_addr_inApp()
        if self.user_pref_filename.exists():
            with open(self.user_pref_filename, 'r') as f:
                config = json.load(f)
            # edit the data
            try:
                self.imshow_var_bool.set(config['imshow_var_bool'])
                self.add_timestamp_var_bool.set(config['add_timestamp_var_bool'])
                self.addTextOverlay_var_bool.set(config['addTextOverlay_var_bool'])
                self.path_var.set(config['path_var'])
                self.filename_var.set(config['filename_var'])
                self.scopeUseExtDrv_var_bool.set(config["use_externalDrv_var_bool"])
                self.use_inkSaver_var_bool.set(config["use_inkSaver_var_bool"])
                App.cls_var = config["target_gpib_address"]
                # self.target_gpib_address.set(config["target_gpib_address"])
            except:
                return self.write_user_pref()
        else:
            self.write_user_pref()

    def write_user_pref(self):
        self.update_addr_inApp()
        with open(self.user_pref_filename, 'w') as f:
            config = {"imshow_var_bool": self.imshow_var_bool.get(),
                      "add_timestamp_var_bool": self.add_timestamp_var_bool.get(),
                      "addTextOverlay_var_bool": self.addTextOverlay_var_bool.get(),
                      "path_var": self.path_var.get(),
                      "filename_var": self.filename_var.get(),
                      "use_externalDrv_var_bool": self.scopeUseExtDrv_var_bool.get(),
                      "use_inkSaver_var_bool": self.use_inkSaver_var_bool.get(),
                      "target_gpib_address": self.target_gpib_address.get()
                      }
            json.dump(config, f)

    def create_frame_gpib_scanner(self):
        self.newwindow = tk.Toplevel(self.master)
        self.gpibScannerObj = WindowGPIBScanner(self.newwindow)


    def get_acq_state(self):
        self.update_addr_inApp()
        try:
            rm = visa.ResourceManager()
            try:
                scope = rm.open_resource(self.target_gpib_address.get())
                self.sel_ch1_var_bool.set(value=int(scope.query('SELect:CH1?')[:-1]))
                self.sel_ch2_var_bool.set(value=int(scope.query('SELect:CH2?')[:-1]))
                self.sel_ch3_var_bool.set(value=int(scope.query('SELect:CH3?')[:-1]))
                self.sel_ch4_var_bool.set(value=int(scope.query('SELect:CH4?')[:-1]))
                acq_state = int(scope.query('ACQuire:STATE?')[:-1])
                print("scope acq state=", acq_state)
                self.acq_state_var_bool.set(acq_state)
                self.fastacq_var_bool.set(int(scope.query('FASTAcq:STATE?')))
                # orig_color = self.chkbox_fastacq.cget("background")
                if self.fastacq_var_bool.get():
                    self.chkbox_fastacq.configure(fg="Purple2")
                else:
                    self.chkbox_fastacq.configure(fg="black")
                # print("per", scope.query('DISplay:PERSistence?').rstrip())
                if scope.query('DISplay:PERSistence?').rstrip() == 'OFF':
                    self.persistence_var_bool.set(0)
                else:
                    self.persistence_var_bool.set(1)
                if self.acq_state_var_bool.get() == True:
                    self.btn_RunStop.configure(fg="green4")
                elif self.acq_state_var_bool.get() == False:
                    self.btn_RunStop.configure(fg="black")
                else:
                    # print("Cannot get Acq state")
                    self.status_var.set("Cannot get Acq state")
                scope.close()
            except Exception:
             rm.close()
        except ValueError:
            print("Cannot get Acq status-VISA driver Error")

    def get_scope_info(self):
        # self.update_addr_inApp()
        try:
            rm = visa.ResourceManager()
            try:
                with rm.open_resource(self.target_gpib_address.get()) as scope:
                    idn_query = scope.query('*IDN?')[:-1]
                    self.IDN_of_scope.set(idn_query)
                    idn_model_name = idn_query.split(",")[1]
                    self.appTitleText = "KW Scope Capture" + self.app_version + " Found:" + idn_model_name
                    self.master.title(self.appTitleText)
                    scope.close()
                rm.close()
                self.status_var.set(" tip: Use <Control> key + <Left> or <Right> arrow key to scale time division")
            except:
                pass
                messagebox.showinfo("Oops! Something changed!",
                                    "Unable to connect the device used last time.\n"
                                    "You could check:\n"
                                    "1. connection between the target device & your PC.\n"
                                    "2. Any change of GPIB address? \n"
                                    "Then use Tool>GPIB Scanner to Set New target Device.")
                # self.create_frame_gpib_scanner()
        except:
            self.appTitleText = self.appTitleText + "  [VISA driver Error]!"
            self.master.title(self.appTitleText)
            print("Cannot get scope info-VISA driver Error")

    def get_default_filename(self):
        # self.update_addr_inApp()
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
        # self.update_addr_inApp()
        self.get_scope_info()
        self.status_var.set("Try Talking to Scope")
        self.get_default_filename()
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                scope.timeout = self.visa_timeout_duration
                if self.scopeUseExtDrv_var_bool.get():
                    # test DPO2024B, DPO4104 OK
                    print("Alt way Scrshot")
                    if self.use_inkSaver_var_bool.get():
                        scope.write("SAVe:IMAGe:INKSaver ON")
                    else:
                        scope.write("SAVe:IMAGe:INKSaver OFF")
                    scope.write("SAVe:IMAGe:FILEFormat PNG")
                    # scope.write('FILESystem:MKDir \'E:\TempScrShot\'')
                    # scope.write('SAVE:IMAGe \"E:\TempScrShot\KWScrShotTemp.png\"')
                    scope.write("HARDCopy STARt")
                    # scope.write('*OPC?')
                    # scope.write('FILESystem:READFile \"E:\TempScrShot\KWScrShotTemp.png\"')
                    img_data = scope.read_raw()
                    # print(img_data)
                    # scope.write('FILESystem:DELEte \"E:\TempScrShot\KWScrShotTemp.png\"')
                else:
                    scope.write("HARDCopy:PORT FILE")
                    # Notice: CANNOT access C Drive root directly if scope use win10
                    scope.write('FILESystem:MKDir \'C:\TempScrShot(could be Deleted)\'')
                    scope.write('HARDCopy:FILEName  \'C:\TempScrShot(could be Deleted)\KWScrShot.png\'')
                    scope.write("HARDCopy STARt")
                    scope.query('*OPC?')
                    scope.write('FILESystem:READFile \'C:\TempScrShot(could be Deleted)\KWScrShot.png\'')
                    img_data = scope.read_raw()
                    scope.write('FILESystem:DELEte \'C:\TempScrShot(could be Deleted)\KWScrShot.png\'')
                    # print(img_data)



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
        except:
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
        # self.update_addr_inApp()
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
        # self.update_addr_inApp()
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                scope.write('*RST')
                scope.close()
            rm.close()
        except ValueError:
            print("Factory Reset Failed")
            self.status_var.set("Factory Reset, VISA ERROR")

    def scope_set_trigger_a(self):
        # self.update_addr_inApp()
        print("Into --scope_channel_select--")
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                scope.write('TRIGger:A SETLevel')
                scope.write('TRIGger:B SETLevel')
                scope.close()
            rm.close()
        except ValueError:
            print("Set Trig A failed")
            self.status_var.set("Set Trig A failed, VISA ERROR")

    def scope_channel_select(self):
        # self.update_addr_inApp()
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
        # self.update_addr_inApp()
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
        # self.update_addr_inApp()
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                if self.persistence_var_bool.get():
                    scope.write('DISplay:PERSistence INFPersist')
                else:
                    scope.write('DISplay:PERSistence OFF')
                scope.close()
            rm.close()
        except:
            print("cannot set Persistence")
            self.status_var.set("VISA driver Error")

    def btn_single_clicked(self):
        # self.update_addr_inApp()
        self.get_scope_info()
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                scope.write('ACQuire:STOPAFTER SEQUENCE')
                scope.write('ACQ:STATE ON')
            scope.close()
            rm.close()
        except:
            print("cannot do Single shot")
            self.status_var.set("VISA driver Error")

    def btn_clear_clicked(self, *args):
        # self.update_addr_inApp()
        self.get_scope_info()
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                ScopeModel = self.IDN_of_scope.get().split(',')
                print(ScopeModel)
                isCModel = False
                try:
                    if ScopeModel[1][-1] == 'C':
                        isCModel = True
                        print('isCModel=', isCModel)
                    else:
                        isCModel = False
                except IndexError:
                    print("var \"self.IDN_of_scope[1][-1]\" does not exist.")
                print("Clear Btn clicked")

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
        except:
            print("cannot clear scope-VISA driver Error")
            self.status_var.set("VISA driver Error")

    def btn_runstop_clicked(self, *args):
        # self.update_addr_inApp()
        self.get_scope_info()
        print("Run/Stop Btn clicked")
        # print("obj_[selected_device_addr]->", self.gpibScannerObj.selected_device_addr)
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
        # self.update_addr_inApp()
        self.get_scope_info()
        folder = self.path_var.get()
        print("Capture Btn clicked, save folder", folder)
        self.get_shot_scope()

    # def btn_countdown_capture_clicked(self):
    #     folder = self.path_var.get()
    #     print("Capture Btn clicked, save folder", folder)
    #     self.get_shot_scope()

    def horizontal_scale(self, event):
        # self.update_addr_inApp()
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
                        scope.write('HORizontal:RESOlution 2e5')
                elif event.keysym == 'Right':
                    if self.closest_index > 1:
                        self.target_index = self.closest_index - 1
                        scope.write('HORizontal:MAIn:SCAle ' + str(self.scaleList[self.target_index]))
                        scope.write('HORizontal:RESOlution 2e5')
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
    root.protocol("WM_DELETE_WINDOW", app.ask_quit)
    root.mainloop()


if __name__ == '__main__':
    mainApp()
