import pyvisa as visa # https://pyvisa.readthedocs.org/en/stable/

target_gpib_address='GPIB::6::INSTR'

try:
    rm = visa.ResourceManager()
    GPIB_list = rm.list_resources()
    print(GPIB_list)
    for deviceaddr in GPIB_list:
        with rm.open_resource(deviceaddr) as scope:
            print("Device Found: ", scope.query('*IDN?'))
            scope.close()
    rm.close()
except ValueError:
    print("VISA driver Error, Scope NOT Found")

