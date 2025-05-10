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
        if message.arbitration_id == known_ids[5]:  
            #print (message)
            #print(f"ID: {hex(message.arbitration_id)}, Data: {[hex(b) for b in message.data]}")
            number=0
            for i in range(len(message.data)):
               data[i]=message.data[i]
               number+=data[i]*2**i
            B01= int.from_bytes(data[0:2], byteorder='little', signed=True)
            B23= int.from_bytes(data[2:4], byteorder='little', signed=True)
            print(f"discharge={B01/2000:5.2f}, {B23/2000:5.2f}", end='')
            print(f" {hex(message.arbitration_id)},{[(b) for b in message.data]}")
         
            #state="C6"
            
            
            
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