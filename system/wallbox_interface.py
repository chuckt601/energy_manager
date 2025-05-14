from wallbox import Wallbox, Statuses
#from wallbox.exceptions import WallboxException
import requests
from datetime import datetime, timedelta,timezone
import config
import threading
import time

class WallboxCharger:
    def __init__ (self, user, password, charger_id, logger):
        self.user = user
        self.password = password
        self.charger_id = charger_id
        self.logger = logger
        self.wallbox = Wallbox(self.user, self.password)
        self.latest_data = {}         
        self.now = datetime.now(timezone.utc)
        self.authentication_time = self.now        
        self.authenticate()  #initial authentication
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()
        self.old_charging_rate=0

    def authenticate(self):
        try:
            self.wallbox.authenticate()
        except requests.exceptions.HTTPError as e:
             self.logger.info("Wallbox authentication error code={e.response.status_code}")
             raise    


    def re_authenticate(self):
         if self.now-self.authentication_time > timedelta(hours=1):
             self.authenticate()
             self.logger.info("re-authenticating")
             self.authentication_time=self.now

    def safe_get_status(self):
         try:
             return self.wallbox.getChargerStatus(config.WALLBOX_CHARGER_ID)
         except requests.exceptions.HTTPError as e:
             global authentication_time
             if e.response.status_code == 401:
                 self.logger.warning("Wallbox code 401, Token expired, re-authenticating...")
                 self.wallbox.authenticate()  # This should refresh your token
                 self.authentication_time = self.now 

                 return self.wallbox.getChargerStatus(config.WALLBOX_CHARGER_ID)  # Retry after auth
             else:
                 self.logger.error("⚠️  wallbox error code not known =  {e.response.status_code}")
                 raise

    def _poll_loop(self):
        while True:
            try:
                self.now = datetime.now(timezone.utc)
                self.re_authenticate()
                #self.get_status = self.safe_get_status()
                car_charger_dictionary = self.safe_get_status() #w.getChargerStatus(chargerId)
                car_charger_status_code= car_charger_dictionary['status_id']
                car_charger_status = Statuses(car_charger_dictionary['status_id']).name
                current_car_charging_rate = car_charger_dictionary['config_data']['max_charging_current'] #in AMPS
                current_car_charging_rate = current_car_charging_rate*240/1000 #now car charging rate will report in kW
                self.latest_data["car_charger_status_code"] =car_charger_status_code
                self.latest_data["car_charger_status"] =car_charger_status
                self.latest_data["current_car_charging_rate"] = current_car_charging_rate                
                #self.logger.info(f"Wallbox status: {self.status}")
            except requests.exceptions.HTTPError as e:
                self.logger.error(f"Wallbox error: {e}")
            time.sleep(10)

    def get_latest_data(self):
        return self.latest_data  

    def set_new_charging_rate(self, new_charging_rate):     
        if new_charging_rate > config.CAR_CHARGE_RATE_MAX:
            new_charging_rate = config.CAR_CHARGE_RATE_MAX
        elif new_charging_rate < config.CAR_CHARGE_RATE_MIN:
            new_charging_rate = config.CAR_CHARGE_RATE_MIN  
        #internal to this routine we will use AMPS
        new_charging_rate=round(new_charging_rate*1000/240)    
        if new_charging_rate != self.old_charging_rate:
             self.old_charging_rate=new_charging_rate       
             try:
                 self.wallbox.setMaxChargingCurrent(config.WALLBOX_CHARGER_ID, new_charging_rate)
                 self.logger.debug(f"New charging rate set to {new_charging_rate} A")
                 self.logger.info(f"New charging rate set to {new_charging_rate*240/1000} kW")
             except requests.exceptions.HTTPError as e:
                 self.logger.error(f"Error setting new charging rate: {e}") 

    def pause_charging(self):        
        try:
            if self.latest_data["car_charger_status"]=="CHARGING":
                 self.wallbox.pauseChargingSession(config.WALLBOX_CHARGER_ID)
                 self.logger.info("Charging paused")
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Error pausing charging: {e}")

    def resume_charging(self):
        try:
            if self.latest_data["car_charger_status_code"] in [209, 164, 162, 182]:                                       
                self.wallbox.resumeChargingSession(config.WALLBOX_CHARGER_ID)
                self.logger.info("Charging resumed")                
                return   
                       
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Error resuming charging: {e}")        

        