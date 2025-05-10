import os
import can
import matplotlib.pyplot as plt
import time
import matplotlib.animation as animation

os.system('sudo ip link set can0 down')
os.system('sudo ip link set can0 type can bitrate 500000 listen-only on')
os.system('sudo ifconfig can0 up') # Enable can0 

#bus = can.interface.Bus(channel = 'can0', bustype = 'socketcan_ctypes')# socketcan_native
bus = can.interface.Bus(channel='can0', bustype='socketcan')
state = "initial";
data = [0] * 5;

def to_signed(val, bits):
    if val & (1 << (bits - 1)):
        return val - (1 << bits)
    else:
        return val


while 1:
    message = bus.recv(10.0)
    if message is not None: 
        if message.arbitration_id == 0x23F01 or message.arbitration_id == 0x40803F :       
             if message.arbitration_id == 0x23F01:
                 data[0]=message.data[0];  #0
                 data[1]=to_signed(message.data[2],8);  #2
                
                #print(f"ID: {hex(message.arbitration_id)}, Data: {[hex(b) for b in message.data]}", end=" ")
            
             elif message.arbitration_id == 0x40803F:
                 data[2]=0 #message.data[0]
                 data[3]=to_signed(message.data[1] | message.data[2]<<8 | message.data[3]<<16,24)
                 data[4]=message.data[4]
             
                 #print(data);
                 #print(f"{val:+5d}")
                 for val in data:
                     #signed_val = to_signed(val)
                     print(f"{val:+5d}", end="", flush=True)
                 print()    
                    
        

    if message is None:
        print('Timeout occurred, no message received.')
        os.system('sudo ifconfig can0 down')  #Disable can0
