import pyvisa as visa # https://pyvisa.readthedocs.org/en/stable/
import time

target_gpib_address='GPIB::6::INSTR'

try:
    rm = visa.ResourceManager()
    GPIB_list = rm.list_resources()
    print("GPIB list:", GPIB_list)
    # GPIB list: ('GPIB0::6::INSTR',)

    with rm.open_resource('GPIB0::6::INSTR') as scope:
        scope.timeout = 2000  # ms
        idn = scope.query('*IDN?')
        print("Device Found: ", idn)
        # Device Found: TEKTRONIX,DPO7104C,C302654,CF:91.1CT FV:10.8.3 Build 3
        x = idn.split(",")
        print(x[1])
        if x[1][-1] == 'C':
            print("it's C model")
        else:
            print("Isn't C model")
        # scope.query('*OPC?')
        # scope.write('ACQUIRE:STATE STOP')
        # print("Acc state: ", scope.query('ACQuire:STATE?'))
        # print("Acc state: ", scope.query('ACQuire:STATE ON'))
        # print("Acc state: ", scope.query('ACQuire:STATE OFF'))
        # scope.query('acquire:stopafter SEQUENCE')
        # print("Acc #: ", scope.query('ACQuire:NUMACq?'))
        # print("clear stat: ", scope.query('MEASUrement:STATIstics:COUNt {RESET}'))

        # WORKS BUT AS Fallback
        # print("clear waveform ", scope.write('ACQuire:REPEt OFF'))
        # print("clear waveform ", scope.write('FASTAcq:STATE ON'))
        # print("clear waveform ", scope.write('ACQuire:REPEt ON'))
        # WORKS BUT AS Fallback

        #alter CLEAR ALL for non C model
        # scope.write('ACQuire:STOPAFTER SEQUENCE')
        # scope.write('ACQ:STATE ON')
        # scope.write('ACQ:STOPA RUNST')
        # print("acq#=", scope.query("ACQ:NUMAC?"))

        # equivalent to clear button
        # scope.write('CLEAR ALL')
        # acc_num = 0

        # while acc_num < 30:
        #     acc_num = int(scope.query('ACQuire:NUMACq?'))
        #     print("Acc #=", acc_num)
        #     time.sleep(1)
        #
        # scope.write('ACQuire:STATE STOP')

        scope.close()

    rm.close()
except ValueError:
    print("VISA driver Error, Scope NOT Found")

   # def start_n_stop_scope_accquisition(self):
    #     # try:
    #     #     rm = visa.ResourceManager()
    #     #     with rm.open_resource(self.target_gpib_address.get()) as scope:
    #     # #'ACQuire: STOPAfter:COUNt500'

# print(scope.query('*IDN?'))
# print(scope.write("TRIGger:MODe NORMal")) # set trigger normal
# #print(scope.write("ACQuire:STOPAfter RUNSTop")) # continuous
# print(scope.write("ACQuire:STOPAfter SEQ")) # single shot
# print(scope.query("ACQ?"))
# print(scope.write("ACQuire:STATE RUN")) # acquire single trigger
# """
# print(scope.query("ACQ?"))
# #print(scope.query("MEASU?"))
# print(scope.query("MEASUrement:MEAS1:MEAN?"))
# print(scope.query("CH1:OFFSet?"))
# print(scope.write("CH1:OFFSet 0.02"))
# print(scope.query("CH1:OFFSet?"))
# # try to grab a capture
# print(scope.write("data:source ch1"))
# print(scope.write("curve?"))
# data = scope.read_values()
# print(len(data))
# x = range(len(data))
# import matplotlib.pyplot as plt
# fig = plt.figure()
# ax = fig.add_subplot(1,1,1)
# ax.plot(x, data)
# plt.show()