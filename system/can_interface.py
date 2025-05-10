import can
import os
import threading
import time
import subprocess

#os.system('sudo ifconfig can0 down')  #Disable can0
#os.system('sudo ip link set can0 type can bitrate 500000 listen-only on')
#os.system('sudo ifconfig can0 up') # Enable can0 

#bus = can.interface.Bus(channel='can0', interface='socketcan')

class CANBus:
    def __init__(self,logger,channel="can0"):
        self.logger = logger
        self.channel = channel
        self._setup_can_interface()
        self.bus = can.interface.Bus(channel=self.channel, interface='socketcan')
        self.state = "initial"
        self.data_803f01=[0] * 2*8
        self.data_23f01=[0] * 8
        self.latest_data = {} 
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()

    def _setup_can_interface(self):
         subprocess.run(['sudo', 'ifconfig', 'can0', 'down'])
         subprocess.run(['sudo', 'ip', 'link', 'set', 'can0', 'type', 'can', 'bitrate', '500000', 'listen-only', 'on'])
         subprocess.run(['sudo', 'ifconfig', 'can0', 'up'])
    
    
    def _poll_loop(self):
        while True:
            try:
                message = self.bus.recv(10.0)
                if message is not None:
                    self._process_message(message)
            except Exception as e:
                print(f"CAN read error: {e}")
                time.sleep(1)

    def _process_message(self,message,):
        if message is not None and (message.arbitration_id == 0x803F01 or message.arbitration_id == 0x23F01):        
            if message.arbitration_id == 0x803F01 and self.state == "initial" and message.data[0] == 0xC6 :# and message.data[2] == 0xD0 :  
                #logger.info
                #  (message)
                #logger.info
                # (f"ID: {hex(message.arbitration_id)}", end="") #Data: {[f'0x{b:02X}' for b in message.data]}")
                for i in range(len(message.data)):
                        self.data_803f01[i+0]=message.data[i]
                self.state="2nd line"
                  
            elif message.arbitration_id == 0x803F01 and self.state == "2nd line":
                #logger.info
                # (f"{[hex(b) for b in message.data]}", end=" ")
                self.state="initial"
                for i in range(len(message.data)):
                        self.data_803f01[i+8]=message.data[i]            
                        #logger.info
                        # (f"{[hex(b) for b in data_803f01]}", end=" ")   
                bab = int.from_bytes(self.data_803f01[10:12], byteorder='little', signed=True)                
                soc = .1179 * bab - 494.8  #from spreadsheet SOC correlation chart 
                self.latest_data["soc"] =soc 
                return self.latest_data
            elif message.arbitration_id == 0x23F01:
                #logger.info
                # (f"{[hex(b) for b in message.data]}", end=" ")
                #state="initial"
                for i in range(len(message.data)):
                        self.data_23f01[i]=message.data[i]    
                #logger.info
                # (f"ID: {hex(message.arbitration_id)}", end="")           
                #logger.info
                # (f"{[hex(b) for b in data_23f01]}", end=" ")

                b01 = int.from_bytes(self.data_23f01[0:2], byteorder='little', signed=True)
                #B67 = int.from_bytes(data[6:8], byteorder='little', signed=True)
                #bab = int.from_bytes(data_803f01[10:12], byteorder='little', signed=True)
                measured_home_battery_charge_rate=-1*b01/2000
                self.latest_data["home_battery_charge_rate"] =measured_home_battery_charge_rate 
                return self.latest_data
                
                #logger.info
                # (f"bab = {bab:7d}, SOC= {soc:7.2f}, Discharge= {measured_home_battery_charge_rate:7.2f}")
        #else:
            #logger.error("⚠️  No CAN messages received in the last 10 seconds.") 

    def get_latest_data(self):
        return self.latest_data