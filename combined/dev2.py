import os
import can
import json
from datetime import datetime, timedelta, timezone, time
from wallbox import Wallbox, Statuses
from dotenv import load_dotenv
import pytz  # If you don't have it, run: pip install pytz
import requests
import logging
import sys
from logging.handlers import RotatingFileHandler

# 1. Create a top-level logger
logger = logging.getLogger("energy_manager")
logger.setLevel(logging.INFO)

# 2. Define a formatter (timestamps, level, message)
fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s")

# 3a. Handler #1 → stdout (this goes into the journal under systemd)
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(fmt)
logger.addHandler(ch)

# 3b. Handler #2 → rotating file on disk
fh = RotatingFileHandler(
    "/home/chuck/energy_manager/logs/energy_manager.log",
    maxBytes=5*1024*1024,  # rotate after 5 MB
    backupCount=3,         # keep 3 old files
    encoding="utf-8"
)
fh.setFormatter(fmt)
logger.addHandler(fh)

# 4. Replace all your prints with logger calls:
logger.info("Starting energy manager…")





w = Wallbox("chucktaylorsan@gmail.com", "Dogs2old!")
chargerId="913327"

CAR_CHARGE_RATE_MIN = 6.0 # amp eqivalent to 1.44kw
CAR_CHARGE_RATE_MAX = 32 # amp equivelent to ??kw
HOME_BATTERY_CAPACITY = 13.6 #kh
SOC_VALUE_CONSIDERED_FULL = 91 #SOC value considered full
START_OF_DAY_TIME = time(8, 30)    # 8:30 AM
END_OF_DAY_TIME = time(15, 00)     # 3:00 PM
LOCAL_TZ = 'America/Los_Angeles'  # Change this to your local timezone
UPDATE_INTERVAL = 2 # in minutes
local_tz = pytz.timezone(LOCAL_TZ)
state = "initial"

current_car_charging_rate = 0.0 #kw
car_charger_status=""
data_803f01 = [0] * 2*8
data_23f01 = [0] * 8
number=0
bab=0
b01=0
soc=0.0
measured_home_battery_charge_rate=0.0
first_loop_after_charging_time=False

os.system('sudo ifconfig can0 down')  #Disable can0
os.system('sudo ip link set can0 type can bitrate 500000 listen-only on')
os.system('sudo ifconfig can0 up') # Enable can0 

bus = can.interface.Bus(channel='can0', interface='socketcan')

# Today's date
today = datetime.now(timezone.utc).date()
now = datetime.now(timezone.utc)
end_time = now + timedelta(hours=12)
local_time = now.astimezone(local_tz)
next_time = local_time+timedelta(minutes=1) # now.astimezone(pytz.timezone(LOCAL_TZ) + timedelta(minutes=1))
authentication_time=now

authentication_time=now

def re_authenticate():
    global now, authentication_time
    if now-authentication_time > timedelta(hours=1):
         w.authenticate()
         print("re-authenticating")
         authentication_time=now

def safe_get_status():
    global chargerId
    try:
        return w.getChargerStatus(chargerId)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Token expired, re-authenticating...")
            w.authenticate()  # This should refresh your token
            return w.getChargerStatus(chargerId)  # Retry after auth
        else:
            raise


w.authenticate()
while 1:   
    now = datetime.now(timezone.utc)
    local_time = now.astimezone(local_tz)  

    if local_time >= next_time:
        next_time = local_time + timedelta(minutes=UPDATE_INTERVAL)
        re_authenticate()
        car_charger_dictionary = safe_get_status() #w.getChargerStatus(chargerId)
        car_charger_status = Statuses(car_charger_dictionary['status_id']).name
        current_car_charging_rate = car_charger_dictionary['config_data']['max_charging_current']
        print(f" ")
        print(f"time: {local_time.strftime('%H:%M')}",end=" ")
        print(f"status {car_charger_status} car_charging rate {current_car_charging_rate}")
        print(f"home_battery_SOC={soc:2.0f}%, measured home Battery Charge Rate= {measured_home_battery_charge_rate:2.1f}")     
        if soc > SOC_VALUE_CONSIDERED_FULL:  #fix for non liniarity in SOC data
            needed_home_battery_power = 0
        else:
            needed_home_battery_power = HOME_BATTERY_CAPACITY* (1-soc/100)
        print(f"Needed house battery power: {needed_home_battery_power:.2f} kWh")
        end_of_day_date = datetime.combine(local_time.date(), END_OF_DAY_TIME, local_tz)
        time_remaining = end_of_day_date - local_time
        hours_remaining = time_remaining.total_seconds() / 3600
        if hours_remaining <= 0 or current_car_charging_rate <= 0:
            #print("Time remaining is less than 0, setting to 1 hour")            
            optimum_home_battery_charge_rate = 0 
        else:
            optimum_home_battery_charge_rate = needed_home_battery_power / hours_remaining
        print(f"Optimum Home battery charge rate: {optimum_home_battery_charge_rate:2.2f} kW")

        if START_OF_DAY_TIME < local_time.time() < END_OF_DAY_TIME:
            if first_loop_after_charging_time == True:
                print(f"First iteration during daytime range")
                first_loop_after_charging_time = False                
            print("Time is between 8:30 AM and 3:00 PM")
            if soc>SOC_VALUE_CONSIDERED_FULL:  #fix for non liniarity in SOC data                 
                 soc=100
                 if measured_home_battery_charge_rate < 0:   #discharging
                      print(f"home battery full, home battery discharging")
                      if car_charger_status == "CHARGING":
                            print(f"car is charging at rate {current_car_charging_rate:2.2f} A")
                            new_car_charging_rate= current_car_charging_rate + measured_home_battery_charge_rate*1000/240
                            if new_car_charging_rate >= CAR_CHARGE_RATE_MIN:                                 
                                 w.setMaxChargingCurrent(chargerId, new_car_charging_rate)
                                 print(f"new car charging rate {new_car_charging_rate:2.2f} A")
                            else:
                                 print(f"car charging rate too low, stop charging car")
                                 w.pauseChargingSession(chargerId)     
                      else:
                            print(f"continue not charging car")
                 else:                                    #charging or dumping to grid      
                      print(f"home battery full, home battery charging or dumping to the grid")
                      if car_charger_status == "CHARGING":
                            print(f"car charging at rate {current_car_charging_rate:2.2f} A")
                            if measured_home_battery_charge_rate > 0:  #home battery charging
                                 new_car_charging_rate= current_car_charging_rate + measured_home_battery_charge_rate*1000/240
                            else:
                                 new_car_charging_rate= current_car_charging_rate + 1.0  #home battery dumping to the grid?
                            if new_car_charging_rate < CAR_CHARGE_RATE_MAX:
                                 w.setMaxChargingCurrent(chargerId, new_car_charging_rate)
                                 print(f"new car charging rate {new_car_charging_rate:2.2f} A")
                            else:
                                 print(f"car charging rate maxed no change")
                      else:
                            print(f"car not charging, lets try charging car")
                            if measured_home_battery_charge_rate > CAR_CHARGE_RATE_MIN:  #it actualy shows charge rate if near 100%soc   
                                 new_car_charging_rate= measured_home_battery_charge_rate*1000/240
                            else:
                                 new_car_charging_rate= CAR_CHARGE_RATE_MIN
                            if new_car_charging_rate <= CAR_CHARGE_RATE_MAX:
                                 w.setMaxChargingCurrent(chargerId, new_car_charging_rate)
                                 print(f"new car charging rate {new_car_charging_rate:2.2f} A")
                                 print(f"Starting car charging with current status =  {car_charger_status}")
                                 if car_charger_dictionary['status_id'] in [209, 164, 162]:
                                   w.resumeChargingSession(chargerId)  
                                 else:
                                   print(f"Status code is not good for resume charging, status={car_charger_status}")  
                            else:
                                 print(f"insufficent charge rate to start car charging")
                                   
            else: #home battery not full
                 if car_charger_status == "CHARGING":
                      print(f"home battery not full, car is charging @ rate {current_car_charging_rate:2.2f} A")
                      if measured_home_battery_charge_rate < optimum_home_battery_charge_rate:
                           print(f"car charging too fast @ rate {current_car_charging_rate:2.2f} A")
                           new_car_charging_rate = current_car_charging_rate - (optimum_home_battery_charge_rate-measured_home_battery_charge_rate)*1000/240
                           if new_car_charging_rate > CAR_CHARGE_RATE_MIN:
                                print(f"new car charging rate =  {new_car_charging_rate:2.2f} A")                     
                                w.setMaxChargingCurrent(chargerId, new_car_charging_rate)
                           else:
                                print(f"not enough power to charge car at min rate")
                                w.pauseChargingSession(chargerId)
                      else:
                           print(f"home battery charging too fast even with car charging at {current_car_charging_rate:2.2f} A")
                           new_car_charging_rate = current_car_charging_rate + (optimum_home_battery_charge_rate-measured_home_battery_charge_rate)*1000/240
                           if new_car_charging_rate < CAR_CHARGE_RATE_MAX:
                                w.setMaxChargingCurrent(chargerId, new_car_charging_rate)
                                print(f"new car charging rate {new_car_charging_rate:2.2f} A")  
                           else:
                                print(f"charger current maxed out no change")
                 else:
                      print(f"home battery not full, car not charging")  
                      if measured_home_battery_charge_rate >= optimum_home_battery_charge_rate+CAR_CHARGE_RATE_MIN*240/1000:
                           print(f"home battery charging too fast -lets try to charge car")
                           new_car_charging_rate = -(optimum_home_battery_charge_rate-measured_home_battery_charge_rate)*1000/240
                           if CAR_CHARGE_RATE_MAX > new_car_charging_rate >= CAR_CHARGE_RATE_MIN:
                                print(f"new car charging rate =  {new_car_charging_rate:2.2f} A")                     
                                w.setMaxChargingCurrent(chargerId, new_car_charging_rate)
                                print(f"Starting car charging with current status =  {car_charger_status}")
                                if car_charger_dictionary['status_id'] in [209, 164, 162]: 
                                    w.resumeChargingSession(chargerId)
                                else:
                                    print(f"Status code is not good for resume charging, status={car_charger_status}")       
                           else:    
                                print(f"not enough power to charge car at min rate")
                      else:
                           print(f"home battery charging slowly, continue no car charging")
        else:
           if first_loop_after_charging_time == False:
              print(f"First iteration outside of daytime range = pause car charging")
              first_loop_after_charging_time = True 
              if car_charger_status == "CHARGING":
                     w.pauseChargingSession(chargerId)
              else:
                     print(f"car not charging, no change")
              
           else:   
              print("Time is outside of daytime charging, no change in car charging")                                
            
                                 
               
                 

             
             

       
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