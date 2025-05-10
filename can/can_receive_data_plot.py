import os
import can
import matplotlib.pyplot as plt
import time
import matplotlib.animation as animation

os.system('sudo ip link set can0 down')
os.system('sudo ip link set can0 type can bitrate 500000 listen-only on')
os.system('sudo ifconfig can0 up') # Enable can0 

bus = can.interface.Bus(channel='can0', bustype='socketcan')
state = "initial";
data = [0] * 5;

# Setup plot
plt.ion()  # Interactive mode on
fig, ax = plt.subplots()
line, = ax.plot([], [], lw=2)
ax.set_title("Sensor Data (Live)")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Sensor Value")
#ax.set_ylim(-256, 256)  # <-- fixed vertical scale

xdata, ydata = [], []
start_time = time.time()


def to_signed(val, bits):
    if val & (1 << (bits - 1)):
        return val - (1 << bits)
    else:
        return val

try:
   while 1:
    message = bus.recv(10.0)
    if message is not None: 
        if message.arbitration_id == 0x803F01 or message.arbitration_id == 0x23F01 :       
             if message.arbitration_id == 0x803F01 and message.data[0] == 0xC6: 
                 data[0]=to_signed(message.data[4] | message.data[5]<<8,16)# | message.data[3]<<16,24)
                 data[1]=to_signed(message.data[6] | message.data[7]<<8,16)# | message.data[3]<<16,24)
                 #data[0]=message.data[0];  #0
                 #data[1]=to_signed(message.data[2],8);  #2
                
                #print(f"ID: {hex(message.arbitration_id)}, Data: {[hex(b) for b in message.data]}", end=" ")
            
             elif message.arbitration_id == 0x23F01:
                 data[2]=0 #message.data[0]
                 data[3]=to_signed(message.data[0] | message.data[1]<<8,16)
                 data[4]=to_signed(message.data[2] | message.data[3]<<8,16)
                 #data[4]=message.data[4]
             
                 #print(data);
                 #print(f"{val:+5d}")
                 for val in data:
                     #signed_val = to_signed(val)
                     print(f"{val:+11d}", end="", flush=True)
                 print()    
                 now = time.time() - start_time
                 xdata.append(now)
                 ydata.append(data[4])
                 xdata = xdata[-100:]
                 ydata = ydata[-100:]   
                 
                 # Update plot
                 line.set_data(xdata, ydata)
                 ax.relim() #
                 ax.autoscale_view() #
                 #ax.set_xlim(xdata[0], xdata[-1])  # Update X-axis only
                 plt.draw()
                 plt.pause(0.001)  # Just enough to render the plot


    if message is None:
        print('Timeout occurred, no message received.')
        os.system('sudo ifconfig can0 down')  #Disable can0
    
except KeyboardInterrupt:
    os.system('sudo ifconfig can0 down')  #Disable can0
    print("Exiting...")