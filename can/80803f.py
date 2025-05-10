import os
import can

os.system('sudo ip link set can0 type can bitrate 500000 listen-only on')
os.system('sudo ifconfig can0 up') # Enable can0 

#bus = can.interface.Bus(channel = 'can0', bustype = 'socketcan_ctypes')# socketcan_native
bus = can.interface.Bus(channel='can0', bustype='socketcan')
state = "initial"
data = [0] * 32
number=0

while 1:
    message = bus.recv(10.0)
    if message is not None and message.arbitration_id == 0x80803F:        
        if state == "initial" and message.data[0] == 0xD0:  
            #print (message)
            #print(f"ID: {hex(message.arbitration_id)}, Data: {[hex(b) for b in message.data]}")
            for i in range(len(message.data)):
               data[i]=message.data[i]
            state="read 2nd line"
            number=0            
            
        elif state == "read 2nd line":
            #print(f"{[hex(b) for b in message.data]}", end=" ")
            state="read 3rd line"
            for i in range(len(message.data)):
               data[i+8]=message.data[i]
            
        elif state == "read 3rd line":
            #print(f"{[hex(b) for b in message.data]}")
            state="read 4th line"
            for i in range(len(message.data)):
               data[i+16]=message.data[i]

        elif state == "read 4th line":
            #print(f"{[hex(b) for b in message.data]}")
            state="initial"
            for i in range(len(message.data)):
               data[i+24]=message.data[i]

            #print(f"ID: {hex(message.arbitration_id)}, Data: {[(b) for b in data]}")
            print(f"{[f'{b:3d}' for b in data]}")

            #for i in range(24):
            #    number+=data[i]*2**i 
            #print(number)    

            

    #if message is None:
    #    print('Timeout occurred, no message received.')

    #os.system('sudo ifconfig can0 down')  #Disable can0