import os
import can
from datetime import datetime, timedelta, timezone, time
from wallbox import Wallbox, Statuses
from dotenv import load_dotenv
import pytz  # If you don't have it, run: pip install pytz



os.system('sudo ifconfig can0 down')  #Disable can0
os.system('sudo ip link set can0 type can bitrate 500000 listen-only on')
os.system('sudo ifconfig can0 up') # Enable can0 



bus = can.interface.Bus(channel='can0', bustype='socketcan')

w = Wallbox("chucktaylorsan@gmail.com", "Dogs2old!")
chargerId="913327"

CAR_CHARGE_RATE_MIN = 6.0 # amp eqivalent to 1.44kw
CAR_CHARGE_RATE_MAX = 32 # amp equivelent to ??kw
HOME_BATTERY_CAPACITY = 13.6 #kh
START_OF_DAY_TIME = time(8, 30)    # 8:30 AM
END_OF_DAY_TIME = time(15, 00)     # 3:00 PM
LOCAL_TZ = 'America/Los_Angeles'  # Change this to your local timezone
UPDATE_INTERVAL = 1  # in minutes
local_tz = pytz.timezone(LOCAL_TZ)
state = "initial"
car_charging_state = "false"
current_car_charging_rate = 0.0 #kw
car_charger_status
data_803f01 = [0] * 2*8
data_23f01 = [0] * 8
number=0
bab=0
b01=0
soc=0.0
measured_home_battery_charge_rate=0.0


# Today's date
today = datetime.now(timezone.utc).date()
now = datetime.now(timezone.utc)
end_time = now + timedelta(hours=12)
local_time = now.astimezone(local_tz)
next_time = local_time # now.astimezone(pytz.timezone(LOCAL_TZ) + timedelta(minutes=1))

def authenticate(self):
    # Authenticate with the credentials above
    w.authenticate()
def get_charger_status(self):    
     chargerStatus = w.getChargerStatus(chargerId)
     return chargerStatus
def set_max_charging_current(self, chargerId, current): 
    w.setMaxChargingCurrent(chargerId, 9.0)

authenticate()

while 1:
    now = datetime.now(timezone.utc)
    local_time = now.astimezone(local_tz)
    
    if local_time >= next_time:
        next_time = local_time + timedelta(minutes=UPDATE_INTERVAL)
        
        print(f"time: {local_time.strftime('%H:%M')}",end=" ")
        print(f"home_battery_SOC={soc:2.0f}%, measured home Battery Charge Rate= {measured_home_battery_charge_rate:2.1f}")     

        if START_OF_DAY_TIME < local_time.time() < END_OF_DAY_TIME:
            #print("Time is between 8:30 AM and 3:00 PM")
            if soc>89:  #fix for non liniarity in SOC data
                 soc=100
            needed_home_battery_power = HOME_BATTERY_CAPACITY* (1-soc/100)
            print(f"Needed house battery charge: {needed_home_battery_power:.2f} kWh")
            end_of_day_date = datetime.combine(local_time.date(), END_OF_DAY_TIME, local_tz)
            time_remaining = end_of_day_date - local_time
            hours_remaining = time_remaining.total_seconds() / 3600
            #print(f"Hours remaining: {hours_remaining:.2f} hours")
            #print(f"Time remaining: {time_remaining}")
            optimum_home_battery_charge_rate = needed_home_battery_power / hours_remaining
            print(f"Home battery charge rate: {optimum_home_battery_charge_rate:2.2f} kW")
            
            if measured_home_battery_charge_rate+current_car_charging_rate> optimum_home_battery_charge_rate+CAR_CHARGE_RATE_MIN:
                 current_car_charging_rate = measured_home_battery_charge_rate + current_car_charging_rate - optimum_home_battery_charge_rate 
                 print(f"New Car charging rate: {current_car_charging_rate:2.2f} kW")
                 car_charging_state = "true"
                 current_car_charging_rate = max(current_car_charging_rate ,CAR_CHARGE_RATE_MIN)
            else:
                 print(f"insufficent power to charge car")
                 car_charging_state = "true"
                 current_car_charging_rate = 0
                 
                 

             
             

       
    message = bus.recv(10.0)
    if message is not None and (message.arbitration_id == 0x803F01 or message.arbitration_id == 0x23F01):        
        if message.arbitration_id == 0x803F01 and state == "initial" and message.data[0] == 0xC6 :# and message.data[2] == 0xD0 :  
            #print (message)
            #print(f"ID: {hex(message.arbitration_id)}", end="") #Data: {[f'0x{b:02X}' for b in message.data]}")
            for i in range(len(message.data)):
                    data_803f01[i+0]=message.data[i]
            state="2nd line"
            number=0
                    #B03 = int.from_bytes(data[0:4], byteorder='little', signed=True)
                    #B47 = int.from_bytes(data[4:8], byteorder='little', signed=True)
                    #print(f"B03 = {B03:7d}, B47 = {B47:7d}", end=" ")
                    #print(f"ID: {(message.arbitration_id)}, Data: {[(b) for b in message.data]}")   
        elif message.arbitration_id == 0x803F01 and state == "2nd line":
            #print(f"{[hex(b) for b in message.data]}", end=" ")
            state="initial"
            for i in range(len(message.data)):
                    data_803f01[i+8]=message.data[i]            
                    #print(f"{[hex(b) for b in data_803f01]}", end=" ")   
            bab = int.from_bytes(data_803f01[10:12], byteorder='little', signed=True)

        elif message.arbitration_id == 0x23F01:
            #print(f"{[hex(b) for b in message.data]}", end=" ")
            #state="initial"
            for i in range(len(message.data)):
                    data_23f01[i]=message.data[i]    
            #print(f"ID: {hex(message.arbitration_id)}", end="")           
            #print(f"{[hex(b) for b in data_23f01]}", end=" ")

            b01 = int.from_bytes(data_23f01[0:2], byteorder='little', signed=True)
            #B67 = int.from_bytes(data[6:8], byteorder='little', signed=True)
            #bab = int.from_bytes(data_803f01[10:12], byteorder='little', signed=True)
            measured_home_battery_charge_rate=-1*b01/2000
            soc = 100-(4976-bab)*52/371
            soc = .1179 * bab - 494.8  #from spreadsheet SOC correlation chart
            
            #print(f"bab = {bab:7d}, SOC= {soc:7.2f}, Discharge= {measured_home_battery_charge_rate:7.2f}")

       











#for i in range(24):
#                number+=data[i]*2**i 
#            print(number)    

            

    #if message is None:
    #    print('Timeout occurred, no message received.')

    #os.system('sudo ifconfig can0 down')  #Disable can0