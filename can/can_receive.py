import os
import can

os.system('sudo ip link set can0 type can bitrate 500000 listen-only on')
os.system('sudo ifconfig can0 up') # Enable can0 

#bus = can.interface.Bus(channel = 'can0', bustype = 'socketcan_ctypes')# socketcan_native
bus = can.interface.Bus(channel='can0', bustype='socketcan')
state = "initial"

while 1:
    message = bus.recv(10.0)
    if message is not None:        
        if state == "initial" and message.arbitration_id == 0x803F01 and message.data[0] == 0xC6:  
            #print (message)
            print(f"ID: {hex(message.arbitration_id)}, Data: {[hex(b) for b in message.data]}", end=" ")
            state="C6"
        if state == "C6":
            print(f"{[hex(b) for b in message.data]}", end=" ")
            state="C6 second set"
        if state == "C6 second set":
            print(f"{[hex(b) for b in message.data]}")
            state="initial" 

    #if message is None:
    #    print('Timeout occurred, no message received.')

    #os.system('sudo ifconfig can0 down')  #Disable can0