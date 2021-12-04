# VISA GUI
**Manipulate your Oscilloscope with keyboard & mouse (or even foot padel !)**

App preview

![mac_GUI screen shot](img/scrshot/macGUIv2.3.png)
![win_GUI screen shot](img/scrshot/v2.4scrshot.png)

### >>Download the latest release -> [here](https://github.com/kw81634dr/VISAGUI/releases)

## Features

#### Screen Shot
* (shortcut: `Enter`)
* Capture ScreenShot without USB flash drive.
* Add text overlay
* Toggle Ink Saver

#### Channels
* Turn ON/OFF.
* Vertical scale Adjustment.
* Horizontal scale Adjustment. (shortcut: `Ctrl` + `←`/`→`)
* Position & Offset** Adjustment.

#### Acquisition
* Set `Run`/`Stop` Acq (shortcut: `Ctrl` + `Enter`)
* Set `Single` Acq (shortcut: `Ctrl` + `Enter`)
* `Clear` (shortcut: `Ctrl` + `Del`)
* Toggle FastAcq**
* Toggle Infinite Persistence.
* Signal Trigger adjusment. 

#### Scope
* execute AutoSet
* execute Signal Path Compensation (SPC)*
* Recall factory default setting

#### Handy Tool
* GPIB bus Scanner

![pic of GPIB Scanner](img/scrshot/GPIBScan.png)


**availability of such features depends on your scope model.

> Dependencies
>> VISA driver : [NI-488.2(NI-VISA)](https://www.ni.com/en-us/support/downloads/drivers/download.ni-488-2.html#306147), Python libraries : [pyvisa](https://pypi.org/project/PyVISA/),
[PIL](https://pypi.org/project/Pillow/),
[requests](https://pypi.org/project/requests/)

>> Tkinter library not found solution for MacOS: `$ brew install python-tk`


[Brew Homepage](https://brew.sh/)

## Compatible model:

|Verified| TeK           | remarks  |
|--------|---------------|---|
|Pending | TBS1052B-EDU  |   |
|&check; | DPO2014B      |   |
|&check; | MSO2024B      |   |
|&check; | DPO4104       |   |
|&check; | MDO4024C      |   |
|&check; | DPO7104       |   |
|&check; | DPO7104C      |   |

Captured ScreenShot from DPO2014B (with & without Ink Saver Enabled)

![pic of Ink Saver](img/scrshot/DPO2014B_InkSaver.png)
![Scope screen shot](img/scrshot/DPO2014B.png)

Captured ScreenShot from DPO4104

![Scope screen shot](img/scrshot/DPO4104.png)

Captured ScreenShot from DPO7104C

![Scope screen shot](img/scrshot/test.png)

## One more thing :bulb:
Foot Padel control implementation (Arduino Code available in sub directory)

![Foot Padel](img/scrshot/footPadel_gif.gif)
![Scope RUN/STOP](img/scrshot/Scoperunstop_gif.gif)


## Todo
- [ ] Support other brand's scope.
- [ ] Customize Keyboard Shortcut.
- [ ] Transform to MVC model and clean up messy code.

https://icoconvert.com/