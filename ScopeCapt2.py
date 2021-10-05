from datetime import datetime  # std library
import pyvisa as visa  # https://pyvisa.readthedocs.org/en/stable/
import os
import re
from pathlib import Path
import atexit
from PIL import Image, ImageTk
from io import BytesIO, StringIO
import numpy as np
import cv2
import base64
import imgBase64 as myIcon
import time
import tkinter as tk
from tkinter import ttk, Entry, messagebox, filedialog, IntVar, DoubleVar, Menu, PhotoImage
from idlelib.tooltip import Hovertip
# https://pythonguides.com/python-tkinter-menu-bar/
# https://coderslegacy.com/python/list-of-tkinter-widgets/
import threading
import json
import requests
import webbrowser


class mySpinbox(tk.Spinbox):
    def __init__(self, *args, **kwargs):
        tk.Spinbox.__init__(self, *args, **kwargs)
        self.bind('<MouseWheel>', self.mouseWheel)
        self.bind('<Button-4>', self.mouseWheel)
        self.bind('<Button-5>', self.mouseWheel)

    #     self.bind('<Return>', self.returnKeyPressed)
    #
    # def returnKeyPressed(self, event):
    #     print("Return pressed in mySpinbox")
    #     self.invoke('buttondown')
    #     self.invoke('buttonup')

    def mouseWheel(self, event):
        if event.num == 5 or event.delta < 0:
            self.focus_set()
            self.invoke('buttondown')
        elif event.num == 4 or event.delta > 0:
            self.focus_set()
            self.invoke('buttonup')


class WindowGPIBScanner:
    isOktoUpdateState = True

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
        self.sel_btn = tk.Button(self.frame, text='Set Selected as target device', width=25, command=self.selected_item)
        # self.quitButton = tk.Button(self.frame, text='Quit', width=25, command=self.close_window)
        self.scanButton.pack()
        # self.quitButton.pack()

        self.sel_btn.pack(side='bottom', pady=3)
        self.sel_btn["state"] = "disabled"
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
            print("Selected", i, selected_item)
            print("selected Device Addr=", i, self.selected_device_addr)
            # print("")
            App.cls_var = self.selected_device_addr
        return self.close_window()

    def close_window(self):
        WindowGPIBScanner.isOktoUpdateState = True
        self.scanthread.join()
        self.frame.destroy()
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
                addr = ""
            list_item_text = (vendor + ", " + model_name + ", address: " + addr)
            self.listbox.insert(i, list_item_text)

    def scan_gpib(self):
        WindowGPIBScanner.isOktoUpdateState = False
        self.sel_btn["state"] = "disabled"
        self.scanButton["state"] = "disabled"
        print("scan_gpib")
        """
        list name & address of found GPIB devices, get user prompt device
        """
        self.found_device_with_name = []
        try:
            rm = visa.ResourceManager()
            ls_res = rm.list_resources()  # query='?*'
            for addr in ls_res:
                title = "Scanning: " + str(int(((ls_res.index(addr) + 1) / (len(ls_res))) * 100)) + "%"
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
                    # self.found_device_with_name.append((idn, addr))
                except Exception as e:
                    pass
                print("gotoupdate")
                self.update_device_listbox()
            rm.close()
        except ValueError:
            print("Scan gpib Error")
        self.scanButton["state"] = "normal"
        self.sel_btn["state"] = "normal"
        self.master.title("GPIB Scanner [finished!]")


class App:
    cls_var = ""

    def __init__(self, master):
        self.master = master
        self.frame = tk.Frame(self.master)

        self.app_version = 2.2
        # self.master.geometry("+%d+%d" % (self.frame.window_start_x, self.frame.window_start_y))
        self.appTitleText = "KW Scope Capture" + "v" + str(self.app_version)
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
        self.enable_cursor_var_bool = IntVar(value=0)
        self.cursor_type_var = tk.StringVar()
        self.cursor_type_var.set('HBar')

        # User Preference var
        self.imshow_var_bool = IntVar(value=0)
        self.add_timestamp_var_bool = IntVar(value=1)
        self.addTextOverlay_var_bool = IntVar(value=0)
        self.path_var = tk.StringVar()
        self.path_var.set(os.getcwd())
        self.filename_var.set('Name_File_Here')

        self.use_inkSaver_var_bool = IntVar(value=0)
        self.cursor_mode = IntVar(value=0)
        self.trig_ch = tk.StringVar()
        self.trig_ch.set('1')
        self.trig_edge = tk.StringVar()
        self.trig_edge.set('Rise')

        self.overwrite_bool = True
        self.IDN_of_scope.set('')
        self.scope_series_num = 0
        self.ch_available = 1
        self.dt = datetime.now()
        self.visa_timeout_duration = 10000  # in ms
        self.offset_err_cnt = 0

        self.spinbox_cur1_x_increment = 0.01
        self.spinbox_cur2_x_increment = 0.01
        self.spinbox_cur1_y_increment = 0.01
        self.spinbox_cur2_y_increment = 0.01
        self.is_cur_use_fine_step = False

        self.ch1_pos = DoubleVar(value=0.0)
        self.ch1_offset = DoubleVar(value=0.0)
        self.ch2_pos = DoubleVar(value=0.0)
        self.ch2_offset = DoubleVar(value=0.0)
        self.ch3_pos = DoubleVar(value=0.0)
        self.ch3_offset = DoubleVar(value=0.0)
        self.ch4_pos = DoubleVar(value=0.0)
        self.ch4_offset = DoubleVar(value=0.0)

        self.cur_x1_doublevar = DoubleVar(value=0.0)
        self.cur_x2_doublevar = DoubleVar(value=0.0)
        self.cur_y1_doublevar = DoubleVar(value=0.0)
        self.cur_y2_doublevar = DoubleVar(value=0.0)

        self.pause_get_status_thread = False

        # --------------row 0
        # blanklabel1 = tk.Label(self.frame, text=" ")
        # blanklabel1.grid(row=0, column=0, sticky='W', pady=1)

        # --------------row 1
        # blanklabel2 = tk.Label(self.frame, text=" ")
        # blanklabel2.grid(row=1, column=0, sticky='W', pady=1)
        label_entry_dir = tk.Label(self.frame, text="Save to :")
        label_entry_dir.grid(row=0, column=0, sticky='W', pady=0)
        self.E_dir = tk.Entry(self.frame, textvariable=self.path_var)
        self.E_dir.grid(row=0, column=1, columnspan=9, padx=1, pady=0, sticky='we')
        label_entry_dir = tk.Label(self.frame, text="Filename:")
        label_entry_dir.grid(row=1, column=0, sticky='W', pady=0)
        self.E_filename = tk.Entry(self.frame, textvariable=self.filename_var)
        self.E_filename.grid(row=1, column=1, columnspan=9, padx=1, pady=0, sticky='we')

        btn_prompt_dir = tk.Button(self.frame, text="Prompt folder", command=self.prompt_path)
        btn_prompt_dir.grid(row=0, column=10, padx=2, pady=0, columnspan=2, rowspan=2, sticky='nswe')

        # --------------row 2

        # --------------row 3
        self.labelFr_trig = tk.LabelFrame(self.frame, text="Trigger CH")
        self.labelFr_trig.grid(row=3, column=5, padx=5, columnspan=3, pady=0, sticky='w')

        self.trig_ch_combobox = ttk.Combobox(self.labelFr_trig, state='readonly', textvariable=None, width=1)
        self.trig_ch_combobox['values'] = ('1', '2', '3', '4')
        self.trig_ch_combobox.grid(row=4, column=5, padx=5, pady=1)
        self.trig_ch_combobox.current(0)
        #
        self.trig_edge_combobox = ttk.Combobox(self.labelFr_trig, state='readonly', textvariable=None, width=4)
        self.trig_edge_combobox['values'] = ('Rise', 'Fall', 'Either')
        self.trig_edge_combobox.grid(row=4, column=6, padx=5, pady=1)
        self.trig_edge_combobox.current(0)

        self.btn_trig50 = tk.Button(self.labelFr_trig, text="Set", command=self.scope_set_trigger_a)
        self.btn_trig50.grid(row=4, column=7, padx=5, pady=1)

        # --------------row4
        self.labelFr_periss = tk.LabelFrame(self.frame, text="Display")
        self.labelFr_periss.grid(row=3, column=1, padx=5, columnspan=4, pady=0, sticky='w')
        self.chkbox_persistence = tk.Checkbutton(self.labelFr_periss, text='Persistence',
                                                 variable=self.persistence_var_bool,
                                                 onvalue=1, offvalue=0, command=self.set_persistence)
        self.chkbox_persistence.grid(row=3, column=1, columnspan=3, padx=0, pady=1, sticky='w')
        self.chkbox_fastacq = tk.Checkbutton(self.labelFr_periss, text='FastAcq',
                                             variable=self.fastacq_var_bool,
                                             onvalue=1, offvalue=0, command=self.trigger_fstacq)
        self.chkbox_fastacq.grid(row=3, column=4, columnspan=3, padx=0, pady=1, sticky='w')
        self.label_acqnum = tk.Label(self.labelFr_periss, text='Acq#')
        self.label_acqnum.grid(row=3, column=7, columnspan=3, padx=0, pady=1, sticky='w')
        # self.chkbox_cursor = tk.Checkbutton(self.labelFr_periss, text='cursor',
        #                                     variable=self.enable_cursor_var_bool,
        #                                     onvalue=1, offvalue=0, command=None)
        # self.chkbox_cursor.grid(row=3, column=7, columnspan=3, padx=0, pady=1, sticky='w')

        self.labelFr_time_scale = tk.LabelFrame(self.frame, text="Time/div")
        self.labelFr_time_scale.grid(row=3, column=8, padx=5, columnspan=5, pady=0, sticky='We')
        self.l = tk.Button(self.labelFr_time_scale, text="◀ZoomOut", command=self.horizontal_zoom_out)
        self.l.grid(row=4, column=0, columnspan=3, padx=3, pady=1, sticky='we')
        self.r = tk.Button(self.labelFr_time_scale, text="ZoomIn▶", command=self.horizontal_zoom_in)
        self.r.grid(row=4, column=4, columnspan=3, padx=3, pady=1, sticky='we')

        # ▼▲▶◀↶⤾⟲
        # color yellow=#F7F700, cyan=#00F7F8, magenta=#FF33FF, green=#00F700
        self.labelFr_ch1 = tk.LabelFrame(self.frame, text="CH1")
        self.labelFr_ch1.grid(row=5, column=1, padx=3)
        self.labelFr_ch2 = tk.LabelFrame(self.frame, text="CH2")
        self.labelFr_ch2.grid(row=5, column=4, padx=3)
        self.labelFr_ch3 = tk.LabelFrame(self.frame, text="CH3")
        self.labelFr_ch3.grid(row=5, column=7, padx=3)
        self.labelFr_ch4 = tk.LabelFrame(self.frame, text="CH4")
        self.labelFr_ch4.grid(row=5, column=10, padx=3)

        # ch1 labelFrame
        label_pos_ch1 = tk.Label(self.labelFr_ch1, text="Position")
        label_pos_ch1.grid(row=5, column=1, padx=0, pady=1, sticky='w')
        self.spinbox_pos_ch1 = mySpinbox(self.labelFr_ch1, from_=-5, to=5, increment=.08, justify=tk.CENTER,
                                         command=lambda: self.adjust_pos(ch=1), width=7, textvariable=self.ch1_pos)
        self.spinbox_pos_ch1.grid(row=5, column=2, padx=1, pady=1, sticky='w')
        self.spinbox_pos_ch1.bind('<Return>', lambda i: (self.spinbox_pos_ch1.invoke('buttondown'),
                                                         self.spinbox_pos_ch1.invoke('buttonup'),
                                                         self.frame.focus_force()))

        label_offs_ch1 = tk.Label(self.labelFr_ch1, text="Offset(V)", command=None)
        label_offs_ch1.grid(row=6, column=1, padx=0, pady=1, sticky='w')
        self.spinbox_offset_ch1 = mySpinbox(self.labelFr_ch1, from_=-9.3, to=9.3, increment=.004, justify=tk.CENTER,
                                            command=lambda: self.adjust_offset(ch=1), width=7,
                                            textvariable=self.ch1_offset, takefocus=True)
        self.spinbox_offset_ch1.grid(row=6, column=2, padx=1, pady=1, sticky='e')
        self.spinbox_offset_ch1.bind('<Return>', lambda i: (self.spinbox_offset_ch1.invoke('buttondown'),
                                                            self.spinbox_offset_ch1.invoke('buttonup'),
                                                            self.frame.focus_force()))

        # ch2 labelFrame
        label_pos_ch2 = tk.Label(self.labelFr_ch2, text="Position")
        label_pos_ch2.grid(row=5, column=5, padx=0, pady=1, sticky='w')
        self.spinbox_pos_ch2 = mySpinbox(self.labelFr_ch2, from_=-5, to=5, increment=.08, justify=tk.CENTER,
                                         command=lambda: self.adjust_pos(ch=2), width=7, textvariable=str(self.ch2_pos))
        self.spinbox_pos_ch2.grid(row=5, column=6, padx=1, pady=1, sticky='w')
        self.spinbox_pos_ch2.bind('<Return>', lambda i: (self.spinbox_pos_ch2.invoke('buttondown'),
                                                         self.spinbox_pos_ch2.invoke('buttonup'),
                                                         self.frame.focus_force()))

        label_offs_ch2 = tk.Label(self.labelFr_ch2, text="Offset(V)", command=None)
        label_offs_ch2.grid(row=6, column=5, padx=0, pady=1, sticky='w')
        self.spinbox_offset_ch2 = mySpinbox(self.labelFr_ch2, from_=-9.3, to=9.3, increment=.004, justify=tk.CENTER,
                                            command=lambda: self.adjust_offset(ch=2), width=7,
                                            textvariable=str(self.ch2_offset))
        self.spinbox_offset_ch2.grid(row=6, column=6, padx=1, pady=1, sticky='e')
        self.spinbox_offset_ch2.bind('<Return>', lambda i: (self.spinbox_offset_ch2.invoke('buttondown'),
                                                            self.spinbox_offset_ch2.invoke('buttonup'),
                                                            self.frame.focus_force()))

        # ch3 labelFrame
        label_pos_ch3 = tk.Label(self.labelFr_ch3, text="Position")
        label_pos_ch3.grid(row=5, column=8, padx=0, pady=1, sticky='w')
        self.spinbox_pos_ch3 = mySpinbox(self.labelFr_ch3, from_=-5, to=5, increment=.08, justify=tk.CENTER,
                                         command=lambda: self.adjust_pos(ch=3), width=7, textvariable=str(self.ch3_pos))
        self.spinbox_pos_ch3.grid(row=5, column=9, padx=1, pady=1, sticky='w')
        self.spinbox_pos_ch3.bind('<Return>', lambda i: (self.spinbox_pos_ch3.invoke('buttondown'),
                                                         self.spinbox_pos_ch3.invoke('buttonup'),
                                                         self.frame.focus_force()))

        label_offs_ch3 = tk.Label(self.labelFr_ch3, text="Offset(V)", command=None)
        label_offs_ch3.grid(row=6, column=8, padx=0, pady=1, sticky='w')
        self.spinbox_offset_ch3 = mySpinbox(self.labelFr_ch3, from_=-9.3, to=9.3, increment=.002, justify=tk.CENTER,
                                            command=lambda: self.adjust_offset(ch=3), width=7,
                                            textvariable=str(self.ch3_offset))
        self.spinbox_offset_ch3.grid(row=6, column=9, padx=1, pady=1, sticky='e')
        self.spinbox_offset_ch3.bind('<Return>', lambda i: (self.spinbox_offset_ch3.invoke('buttondown'),
                                                            self.spinbox_offset_ch3.invoke('buttonup'),
                                                            self.frame.focus_force()))

        # ch4 labelFrame
        label_pos_ch4 = tk.Label(self.labelFr_ch4, text="Position")
        label_pos_ch4.grid(row=0, column=0, padx=0, pady=1, sticky='w')
        self.spinbox_pos_ch4 = mySpinbox(self.labelFr_ch4, from_=-5, to=5, increment=.08, justify=tk.CENTER,
                                         command=lambda: self.adjust_pos(ch=4), width=7, textvariable=str(self.ch4_pos))
        self.spinbox_pos_ch4.grid(row=0, column=1, padx=1, pady=1, sticky='w')
        self.spinbox_pos_ch4.bind('<Return>', lambda i: (self.spinbox_pos_ch4.invoke('buttondown'),
                                                         self.spinbox_pos_ch4.invoke('buttonup'),
                                                         self.frame.focus_force()))

        label_offs_ch4 = tk.Label(self.labelFr_ch4, text="Offset(V)", command=None)
        label_offs_ch4.grid(row=1, column=0, padx=0, pady=1, sticky='w')
        self.spinbox_offset_ch4 = mySpinbox(self.labelFr_ch4, from_=-9.3, to=9.3, increment=.002, justify=tk.CENTER,
                                            command=lambda: self.adjust_offset(ch=4), width=7,
                                            textvariable=str(self.ch4_offset))
        self.spinbox_offset_ch4.grid(row=1, column=1, padx=1, pady=1, sticky='e')
        self.spinbox_offset_ch4.bind('<Return>', lambda i: (self.spinbox_offset_ch4.invoke('buttondown'),
                                                            self.spinbox_offset_ch4.invoke('buttonup'),
                                                            self.frame.focus_force()))

        self.btn_ch1_up = tk.Button(self.labelFr_ch1, text="▲", command=lambda: self.ch_scale_adj(ch=1, updn='up'))
        self.btn_ch1_up.grid(row=5, column=3, padx=0, pady=1)
        self.btn_ch1_down = tk.Button(self.labelFr_ch1, text="▼", command=lambda: self.ch_scale_adj(ch=1, updn='dn'))
        self.btn_ch1_down.grid(row=6, column=3, padx=0, pady=1)

        self.btn_ch2_up = tk.Button(self.labelFr_ch2, text="▲", command=lambda: self.ch_scale_adj(ch=2, updn='up'))
        self.btn_ch2_up.grid(row=5, column=7, padx=0, pady=1)
        self.btn_ch2_down = tk.Button(self.labelFr_ch2, text="▼", command=lambda: self.ch_scale_adj(ch=2, updn='dn'))
        self.btn_ch2_down.grid(row=6, column=7, padx=0, pady=1)

        self.btn_ch3_up = tk.Button(self.labelFr_ch3, text="▲", command=lambda: self.ch_scale_adj(ch=3, updn='up'))
        self.btn_ch3_up.grid(row=5, column=10, padx=0, pady=1)
        self.btn_ch3_down = tk.Button(self.labelFr_ch3, text="▼", command=lambda: self.ch_scale_adj(ch=3, updn='dn'))
        self.btn_ch3_down.grid(row=6, column=10, padx=0, pady=1)

        self.btn_ch4_up = tk.Button(self.labelFr_ch4, text="▲", command=lambda: self.ch_scale_adj(ch=4, updn='up'))
        self.btn_ch4_up.grid(row=0, column=2, padx=0, pady=1)
        self.btn_ch4_down = tk.Button(self.labelFr_ch4, text="▼", command=lambda: self.ch_scale_adj(ch=4, updn='dn'))
        self.btn_ch4_down.grid(row=1, column=2, padx=0, pady=1)

        # --------------row 7
        self.btn_capture = tk.Button(self.frame, text=" Take ScreenShot ", command=self.btn_capture_clicked)
        self.btn_capture.grid(row=7, column=1, padx=3, pady=2, columnspan=3)
        self.btn_RunStop = tk.Button(self.frame, text="Run/Stop (Ctrl+⮐)", command=self.btn_runstop_clicked)
        self.btn_RunStop.grid(row=7, column=3, padx=3, pady=2, columnspan=3)
        self.btn_Single = tk.Button(self.frame, text=" Single Acq ", command=self.btn_single_clicked)
        self.btn_Single.grid(row=7, column=7, padx=3, pady=2, columnspan=2)
        self.btn_Clear = tk.Button(self.frame, text="Clear (Ctrl+Del)", command=self.btn_clear_clicked)
        self.btn_Clear.grid(row=7, column=8, padx=3, pady=2, columnspan=3)

        self.labelFr_cursor = tk.LabelFrame(self.frame, text="Cursor")
        self.labelFr_cursor.grid(row=0, column=14, columnspan=3, rowspan=9, padx=3, sticky='ns')
        self.cursor_type_combobox = ttk.Combobox(self.labelFr_cursor, state='readonly', textvariable=None, width=6)
        self.cursor_type_combobox['values'] = ('OFF', 'HBar', 'VBar', 'Wave', 'Screen')
        self.cursor_type_combobox.grid(row=0, column=0, padx=2, pady=0)
        self.cursor_type_combobox.current(0)

        # ✜
        self.btn_cur_set = tk.Button(self.labelFr_cursor, text="set", command=self.adjust_cur)
        self.btn_cur_set.grid(row=0, column=1, padx=1, pady=0)

        self.labelFr_cursor_one = tk.LabelFrame(self.labelFr_cursor, text="Cursor1")
        self.labelFr_cursor_one.grid(row=1, column=0, padx=1, columnspan=2, rowspan=3)
        label_cur1_ch = tk.Label(self.labelFr_cursor_one, text="CH", command=None)
        label_cur1_ch.grid(row=0, column=0, padx=0, pady=1, sticky='w')
        self.cursor1_ch_combobox = ttk.Combobox(self.labelFr_cursor_one, state='readonly', textvariable=None, width=1)
        self.cursor1_ch_combobox['values'] = ('1', '2', '3', '4')
        self.cursor1_ch_combobox.grid(row=0, column=1, padx=1, pady=1, sticky='w')
        self.cursor1_ch_combobox.current(0)
        label_cur1_x = tk.Label(self.labelFr_cursor_one, text="X", command=None)
        label_cur1_x.grid(row=1, column=0, padx=0, pady=1, sticky='w')
        self.spinbox_cur1_x = mySpinbox(self.labelFr_cursor_one, from_=-50, to=50, increment=.01, justify=tk.CENTER,
                                        command=lambda: self.adjust_cur(), width=7,
                                        textvariable=self.cur_x1_doublevar)
        self.spinbox_cur1_x.grid(row=1, column=1, padx=1, pady=1, sticky='w')
        self.spinbox_cur1_x.bind('<Button-3>', lambda i: (self.cursor_step_set(fine=True)))
        self.spinbox_cur1_x.bind('<ButtonRelease-3>', lambda i: (self.cursor_step_set(fine=False)))
        self.spinbox_cur1_x.bind('<Return>', lambda i: (self.spinbox_cur1_x.invoke('buttondown'),
                                                         self.spinbox_cur1_x.invoke('buttonup'),
                                                         self.frame.focus_force()))
        myTip_cur1_x = Hovertip(self.spinbox_cur1_x, 'Use the Right mouse\nbutton to fine tune.',
                                hover_delay=1000)

        label_cur1_y = tk.Label(self.labelFr_cursor_one, text="Y", command=None)
        label_cur1_y.grid(row=2, column=0, padx=0, pady=1, sticky='w')
        self.spinbox_cur1_y = mySpinbox(self.labelFr_cursor_one, from_=-50, to=50, increment=.01, justify=tk.CENTER,
                                        command=lambda: self.adjust_cur(), width=7,
                                        textvariable=self.cur_y1_doublevar)
        self.spinbox_cur1_y.grid(row=2, column=1, padx=1, pady=1, sticky='w')
        self.spinbox_cur1_y.bind('<Button-3>', lambda i: (self.cursor_step_set(fine=True)))
        self.spinbox_cur1_y.bind('<ButtonRelease-3>', lambda i: (self.cursor_step_set(fine=False)))
        self.spinbox_cur1_y.bind('<Return>', lambda i: (self.spinbox_cur1_y.invoke('buttondown'),
                                                        self.spinbox_cur1_y.invoke('buttonup'),
                                                        self.frame.focus_force()))
        myTip_cur1_y = Hovertip(self.spinbox_cur1_y, 'Use the Right mouse\nbutton to fine tune.',
                                hover_delay=1000)

        self.labelFr_cursor_two = tk.LabelFrame(self.labelFr_cursor, text="Cursor2")
        self.labelFr_cursor_two.grid(row=4, column=0, padx=3, pady=0, columnspan=2, rowspan=3)
        label_cur2_ch = tk.Label(self.labelFr_cursor_two, text="CH", command=None)
        label_cur2_ch.grid(row=0, column=0, padx=0, pady=1, sticky='w')
        self.cursor2_ch_combobox = ttk.Combobox(self.labelFr_cursor_two, state='readonly', textvariable=None, width=1)
        self.cursor2_ch_combobox['values'] = ('1', '2', '3', '4')
        self.cursor2_ch_combobox.grid(row=0, column=1, padx=1, pady=1, sticky='w')
        self.cursor2_ch_combobox.current(0)
        label_cur2_x = tk.Label(self.labelFr_cursor_two, text="X", command=None)
        label_cur2_x.grid(row=1, column=0, padx=0, pady=1, sticky='w')
        self.spinbox_cur2_x = mySpinbox(self.labelFr_cursor_two, from_=-50, to=50, increment=.5, justify=tk.CENTER,
                                        command=lambda: self.adjust_cur(), width=7,
                                        textvariable=self.cur_x2_doublevar)
        self.spinbox_cur2_x.grid(row=1, column=1, padx=1, pady=1, sticky='w')
        self.spinbox_cur2_x.bind('<Button-3>', lambda i: (self.cursor_step_set(fine=True)))
        self.spinbox_cur2_x.bind('<ButtonRelease-3>', lambda i: (self.cursor_step_set(fine=False)))
        self.spinbox_cur2_x.bind('<Return>', lambda i: (self.spinbox_cur2_x.invoke('buttondown'),
                                                        self.spinbox_cur2_x.invoke('buttonup'),
                                                        self.frame.focus_force()))
        myTip_cur2_x = Hovertip(self.spinbox_cur2_x, 'Use the Right mouse\nbutton to fine tune.',
                                hover_delay=1000)

        label_cur2_y = tk.Label(self.labelFr_cursor_two, text="Y", command=None)
        label_cur2_y.grid(row=2, column=0, padx=0, pady=1, sticky='w')
        self.spinbox_cur2_y = mySpinbox(self.labelFr_cursor_two, from_=-50, to=50, increment=.01, justify=tk.CENTER,
                                        command=lambda: self.adjust_cur(), width=7,
                                        textvariable=self.cur_y2_doublevar)
        self.spinbox_cur2_y.grid(row=2, column=1, padx=1, pady=1, sticky='w')
        self.spinbox_cur2_y.bind('<Button-3>', lambda i: (self.cursor_step_set(fine=True)))
        self.spinbox_cur2_y.bind('<ButtonRelease-3>', lambda i: (self.cursor_step_set(fine=False)))
        self.spinbox_cur2_y.bind('<Return>', lambda i: (self.spinbox_cur2_y.invoke('buttondown'),
                                                        self.spinbox_cur2_y.invoke('buttonup'),
                                                        self.frame.focus_force()))
        myTip_cur2_y = Hovertip(self.spinbox_cur2_y, 'Use the Right mouse\nbutton to fine tune.', hover_delay=1000)


        # --------------row 8, status bar
        status_bar = tk.Label(self.frame, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=8, column=0, columnspan=14, sticky='we')

        self.closest_timediv_index = 0
        self.time_scaleList = [1e-9, 2e-9, 5e-9,
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

        self.vertical_scaleList = [1e-3, 2e-3, 3e-3,
                                   4e-3, 5e-3, 6e-3,
                                   7e-3, 8e-3, 9e-3,
                                   1e-2, 2e-2, 3e-2,
                                   4e-2, 5e-2, 6e-2,
                                   7e-2, 8e-2, 9e-2,
                                   1e-1, 2e-1, 3e-1,
                                   4e-1, 5e-1, 6e-1,
                                   7e-1, 8e-1, 9e-1,
                                   1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        # --------------MenuBar
        menubar = Menu(self.master)
        self.master.config(menu=menubar)

        filemenu = Menu(menubar, tearoff=False)
        scopemenu = Menu(menubar, tearoff=False)
        miscmenu = Menu(menubar, tearoff=False)
        toolmenu = Menu(menubar, tearoff=False)
        helpmenu = Menu(menubar, tearoff=False)

        file_submenu_save_setup = Menu(filemenu, tearoff=False)
        filemenu.add_cascade(label='Save Setup', menu=file_submenu_save_setup, underline=0)
        file_submenu_save_setup.add_command(label="Slot 1", command=lambda: self.save_setup_slot(slot_num=1))
        file_submenu_save_setup.add_command(label="Slot 2", command=lambda: self.save_setup_slot(slot_num=2))
        file_submenu_save_setup.add_command(label="Slot 3", command=lambda: self.save_setup_slot(slot_num=3))
        file_submenu_save_setup.add_command(label="Slot 4", command=lambda: self.save_setup_slot(slot_num=4))
        file_submenu_save_setup.add_command(label="Slot 5", command=lambda: self.save_setup_slot(slot_num=5))

        file_submenu_recall_setup = Menu(filemenu, tearoff=False)
        filemenu.add_cascade(label='Recall Setup', menu=file_submenu_recall_setup, underline=0)
        file_submenu_recall_setup.add_command(label="Slot 1", command=lambda: self.recall_setup_slot(slot_num=1))
        file_submenu_recall_setup.add_command(label="Slot 2", command=lambda: self.recall_setup_slot(slot_num=2))
        file_submenu_recall_setup.add_command(label="Slot 3", command=lambda: self.recall_setup_slot(slot_num=3))
        file_submenu_recall_setup.add_command(label="Slot 4", command=lambda: self.recall_setup_slot(slot_num=4))
        file_submenu_recall_setup.add_command(label="Slot 5", command=lambda: self.recall_setup_slot(slot_num=5))

        filemenu.add_command(label="Check App Updates", underline=0, command=self.check_app_update)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", underline=0, command=self.ask_quit)

        miscmenu.add_checkbutton(label="Add TimeStamp postfix to filename", onvalue=1, offvalue=0,
                                 variable=self.add_timestamp_var_bool)
        miscmenu.add_checkbutton(label="Show Image after ScreenShot", onvalue=1, offvalue=0,
                                 variable=self.imshow_var_bool)
        miscmenu.add_checkbutton(label="Add Text overlay on ScreenShot", onvalue=1, offvalue=0,
                                 variable=self.addTextOverlay_var_bool)
        miscmenu.add_checkbutton(label="Enable Ink Saver", onvalue=1, offvalue=0,
                                 variable=self.use_inkSaver_var_bool)

        scope_submenu = Menu(scopemenu, tearoff=False)

        scope_submenu.add_checkbutton(label="CH 1", onvalue=1, offvalue=0, variable=self.sel_ch1_var_bool,
                                      command=self.scope_channel_select)
        scope_submenu.add_checkbutton(label="CH 2", onvalue=1, offvalue=0, variable=self.sel_ch2_var_bool,
                                      command=self.scope_channel_select)
        scope_submenu.add_checkbutton(label="CH 3", onvalue=1, offvalue=0, variable=self.sel_ch3_var_bool,
                                      command=self.scope_channel_select)
        scope_submenu.add_checkbutton(label="CH 4", onvalue=1, offvalue=0, variable=self.sel_ch4_var_bool,
                                      command=self.scope_channel_select)

        scopemenu.add_cascade(label='Enable CH', menu=scope_submenu, underline=0)
        # scopemenu.add_checkbutton(label="Use FastAcq", onvalue=1, offvalue=0, variable=self.fastacq_var_bool,
        #                           command=self.trigger_fstacq)
        # scopemenu.add_checkbutton(label="Use Persistence", onvalue=1, offvalue=0, variable=self.persistence_var_bool,
        #                           command=self.set_persistence)
        scopemenu.add_separator()
        scopemenu.add_command(label="Exec. AutoSet", command=self.scope_execute_autoset)
        scopemenu.add_command(label="Exec. SPC", command=self.scope_execute_spc)
        scopemenu.add_command(label="Recall Factory Settings", command=self.scope_factory_reset)

        toolmenu.add_command(label="GPIB Scanner", command=self.create_frame_gpib_scanner)

        helpmenu.add_command(label="tips", underline=0, command=lambda: messagebox.showinfo("tips",
                                                                                            "Use <Control>+<Left> & <Control>+<Right> arrow key to scale time division"))

        helpmenu.add_command(label="About", underline=0, command=lambda:
        messagebox.showinfo("About this program", "KW ScopeCapt " + " Version:" + str(self.app_version)
                            + "\n\nIcons made by [smashicons.com]."
                            + "\n'OpenCV' is licensed under the [Apache 2 License]."
                            + "\n'numpy' is licensed under the [NumPy license]."
                            + "\n'pyvisa' is licensed under the [MIT License]."
                            + "\n'PIL' is licensed under open the [source HPND License]."
                            + "\n\nTHE APPLICATIONS IS PROVIDED “AS IS” WITHOUT ANY WARRANTIES."
                            + "\n\nYOUR USAGE OF THE APPLICATIONS IS AT YOUR OWN RISK. OWNER AND ANY OF ITS CONTRACTORS,"
                            + "\nWHO PARTICIPATED IN PROVIDING THE FUNCTIONALITY OF THE APPLICATIONS EXPRESSLY DISCLAIM ANY WARRANTY."
                            + "\n\n**Some of functions of the Applications can be temporarily unavailable."
                            ))

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

        if len(self.target_gpib_address.get()) > 1:
            self.update_addr_inApp()
            print("ReadOut_target-addr=", self.target_gpib_address.get())
            # self.get_scope_info()
            self.get_acq_state()
        else:
            messagebox.showinfo("First time Huh?",
                                "Target device record not found\nUse Tool>GPIB Scanner to Set target Device.")
            # self.create_frame_gpib_scanner()

        # !!! add parameter:[daemon=True] to prevent ghost thread!!!
        self.update_scope_thread = threading.Thread(target=self.task_update_device_state, daemon=True)
        self.update_scope_thread.start()
        
    def validate_spinbox(self, new_value):
        # Returning True allows the edit to happen, False prevents it.
        return new_value.isdigit()

    def task_update_device_state(self):
        while 1:
            if WindowGPIBScanner.isOktoUpdateState:
                try:
                    # print("Thread: check for updates")
                    self.update_addr_inApp()
                    self.get_acq_state()
                    self.master.update_idletasks()
                    time.sleep(0.5)
                except Exception as e:
                    print("task update state->", e)
        # messagebox.showerror("Failed!", "Failed to establish connection between instrument and PC."
        #                          + "\nCheck either NI-VISA driver installation or wiring."
        #                          + "\nThen restart this App.")

    def update_addr_inApp(self):
        # print("APP __class__.cls_var=")
        # print(self.__class__.cls_var)
        self.target_gpib_address.set(self.__class__.cls_var)
        # print("self.target_gpib_address->get()=")
        # print(self.target_gpib_address.get())

    def ask_quit(self):
        # if messagebox.askokcancel("Quit", "Do you want to quit?"):
        #     # file must be saved before destroy main frame.
        #     self.write_user_pref()
        #     self.master.destroy()
        #     # self.frame.destroy()
        #     # exit()
        self.write_user_pref()
        self.master.destroy()


    def at_exit(self):
        try:
            pass
        except:
            pass

    def onKey(self, event):
        print("On key")

    def check_app_update(self):
        self.check_app_update_thread = threading.Thread(target=self.task_check_app_update, daemon=True)
        self.check_app_update_thread.start()

    def task_check_app_update(self):
        url_api = 'https://api.github.com/repos/kw81634dr/VISAGUI/releases/latest'
        url_release = 'https://github.com/kw81634dr/VISAGUI/releases/latest'
        response = requests.get(url_api)
        latest_release_float = float((response.json()["name"])[1:])
        print(response.json())
        # response = requests.get("",
        #                         headers={"PRIVATE-TOKEN": ""})
        # print("GitLab-Version=", response.json()[0]['name'])
        if latest_release_float > self.app_version:
            print("there's an Update")
            ans = messagebox.askokcancel("Version check", "New version available,"
                                         + "\nWould you like to take a look?"
                                         + "\n** click [OK] will direct you to repository)")
            if ans:
                webbrowser.open(url_release)
        else:
            messagebox.showinfo("Version check", "You are using the latest version."
                                + " v" + str(self.app_version))
        exit()

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
                self.use_inkSaver_var_bool.set(config["use_inkSaver_var_bool"])
                App.cls_var = config["target_gpib_address"]
                self.target_gpib_address.set(config["target_gpib_address"])
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
                      "use_inkSaver_var_bool": self.use_inkSaver_var_bool.get(),
                      "target_gpib_address": self.target_gpib_address.get()
                      }
            json.dump(config, f)

    def create_frame_gpib_scanner(self):
        self.newwindow = tk.Toplevel(self.master)
        self.gpibScannerObj = WindowGPIBScanner(self.newwindow)

    def cursor_step_set(self, fine=False):
        if fine:
            self.is_cur_use_fine_step = True
        else:
            self.is_cur_use_fine_step = False

    def get_acq_state(self):
        opc = 0
        focused_obj = None
        try:
            focused_obj = self.frame.focus_get()
            print("focused=", focused_obj)
        except:
            pass
        if not self.pause_get_status_thread:
            try:
                rm = visa.ResourceManager()
                try:
                    if focused_obj is not None:
                        scope = rm.open_resource(self.target_gpib_address.get(), open_timeout=1)
                        opc = scope.query('*OPC?')
                    else:
                        pass
                    if opc:
                        idn_query = scope.query('*IDN?')
                        series = re.sub(r"[\n\t\s]+", "", idn_query)  # remove \n\t\s
                        series = series.split(',')[1]
                        self.scope_series_num = int(re.sub(r"[aA-zZ]", "", series)[0])
                        self.ch_available = int(re.sub(r"[aA-zZ]", "", series)[-1])
                        # print("self.ch_available->", self.ch_available)
                        idn_splited = idn_query.rstrip().split(',')
                        idn_title = idn_splited[0] + ", " + idn_splited[1]
                        Text = "KW Scope Capture" + " v" + str(self.app_version) + "  Found: " + idn_title
                        self.master.title(Text)

                        # Test if Scope support Offset
                        if (self.offset_err_cnt < 2) and (self.offset_err_cnt > -1):
                            try:
                                scope.query('CH1:OFFS?').rstrip()
                                self.offset_err_cnt = self.offset_err_cnt - 1
                            except Exception as e:
                                self.offset_err_cnt = self.offset_err_cnt + 1
                                print("stst cmd dsn support ", e)
                        if self.scope_series_num == 1:
                            self.chkbox_fastacq["state"] = "disabled"
                        else:
                            self.chkbox_fastacq["state"] = "normal"

                        if self.ch_available == 2:
                            self.sel_ch1_var_bool.set(value=int(scope.query('SELect:CH1?').rstrip()))
                            self.sel_ch2_var_bool.set(value=int(scope.query('SELect:CH2?').rstrip()))
                            self.sel_ch3_var_bool.set(value=0)
                            self.sel_ch4_var_bool.set(value=0)
                            self.btn_ch3_up["state"] = "disabled"
                            self.btn_ch3_down["state"] = "disabled"
                            self.btn_ch4_up["state"] = "disabled"
                            self.btn_ch4_down["state"] = "disabled"
                            self.spinbox_pos_ch3['state'] = 'disabled'
                            self.spinbox_offset_ch3['state'] = 'disabled'
                            self.spinbox_pos_ch4['state'] = 'disabled'
                            self.spinbox_offset_ch4['state'] = 'disabled'
                            self.labelFr_ch3['text'] = 'Ch3 Unavailable'
                            self.labelFr_ch4['text'] = 'Ch4 Unavailable'

                            # ch1_pos_offset
                            if self.sel_ch1_var_bool.get():
                                if focused_obj != self.spinbox_offset_ch1:
                                    # self.ch1_offset.set(value=float(scope.query('CH1:OFFS?').rstrip()))
                                    self.ch1_offset.set(value="{:.3f}".format(float(scope.query('CH1:OFFS?').rstrip())))
                                if focused_obj != self.spinbox_pos_ch1:
                                    self.ch1_pos.set(value="{:.2f}".format(float(scope.query('CH1:POS?').rstrip())))

                            # ch2_pos_offset
                            if self.sel_ch2_var_bool.get():
                                if focused_obj != self.spinbox_offset_ch2:
                                    self.ch2_offset.set(value="{:.3f}".format(float(scope.query('CH2:OFFS?').rstrip())))
                                if focused_obj != self.spinbox_pos_ch2:
                                    self.ch1_pos.set(value="{:.2f}".format(float(scope.query('CH2:POS?').rstrip())))

                            self.spinbox_offset_ch1['state'] = 'disabled' if self.offset_err_cnt > 1 else 'normal'
                            self.spinbox_offset_ch2['state'] = 'disabled' if self.offset_err_cnt > 1 else 'normal'
                            self.labelFr_ch1['text'] = 'CH1-ON' if self.sel_ch1_var_bool.get() else 'CH1-OFF'
                            self.labelFr_ch2['text'] = 'CH2-ON' if self.sel_ch2_var_bool.get() else 'CH2-OFF'

                        else:
                            self.sel_ch1_var_bool.set(value=int(scope.query('SELect:CH1?').rstrip()))
                            self.sel_ch2_var_bool.set(value=int(scope.query('SELect:CH2?').rstrip()))
                            self.sel_ch3_var_bool.set(value=int(scope.query('SELect:CH3?').rstrip()))
                            self.sel_ch4_var_bool.set(value=int(scope.query('SELect:CH4?').rstrip()))

                            # ch1_pos_offset
                            # if self.sel_ch1_var_bool.get():
                            #     if focused_obj != self.spinbox_offset_ch1:
                            #         # self.ch1_offset.set(value=float(scope.query('CH1:OFFS?').rstrip()))
                            #         self.ch1_offset.set(value="{:.3f}".format(float(scope.query('CH1:OFFS?').rstrip())))
                            #     if focused_obj != self.spinbox_pos_ch1:
                            #         self.ch1_pos.set(value="{:.2f}".format(float(scope.query('CH1:POS?').rstrip())))
                            #
                            # # ch2_pos_offset
                            # if self.sel_ch2_var_bool.get():
                            #     if focused_obj != self.spinbox_offset_ch2:
                            #         self.ch2_offset.set(value="{:.3f}".format(float(scope.query('CH2:OFFS?').rstrip())))
                            #     if focused_obj != self.spinbox_pos_ch2:
                            #         self.ch2_pos.set(value="{:.2f}".format(float(scope.query('CH2:POS?').rstrip())))

                            # ch3_pos_offset
                            if self.sel_ch3_var_bool.get():
                                if focused_obj != self.spinbox_offset_ch3:
                                    self.ch3_offset.set(value="{:.3f}".format(float(scope.query('CH3:OFFS?').rstrip())))
                                if focused_obj != self.spinbox_pos_ch3:
                                    self.ch3_pos.set(value="{:.2f}".format(float(scope.query('CH3:POS?').rstrip())))

                            # ch4_pos_offset
                            if self.sel_ch4_var_bool.get():
                                if focused_obj != self.spinbox_offset_ch4:
                                    self.ch4_offset.set(value="{:.3f}".format(float(scope.query('CH4:OFFS?').rstrip())))
                                if focused_obj != self.spinbox_pos_ch4:
                                    self.ch4_pos.set(value="{:.2f}".format(float(scope.query('CH4:POS?').rstrip())))

                        self.spinbox_offset_ch1['state'] = 'disabled' if self.offset_err_cnt > 1 else 'normal'
                        self.spinbox_offset_ch2['state'] = 'disabled' if self.offset_err_cnt > 1 else 'normal'
                        self.spinbox_offset_ch3['state'] = 'disabled' if self.offset_err_cnt > 1 else 'normal'
                        self.spinbox_offset_ch4['state'] = 'disabled' if self.offset_err_cnt > 1 else 'normal'
                        self.labelFr_ch1['text'] = 'CH1-ON' if self.sel_ch1_var_bool.get() else 'CH1-OFF'
                        self.labelFr_ch2['text'] = 'CH2-ON' if self.sel_ch2_var_bool.get() else 'CH2-OFF'
                        self.labelFr_ch3['text'] = 'CH3-ON' if self.sel_ch3_var_bool.get() else 'CH3-OFF'
                        self.labelFr_ch4['text'] = 'CH4-ON' if self.sel_ch4_var_bool.get() else 'CH4-OFF'

                        acq_state = int(scope.query('ACQuire:STATE?').rstrip())
                        acq_num = int(scope.query("ACQ:NUMAC?").rstrip())
                        # print("scope acq state=", acq_state)
                        self.acq_state_var_bool.set(acq_state)
                        acqlabeltext = " Acq #" + str(acq_num)
                        self.label_acqnum.config(text=acqlabeltext)
                        self.fastacq_var_bool.set(int(scope.query('FASTAcq:STATE?')))
                        # orig_color = self.chkbox_fastacq.cget("background")
                        if self.fastacq_var_bool.get():
                            self.chkbox_fastacq.configure(fg="Purple2")
                        else:
                            self.chkbox_fastacq.configure(fg="black")
                        # Persistence---checked on DPO4104B
                        if (self.scope_series_num > 1) and (self.scope_series_num < 5):
                            if float(scope.query('DISplay:PERSistence?').rstrip()) == 0:
                                self.persistence_var_bool.set(0)
                            else:
                                self.persistence_var_bool.set(1)
                        else:
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

                        # get the index of closest value
                        time_scale = float(scope.query('HORizontal:MAIn:SCAle?'))
                        horizontal_pos = float(scope.query('HORizontal:POSition?'))
                        # self.closest_timediv_index = min(range(len(self.time_scaleList)),
                        #                                  key=lambda i: abs(self.time_scaleList[i] - time_scale))

                        cmd_ask_scale1 = 'CH' + str(self.cursor1_ch_combobox.get()) + ':SCALe?'
                        cmd_ask_scale2 = 'CH' + str(self.cursor2_ch_combobox.get()) + ':SCALe?'
                        # print(cmd_ask_scale1, cmd_ask_scale2)
                        scale1 = float(scope.query(cmd_ask_scale1).rstrip())
                        scale2 = float(scope.query(cmd_ask_scale2).rstrip())
                        # print(scale1, scale2)

                        if self.is_cur_use_fine_step:
                            self.spinbox_cur1_x_increment = time_scale*0.01
                            self.spinbox_cur2_x_increment = time_scale * 0.01
                            self.spinbox_cur1_y_increment = scale1*0.02
                            self.spinbox_cur2_y_increment = scale2*0.02
                        else:
                            self.spinbox_cur1_x_increment = time_scale * 0.1
                            self.spinbox_cur2_x_increment = time_scale * 0.1
                            self.spinbox_cur1_y_increment = scale1 * 0.2
                            self.spinbox_cur2_y_increment = scale2 * 0.2
                        # print("horizontal_pos=", horizontal_pos)
                        self.spinbox_cur1_x['increment'] = self.spinbox_cur1_x_increment
                        self.spinbox_cur1_x['from_'] = time_scale * -10 * horizontal_pos*0.01
                        self.spinbox_cur1_x['to'] = time_scale * 10 * (100-horizontal_pos)*0.01

                        self.spinbox_cur2_x['increment'] = self.spinbox_cur2_x_increment
                        self.spinbox_cur2_x['from_'] = time_scale * -10 * horizontal_pos*0.01
                        self.spinbox_cur2_x['to'] = time_scale * 10 * (100-horizontal_pos)*0.01

                        self.spinbox_cur1_y['increment'] = self.spinbox_cur1_y_increment
                        offset1 = 0
                        if self.cursor1_ch_combobox.get() == '1':
                            offset1 = float(self.ch1_offset.get())
                        elif self.cursor1_ch_combobox.get() == '2':
                            offset1 = float(self.ch2_offset.get())
                        elif self.cursor1_ch_combobox.get() == '3':
                            offset1 = float(self.ch3_offset.get())
                        elif self.cursor1_ch_combobox.get() == '4':
                            offset1 = float(self.ch4_offset.get())
                        else:
                            pass
                        # print("offset1=", offset1)
                        self.spinbox_cur1_y['from_'] = scale1*-5 + offset1
                        self.spinbox_cur1_y['to'] = scale1*5 + offset1

                        self.spinbox_cur2_y['increment'] = self.spinbox_cur2_y_increment
                        offset2 = 0
                        if self.cursor2_ch_combobox.get() == '1':
                            offset2 = float(self.ch1_offset.get())
                        elif self.cursor2_ch_combobox.get() == '2':
                            offset2 = float(self.ch2_offset.get())
                        elif self.cursor2_ch_combobox.get() == '3':
                            offset2 = float(self.ch3_offset.get())
                        elif self.cursor2_ch_combobox.get() == '4':
                            offset2 = float(self.ch4_offset.get())
                        else:
                            pass
                        # print("offset2=", offset2)
                        self.spinbox_cur2_y['from_'] = scale2 * -5 + offset2
                        self.spinbox_cur2_y['to'] = scale2 * 5 + offset2

                        if self.cursor_type_combobox.current() == 0:
                            self.cursor1_ch_combobox['state'] = 'disable'
                            self.cursor2_ch_combobox['state'] = 'disable'
                            self.spinbox_cur1_x['state'] = 'disable'
                            self.spinbox_cur1_y['state'] = 'disable'
                            self.spinbox_cur2_x['state'] = 'disable'
                            self.spinbox_cur2_y['state'] = 'disable'
                        elif self.cursor_type_combobox.current() == 1:
                            self.cursor1_ch_combobox['state'] = 'normal'
                            self.cursor2_ch_combobox['state'] = 'normal'
                            self.spinbox_cur1_x['state'] = 'disable'
                            self.spinbox_cur1_y['state'] = 'normal'
                            self.spinbox_cur2_x['state'] = 'disable'
                            self.spinbox_cur2_y['state'] = 'normal'
                        elif self.cursor_type_combobox.current() == 2 or self.cursor_type_combobox.current() == 3:
                            self.cursor1_ch_combobox['state'] = 'normal'
                            self.cursor2_ch_combobox['state'] = 'normal'
                            self.spinbox_cur1_x['state'] = 'normal'
                            self.spinbox_cur1_y['state'] = 'disable'
                            self.spinbox_cur2_x['state'] = 'normal'
                            self.spinbox_cur2_y['state'] = 'disable'
                        else:
                            self.cursor1_ch_combobox['state'] = 'normal'
                            self.cursor2_ch_combobox['state'] = 'normal'
                            self.spinbox_cur1_x['state'] = 'normal'
                            self.spinbox_cur1_y['state'] = 'normal'
                            self.spinbox_cur2_x['state'] = 'normal'
                            self.spinbox_cur2_y['state'] = 'normal'

                        if focused_obj != self.cursor_type_combobox:
                            curfuncnow = str(scope.query('CURSor:FUNCtion?').rstrip()).upper()
                            if curfuncnow == 'HBA':
                                self.cursor_type_combobox.current(1)
                            elif curfuncnow == 'VBA':
                                self.cursor_type_combobox.current(2)
                            elif curfuncnow == 'WAVE':
                                self.cursor_type_combobox.current(3)
                            elif curfuncnow == 'SCREEN':
                                self.cursor_type_combobox.current(4)
                            else:
                                self.cursor_type_combobox.current(0)

                        if focused_obj != self.spinbox_cur1_x:
                            self.cur_x1_doublevar.set(value="{:.4f}".format(float(scope.query('CURS:VBA:POSITION1?').rstrip())))
                        if focused_obj != self.spinbox_cur2_x:
                            self.cur_x2_doublevar.set(value="{:.4f}".format(float(scope.query('CURS:VBA:POSITION2?').rstrip())))
                        if focused_obj != self.spinbox_cur1_y:
                            self.cur_y1_doublevar.set(value="{:.4f}".format(float(scope.query('CURS:HBA:POSITION1?').rstrip())))
                        if focused_obj != self.spinbox_cur2_y:
                            self.cur_y2_doublevar.set(value="{:.4f}".format(float(scope.query('CURS:HBA:POSITION2?').rstrip())))
                        scope.close()
                        self.status_var.set("Waiting for user...")
                    else:
                        self.status_var.set("Window not focused or Scope BUSY...")
                        print("self.frame not focused or Scope BUSY...")
                except Exception as e:
                    print("get_acq_state->", e)
                rm.close()
                # self.offset_err_cnt = self.offset_err_cnt + 1
            except Exception:
                self.status_var.set("Connection issue! Retrying...")
                # self.offset_err_cnt = self.offset_err_cnt + 1
                print("Cannot get Acq status-VISA driver Error")
        else:
            pass

    # def get_scope_info(self):
    #     self.update_addr_inApp()
    #     try:
    #         rm = visa.ResourceManager()
    #         try:
    #             with rm.open_resource(self.target_gpib_address.get()) as scope:
    #                 idn_query = scope.query('*IDN?')
    #                 series = re.sub(r"[\n\t\s]+", "", idn_query)  # remove \n\t\s
    #                 series = series.split(',')[1]
    #                 self.scope_series_num = int(re.sub(r"[aA-zZ]", "", series)[0])
    #                 self.ch_available = int(re.sub(r"[aA-zZ]", "", series)[-1])
    #                 idn_splited = idn_query.rstrip().split(',')
    #                 idn_title = idn_splited[0] + ", " + idn_splited[1]
    #                 Text = "KW Scope Capture" + " v" + str(self.app_version) + "  Found: " + idn_title
    #                 self.master.title(Text)
    #                 scope.close()
    #             rm.close()
    #             # self.status_var.set(" tip: Use <Control> key + <Left> or <Right> arrow key to scale time division")
    #         except:
    #             messagebox.showinfo("Oops! Something changed!",
    #                                 "Unable to connect the device used last time.\n\n"
    #                                 "You could check:\n"
    #                                 "1. connection between the target device & your PC.\n"
    #                                 "2. Any change of GPIB address? \n\n"
    #                                 "Then use Tool>GPIB Scanner to Set New target Device.")
    #             # self.create_frame_gpib_scanner()
    #         rm.close()
    #     except:
    #         self.appTitleText = "KW Scope Capture" + str(self.app_version) + "  [VISA driver Error]!"
    #         self.master.title(self.appTitleText)
    #         print("Cannot get scope info-VISA driver Error")

    def save_setup_slot(self, slot_num=1):
        self.pause_get_status_thread = True
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                cmd = "*SAV " + str(slot_num)
                print(cmd)
                scope.write(cmd)
            scope.close()
            rm.close()
        except Exception as e:
            print("save_setup_slot->", e)
        self.pause_get_status_thread = False

    def recall_setup_slot(self, slot_num=1):
        print("recall_setup_slot")
        self.pause_get_status_thread = True
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                cmd = "*RCL " + str(slot_num)
                print(cmd)
                scope.write(cmd)
            scope.close()
            rm.close()
        except Exception as e:
            print("recall_setup_slot->", e)
        self.pause_get_status_thread = False

    def adjust_cur(self):
        cmd_pool_list = ['']
        if self.cursor_type_combobox.current() == 1:
            cmd_cur1_ch = 'CURS:SOU1 CH' + str(self.cursor1_ch_combobox.get())
            cmd_cur1_y = 'CURS:HBA:POSITION1 ' + str(self.spinbox_cur1_y.get())
            cmd_cur2_ch = 'CURS:SOU2 CH' + str(self.cursor2_ch_combobox.get())
            cmd_cur2_y = 'CURS:HBA:POSITION2 ' + str(self.spinbox_cur2_y.get())
            cmd_pool_list.append('CURS:FUNC HBA')
            cmd_pool_list.append(cmd_cur1_ch)
            cmd_pool_list.append(cmd_cur1_y)
            cmd_pool_list.append(cmd_cur2_ch)
            cmd_pool_list.append(cmd_cur2_y)
            cmd_pool_list.append('CURSor:STATE ON')
        elif self.cursor_type_combobox.current() == 2:
            cmd_cur1_ch = 'CURS:SOU1 CH' + str(self.cursor1_ch_combobox.get())
            cmd_cur1_x = 'CURS:VBA:POS1 ' + str(self.spinbox_cur1_x.get())
            cmd_cur2_ch = 'CURS:SOU2 CH' + str(self.cursor2_ch_combobox.get())
            cmd_cur2_x = 'CURS:VBA:POS2 ' + str(self.spinbox_cur2_x.get())
            cmd_pool_list.append('CURS:FUNC VBA')
            cmd_pool_list.append(cmd_cur1_ch)
            cmd_pool_list.append(cmd_cur1_x)
            cmd_pool_list.append(cmd_cur2_ch)
            cmd_pool_list.append(cmd_cur2_x)
            cmd_pool_list.append('CURSor:STATE ON')
        elif self.cursor_type_combobox.current() == 3:
            cmd_cur1_ch = 'CURS:SOU1 CH' + str(self.cursor1_ch_combobox.get())
            cmd_cur1_x = 'CURS:VBA:POS1 ' + str(self.spinbox_cur1_x.get())
            cmd_cur2_ch = 'CURS:SOU2 CH' + str(self.cursor2_ch_combobox.get())
            cmd_cur2_x = 'CURS:VBA:POS2 ' + str(self.spinbox_cur2_x.get())
            cmd_pool_list.append('CURS:FUNC WAVE')
            cmd_pool_list.append(cmd_cur1_ch)
            cmd_pool_list.append(cmd_cur1_x)
            cmd_pool_list.append(cmd_cur2_ch)
            cmd_pool_list.append(cmd_cur2_x)
            cmd_pool_list.append('CURSor:STATE ON')
        elif self.cursor_type_combobox.current() == 4:
            cmd_cur1_ch = 'CURS:SOU1 CH' + str(self.cursor1_ch_combobox.get())
            cmd_cur2_ch = 'CURS:SOU2 CH' + str(self.cursor2_ch_combobox.get())
            cmd_cur1_y = 'CURSor:SCREEN:YPOSITION1 ' + str(self.spinbox_cur1_y.get())
            cmd_cur2_y = 'CURSor:SCREEN:YPOSITION2 ' + str(self.spinbox_cur2_y.get())
            cmd_cur1_x = 'CURSor:SCREEN:XPOSITION1 ' + str(self.spinbox_cur1_x.get())
            cmd_cur2_x = 'CURSor:SCREEN:XPOSITION2 ' + str(self.spinbox_cur2_x.get())
            cmd_pool_list.append('CURS:FUNC SCREEN')
            cmd_pool_list.append(cmd_cur1_ch)
            cmd_pool_list.append(cmd_cur1_x)
            cmd_pool_list.append(cmd_cur1_y)
            cmd_pool_list.append(cmd_cur2_ch)
            cmd_pool_list.append(cmd_cur2_x)
            cmd_pool_list.append(cmd_cur2_y)
            cmd_pool_list.append('CURSor:STATE ON')
        else:
            cmd_pool_list.append('CURS:FUNC OFF')
            cmd_pool_list.append('CURSor:STATE OFF')

        self.pause_get_status_thread = True
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                for cmd in cmd_pool_list:
                    scope.write(cmd)
                    print("VISAWrite->", cmd)
            scope.close()
            rm.close()
        except Exception as e:
            print(e)
        self.pause_get_status_thread = False

    def adjust_pos(self, ch=1):
        self.pause_get_status_thread = True
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                if ch == 1:
                    value = self.spinbox_pos_ch1.get()
                elif ch == 2:
                    value = self.spinbox_pos_ch2.get()
                elif ch == 3:
                    value = self.spinbox_pos_ch3.get()
                elif ch == 4:
                    value = self.spinbox_pos_ch4.get()
                else:
                    pass
                ch1_pos_cmd = "CH" + str(ch) + ":POS " + str(value)
                # ch1_pos_cmd = "CH1:POS " + str(self.spinbox_pos_ch1.get())
                scope.write(ch1_pos_cmd)
            scope.close()
            rm.close()
        except Exception as e:
            print(e)
        self.pause_get_status_thread = False

    def adjust_offset(self, ch=1):
        self.pause_get_status_thread = True
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                if ch == 1:
                    value = self.spinbox_offset_ch1.get()
                elif ch == 2:
                    value = self.spinbox_offset_ch2.get()
                elif ch == 3:
                    value = self.spinbox_offset_ch3.get()
                elif ch == 4:
                    value = self.spinbox_offset_ch4.get()
                else:
                    pass
                ch1_offset_cmd = "CH" + str(ch) + ":OFFS " + str(value)
                # ch1_offset_cmd = "CH1:OFFS " + str(self.spinbox_offset_ch1.get())
                scope.write(ch1_offset_cmd)
            scope.close()
            rm.close()
        except Exception as e:
            print(e)
        self.pause_get_status_thread = False

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
        # self.get_scope_info()
        # self.status_var.set("Try Talking to Scope")
        self.pause_get_status_thread = True
        self.get_default_filename()
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                scope.timeout = self.visa_timeout_duration
                if self.scope_series_num < 5:
                    # test DPO2024B, DPO4104 OK
                    print("<5 series Scrshot")
                    scope.write("HARDCOPY:FORMat PNG")
                    if self.use_inkSaver_var_bool.get():
                        scope.write("HARDCOPY:INKSAVER ON")
                        scope.write("SAV:IMAG:INKS ON")  # tested, worked on DPO4104B
                        print("Enable Ink Saver")
                    else:
                        # scope.write("SAVe:IMAGe:INKSaver OFF")
                        scope.write("HARDCOPY:INKSAVER OFF")
                        scope.write("SAV:IMAG:INKS OFF")  # tested, worked on DPO4104B
                        print("Disable Ink Saver")
                    scope.write("HARDCOPY START")
                    # scope.write('*OPC?')
                    img_data = scope.read_raw()
                    # print(img_data)
                else:
                    print(">=5 series Scrshot")
                    scope.write("HARDCopy:PORT FILE")
                    # Notice: CANNOT access C Drive root directly if scope use win10
                    scope.write('FILESystem:MKDir \'C:\TempScrShot(could be Deleted)\'')
                    scope.write('HARDCopy:FILEName  \'C:\TempScrShot(could be Deleted)\KWScrShot.png\'')
                    if self.use_inkSaver_var_bool.get():
                        scope.write("EXPort:PALEtte INKS")
                        print("PALEtte->INKSaver")
                    else:
                        scope.write("EXPort:PALEtte COLO")
                        print("PALEtte->COLOr")
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
                    cv2.rectangle(I_cv2, (width - width + 640, height - height), (width, height - height + 31),
                                  (0, 0, 0), -1)
                    img_text = cv2.putText(I_cv2, text, (width - width + 640, height - height + 20), font,
                                           font_size, font_color, font_thickness,
                                           cv2.LINE_AA)
                    outputImage = img_text
                else:
                    outputImage = I_cv2

                # # Image show (OpenCV)
                if self.imshow_var_bool.get():
                    cv2.imshow("Press Any Key to Dismiss", outputImage)
                    cv2.waitKey()
                    cv2.destroyAllWindows()
                    # img = Image.fromarray(outputImage, 'RGB')
                    # img.show()

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
                                self.status_var.set("Saved: " + self.savefilename + '.png')
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
                except Exception as e:
                    self.status_var.set(e)
                scope.close()
                rm.close()
        except Exception as e:
            print("Cannot get scope shot-VISA Error")
            self.status_var.set(e)
        self.get_default_filename()
        self.pause_get_status_thread = False

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
        answer = messagebox.askokcancel("Are you sure?",
                                        "Execute AutoSet?")
        if answer:
            try:
                rm = visa.ResourceManager()
                with rm.open_resource(self.target_gpib_address.get()) as scope:
                    scope.write('AUTOSet EXECute')
                    scope.close()
                rm.close()
            except ValueError:
                print("Autoset Failed")
                self.status_var.set("AutoSet Failed, VISA ERROR")
        else:
            print("AutoSet Aborted.")

    def scope_execute_spc(self):
        answer = messagebox.askokcancel("Are you sure?",
                                        "[SPC] Signal Path Compensation\n\n"
                                        + "This operation takes about 5~10 minutes,\n"
                                        + "Scope will stop responding during execution.")
        if answer:
            try:
                rm = visa.ResourceManager()
                with rm.open_resource(self.target_gpib_address.get()) as scope:
                    scope.query('*CAL?')
                    scope.close()
                rm.close()
            except ValueError:
                print("SPC Failed")
                self.status_var.set("Factory Reset, VISA ERROR")
        else:
            print("SPC Aborted.")

    def scope_factory_reset(self):
        answer = messagebox.askokcancel("Are you sure?",
                                        "Recall factory default settings?")
        if answer:
            try:
                rm = visa.ResourceManager()
                with rm.open_resource(self.target_gpib_address.get()) as scope:
                    scope.write('*RST')
                    scope.close()
                rm.close()
            except ValueError:
                print("Factory Reset Failed")
                self.status_var.set("Factory Reset, VISA ERROR")
        else:
            print("Factory Default Aborted.")

    def scope_set_trigger_a(self):
        # self.update_addr_inApp()
        print("Into --scope_channel_select--")
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get(), open_timeout=1) as scope:
                # scope.write('TRIGger:B SETLevel')
                if self.trig_ch_combobox.get() == '1':
                    scope.write('TRIGGER:A:EDGE:SOURCE CH1')
                elif self.trig_ch_combobox.get() == '2':
                    scope.write('TRIGGER:A:EDGE:SOURCE CH2')
                elif self.trig_ch_combobox.get() == '3':
                    scope.write('TRIGGER:A:EDGE:SOURCE CH3')
                elif self.trig_ch_combobox.get() == '4':
                    scope.write('TRIGGER:A:EDGE:SOURCE CH4')
                else:
                    pass
                if self.trig_edge_combobox.get() == 'Rise':
                    scope.write('TRIGGER:A:EDGE:SLOPE RISE')
                elif self.trig_edge_combobox.get() == 'Fall':
                    scope.write('TRIGGER:A:EDGE:SLOPE FALL')
                elif self.trig_edge_combobox.get() == 'Either':
                    scope.write('TRIGGER:A:EDGE:SLOPE EITher')
                else:
                    pass
                scope.write('TRIGger:A SETLevel')
                scope.close()
            rm.close()
        except ValueError:
            print("Set Trig A failed")
            self.status_var.set("Set Trig A failed, VISA ERROR")

    def horizontal_zoom_out(self, *args):
        self.pause_get_status_thread = True
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                time_scale = float(scope.query('HORizontal:MAIn:SCAle?'))
                print("Scale = ", time_scale)
                # get the index of closest value
                self.closest_timediv_index = min(range(len(self.time_scaleList)),
                                         key=lambda i: abs(self.time_scaleList[i] - time_scale))
                self.target_index = self.closest_timediv_index
                if self.closest_timediv_index < (len(self.time_scaleList)) - 1:
                    self.target_index = self.closest_timediv_index + 1
                    scope.write('HORizontal:MAIn:SCAle ' + str(self.time_scaleList[self.target_index]))
                    scope.write('HORizontal:RESOlution 1e5')  # set resolution to 100k
                    scope.write('HORizontal:POSition 50')
                else:
                    pass
                scope.write('HORizontal:MODE AUTO')
            rm.close()
        except ValueError:
            self.status_var.set("VISA driver Error")
            self.btn_RunStop.configure(fg="red")
        self.pause_get_status_thread = False

    def horizontal_zoom_in(self, *args):
        self.pause_get_status_thread = True
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                time_scale = float(scope.query('HORizontal:MAIn:SCAle?'))
                # get the index of closest value
                self.closest_timediv_index = min(range(len(self.time_scaleList)),
                                         key=lambda i: abs(self.time_scaleList[i] - time_scale))
                self.target_index = self.closest_timediv_index
                if self.closest_timediv_index > 1:
                    self.target_index = self.closest_timediv_index - 1
                    scope.write('HORizontal:MAIn:SCAle ' + str(self.time_scaleList[self.target_index]))
                    scope.write('HORizontal:RESOlution 1e5')  # set resolution to 100k
                    scope.write('HORizontal:POSition 50')
                else:
                    pass
                scope.write('HORizontal:MODE AUTO')
            rm.close()
        except ValueError:
            self.status_var.set("VISA driver Error")
            self.btn_RunStop.configure(fg="red")
        self.pause_get_status_thread = False

    def ch_scale_adj(self, ch=1, updn='up'):
        cmd_scale = ''
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                cmd = 'CH'+str(ch)+':SCALe?'
                scale_current = float(scope.query(cmd))
                # get the index of closest value
                self.closest_timediv_index = min(range(len(self.vertical_scaleList)),
                                                 key=lambda i: abs(self.vertical_scaleList[i] - scale_current))
                if updn == 'up':
                    if self.closest_timediv_index < (len(self.vertical_scaleList)) - 1:
                        target_index = self.closest_timediv_index + 1
                        cmd_scale = 'CH'+str(ch)+':SCALe ' + str(self.vertical_scaleList[target_index])
                        print('scale cmd=', cmd_scale)
                elif updn == 'dn':
                    if self.closest_timediv_index > 0:
                        target_index = self.closest_timediv_index - 1
                        cmd_scale = 'CH' + str(ch) + ':SCALe ' + str(self.vertical_scaleList[target_index])
                        print('scale cmd=', cmd_scale)
                else:
                    pass
                scope.write(cmd_scale)
                scope.close()
            rm.close()
        except ValueError:
            print("Scale CH1 Failed")
            self.status_var.set("Scale CH1 Failed, VISA ERROR")

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
                if (self.sel_ch3_var_bool.get()) and (self.ch_available > 2):
                    scope.write('SELect:CH3 ON')
                else:
                    scope.write('SELect:CH3 OFF')
                if (self.sel_ch4_var_bool.get()) and (self.ch_available > 2):
                    scope.write('SELect:CH4 ON')
                else:
                    scope.write('SELect:CH4 OFF')
                scope.close()
            rm.close()
        except ValueError:
            print("Sel CH Failed")
            self.status_var.set("Sel CH Failed, VISA ERROR")

    def trigger_fstacq(self):
        self.pause_get_status_thread = True
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
        self.pause_get_status_thread = False

    def set_persistence(self):
        self.pause_get_status_thread = True
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                if self.persistence_var_bool.get():
                    # TBS1000 series
                    if self.scope_series_num == 1:
                        scope.write('DISplay:PERSistence INF')
                    # 234 series
                    elif (self.scope_series_num > 1) and (self.scope_series_num < 5):
                        scope.write('DISplay:PERSistence INFInite')
                    # 5000,7000 series
                    else:
                        scope.write('DISplay:PERSistence INFPersist')
                else:
                    # TBS1000 series
                    if self.scope_series_num == 1:
                        scope.write('DISplay:PERSistence OFF')
                    # 234 series
                    elif (self.scope_series_num > 1) and (self.scope_series_num < 5):
                        scope.write('DISplay:PERSistence MINImum')
                        scope.write('DISplay:PERSistence CLEAR')
                    # 5000,7000 series
                    else:
                        scope.write('DISplay:PERSistence OFF')
                scope.close()
            rm.close()
        except:
            print("cannot set Persistence")
            self.status_var.set("VISA driver Error")
        self.pause_get_status_thread = False

    def btn_single_clicked(self):
        self.pause_get_status_thread = True
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
        self.pause_get_status_thread = False

    def btn_clear_clicked(self, *args):
        self.pause_get_status_thread = True
        try:
            rm = visa.ResourceManager()
            with rm.open_resource(self.target_gpib_address.get()) as scope:
                ScopeModelLastChar = scope.query('*IDN?').rstrip().split(',')[1][-1]
                print("ScopeModelLastChar:", ScopeModelLastChar)
                isCModel = False
                try:
                    if ScopeModelLastChar == 'C':
                        isCModel = True
                        print('isCModel=', isCModel)
                    else:
                        isCModel = False
                        print('isCModel=', isCModel)
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
                    print("Send [SINGLE, RUN, RUN] Cmd to CLEAR ALL")
                    self.status_var.set("Cleared")
                scope.close()
            rm.close()
        except:
            print("cannot clear scope-VISA driver Error")
            self.status_var.set("VISA driver Error")
        self.pause_get_status_thread = False

    def btn_runstop_clicked(self, *args):
        self.pause_get_status_thread = True
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
        self.pause_get_status_thread = False

    def btn_capture_clicked(self, *args):
        self.pause_get_status_thread = True
        folder = self.path_var.get()
        print("Capture Btn clicked, save folder", folder)
        self.get_shot_scope()
        self.pause_get_status_thread = False


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

# Splash
# def splash():
#     splash = tk.Tk()
#     splash.overrideredirect(True)
#     splash.title("Splash!")
#     width = splash.winfo_screenwidth()
#     height = splash.winfo_screenheight()
#     # splash.geometry('%dx%d+%d+%d' % (width*0.2, height*0.2, width*0.1, height*0.1))
#     # splash.geometry("800x750+128+128")
#     splash_img = myIcon.splash_base64_128px
#     splash_img = base64.b64decode(splash_img)
#     splash_img = ImageTk.PhotoImage(data=splash_img)
#     # highlightthickness=0 -> remove frame
#     canvas = tk.Canvas(splash, height=256, width=256, bg='black', highlightthickness=0)
#     canvas.create_image(128, 128, image=splash_img)
#     canvas.pack(fill='both')
#     splash.after(2700, splash.destroy)
#     splash.wm_attributes('-transparentcolor', 'black')
#     center(splash)
#     splash.mainloop()


def mainApp():
    root = tk.Tk()
    app = App(root)
    img = myIcon.icon_base64_32px
    img = base64.b64decode(img)
    img = ImageTk.PhotoImage(data=img)
    root.wm_iconphoto(True, img)
    # root.iconbitmap(r'img/ico32.ico')

    # NEED a better way to fix the delete of filename and cannot Paste by Ctrl+V bug.
    # root.bind("<Control_L>", lambda i: app.frame.focus_set())
    root.bind("<Control_R>", lambda i: app.frame.focus_set())
    # root.bind("<Return>", app.btn_capture_clicked)
    # root.bind("<Return>", lambda i: app.frame.focus_set())
    root.bind("<Control-Return>", app.btn_runstop_clicked)
    root.bind("<Control-Delete>", app.btn_clear_clicked)
    root.bind("<Control-Left>", app.horizontal_zoom_out)
    root.bind("<Control-Right>", app.horizontal_zoom_in)
    center(root)
    root.protocol("WM_DELETE_WINDOW", app.ask_quit)
    root.mainloop()


if __name__ == '__main__':
    mainApp()
