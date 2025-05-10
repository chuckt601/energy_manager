import os
import can

os.system('sudo ip link set can0 type can bitrate 500000 listen-only on')
os.system('sudo ifconfig can0 up') # Enable can0 

#bus = can.interface.Bus(channel = 'can0', bustype = 'socketcan_ctypes')# socketcan_native
bus = can.interface.Bus(channel='can0', bustype='socketcan')
state = "initial"
data = [0] * 24
number=0
known_ids = [0x4803F, 0x80803F, 0x803F01, 0x40803F, 0x20803F, 0x23F01]

while 1:
    message = bus.recv(10.0)
    if message is not None:        
        if message.arbitration_id == known_ids[3]:  
            #print (message)
            #print(f"ID: {hex(message.arbitration_id)}, Data: {[hex(b) for b in message.data]}")
            for i in range(len(message.data)):
               data[i]=message.data[i]
            #state="C6"
            number=0
            B03 = int.from_bytes(data[0:4], byteorder='little', signed=True)
            B47 = int.from_bytes(data[4:8], byteorder='little', signed=True)
            print(f"B03 = {B03:8d}, B47 = {B47:8d}", end=" ")
            print(f"ID: {hex(message.arbitration_id)}, Data: {[(b) for b in message.data]}")

            
        elif state == "C6":
            #print(f"{[hex(b) for b in message.data]}", end=" ")
            state="C6 second set"
            for i in range(len(message.data)):
               data[i+8]=message.data[i]
            
        elif state == "C6 second set":
            #print(f"{[hex(b) for b in message.data]}")
            state="initial"
            for i in range(len(message.data)):
               data[i+16]=message.data[i]
            for i in range(24):
                number+=data[i]*2**i 
            print(number)    

            

    #if message is None:
    #    print('Timeout occurred, no message received.')

    #os.system('sudo ifconfig can0 down')  #Disable can0