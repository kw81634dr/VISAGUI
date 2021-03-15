import pyvisa as visa # https://pyvisa.readthedocs.org/en/stable/
import time

target_gpib_address='GPIB::6::INSTR'

try:
    rm = visa.ResourceManager()
    GPIB_list = rm.list_resources()
    print(GPIB_list)

    with rm.open_resource('GPIB0::6::INSTR') as scope:
        scope.timeout = 2000  # ms
        print("Device Found: ", scope.query('*IDN?'))
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
        print("clear waveform ", scope.write('FASTAcq:STATE ON'))
        # print("clear waveform ", scope.write('ACQuire:REPEt ON'))
        # WORKS BUT AS Fallback

        # equivalent to clear button
        scope.write('CLEAR ALL')
        acc_num = 0

        while acc_num < 30:
            acc_num = int(scope.query('ACQuire:NUMACq?'))
            print("Acc #=", acc_num)
            time.sleep(1)

        scope.write('ACQuire:STATE STOP')

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