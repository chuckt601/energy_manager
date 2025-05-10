import os
import can

os.system('sudo ip link set can0 type can bitrate 500000 listen-only on')
os.system('sudo ifconfig can0 up') # Enable can0 

#bus = can.interface.Bus(channel = 'can0', bustype = 'socketcan_ctypes')# socketcan_native
bus = can.interface.Bus(channel='can0', bustype='socketcan')
state = "initial"
data = [0] * 6*8
number=0



while 1:
    message = bus.recv(10.0)
    if message is not None:        
        if state == "initial" and message.arbitration_id == 0x803F01 and message.data[0] == 0x00:  
            #print (message)
            #print(f"ID: {hex(message.arbitration_id)}, Data: {[f'0x{b:02X}' for b in message.data]}")
            for i in range(len(message.data)):
               data[i]=message.data[i]
            #state="second line"
            number=0
            #B03 = int.from_bytes(data[0:4], byteorder='little', signed=True)
            #B47 = int.from_bytes(data[4:8], byteorder='little', signed=True)
            print(f"B03 = {B03:7d}, B47 = {B47:7d}", end=" ")
            print(f"ID: {(message.arbitration_id)}, Data: {[(b) for b in message.data]}")

            
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