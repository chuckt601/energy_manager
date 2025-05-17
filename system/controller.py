from datetime import datetime, date
import config
#from system.wallbox_interface import WallboxCharger
from astral import LocationInfo
from astral.sun import sun
from astral import sun as astral_sun
import pytz

class EnergyManager:
    def __init__(self, can_data, wallbox_data, wallbox, charging_mode, logger):
        self.can_data = can_data
        self.wallbox_data = wallbox_data
        self.wallbox=wallbox
        self.charging_mode = charging_mode
        self.logger=logger
        self.SOC = 0.0
        self.home_ROC_KW = 0.0
        self.car_ROC_KW = 0.0
        self.last_state = None
        self.last_charging_mode="None"
        self.time_of_day_preiod="None"          
        self.elevation=0.0 # degrees

    def check_charging_mode(self):
        if self.charging_mode.value != self.last_charging_mode:
            self.last_charging_mode= self.charging_mode.value
            self.logger.info(f"New Charging Mode = {self.last_charging_mode}")

    def get_time_period(self):
        city = LocationInfo(config.CITY, "USA", config.LOCAL_TZ, 37.27043, -121.80013)
        now = datetime.now(pytz.timezone(config.LOCAL_TZ))
        hour = now.hour
        #self.logger.debug(f"now={now}")
        #s = sun(city.observer, date=date.today(), tzinfo=city.timezone)
        #self.logger.debug(f"Sunrise: {s['sunrise'].strftime('%H:%M:%S')}")
        #self.logger.debug(f"Sunset:  {s['sunset'].strftime('%H:%M:%S')}")
        #sunset_hour=s['sunset'].hour
        #sunrise_hour=s['sunrise'].hour

        self.elevation = astral_sun.elevation(city.observer, now)
        self.logger.debug(f"solar elevation = {self.elevation}")
        #self.logger.debug(f"sunset hour = {sunset_hour}")
        #self.logger.debug(f"now hour = {hour}")

        if hour<12 and self.elevation<config.ELEVATION_MIN:
            return 'night'
        elif self.elevation>config.ELEVATION_MIN:
            return 'day'
        else:
            return 'evening'            

        #if config.START_OF_DAY <= hour < config.END_OF_DAY:
        #    return "day"
        #elif config.END_OF_DAY <= hour < config.START_OF_NIGHT:
        #    return "evening"
        #else:
        #    return "night"

    def get_SOC(self):
        return float(self.can_data.get("soc", 0))    
    def get_home_ROC(self):
        return float(self.can_data.get("home_battery_charge_rate", 0)) 
    def get_car_ROC(self):
        return float(self.wallbox_data.get("current_car_charging_rate", 0)) 
    def calc_optimum_home_ROC(self):
        if self.time_of_day_period == "day":
            if self.SOC >= config.SOC_VALUE_CONSIDERED_FULL:
                return 0
            else:    
                hour = datetime.now().hour
                hours_to_charge = config.END_OF_DAY-hour 
                needed_home_battery_power = config.HOME_BATTERY_CAPACITY* (1-self.SOC/100)
                optimum_home_ROC= needed_home_battery_power/hours_to_charge 
                self.logger.info(f"optimum home bat ROC = {optimum_home_ROC}")
                return optimum_home_ROC           
        return 0             


    def get_soc_status(self):          
            if self.SOC >= config.SOC_VALUE_CONSIDERED_FULL :  #full
                return "full"
            else:                
                return "not_full"

    def get_charging_status(self):
        return "charging" if self.wallbox_data.get("car_charger_status") == "CHARGING" else "idle"

    def evaluate(self): 
        
             
        self.SOC = self.get_SOC()
        self.home_ROC_KW = self.get_home_ROC()
        self.car_ROC_KW = self.get_car_ROC()
        #self.logger.info(f"SOC={self.SOC}, home_ROC Kw={self.home_ROC_KW}, car ROC Amp={self.car_ROC_KW
        # } ")
        self.time_of_day_period = self.get_time_period()
        soc_status = self.get_soc_status()
        charging_status = self.get_charging_status()
        self.check_charging_mode()        
        current_state = f"{self.time_of_day_period}-{soc_status}-{charging_status}"
        self.logger.info(f"home: ROC={self.home_ROC_KW}, SOC={self.SOC}")
        self.logger.info(f"car : ROC={self.car_ROC_KW}, Status = {charging_status}")

        if current_state != self.last_state:
            #self.logger.info(f"Transitioning to state: {current_state} (mode: {self.charging_mode.value})")
            self.last_state = current_state

        # FSM logic depending on mode
        if self.charging_mode.value == "manual":
            return                        # manual mode: change nothing, user controls everything
        if self.time_of_day_period == 'night':
            if self.charging_mode.value == "solar_and_night":
                self.set_charging_rate(config.CAR_CHARGE_RATE_MAX)   #set charge rate high
                self.start_charging()        #set charge on
                return
            else:
                self.stop_charging()         #pause
                return
        elif self.time_of_day_period == 'evening':
             self.stop_charging()            #pause
             return
        else: # day
             if soc_status == "full":
                if self.home_ROC_KW > config.HOME_ROC_CONSIDERED_NOT_CHARGING:
                    self.logger.debug(f"not actualy full home bat is still charging")
                    if charging_status == "charging":
                        new_car_roc = self.car_ROC_KW + self.home_ROC_KW  #*1000/240
                        #self.logger.info(f"new car roc = {new_car_roc}")
                        if new_car_roc <= config.CAR_CHARGE_RATE_MAX:
                             self.set_charging_rate(new_car_roc)
                             return 
                        else: 
                             self.set_charging_rate(config.CAR_CHARGE_RATE_MAX)                           
                             return
                    else: # not charging
                        if self.home_ROC_KW > config.CAR_CHARGE_RATE_MIN:
                             self.set_charging_rate(self.home_ROC_KW) 
                             self.start_charging()
                             return
                        
                elif config.HOME_ROC_CONSIDERED_NOT_DISCHARGING < self.home_ROC_KW < config.HOME_ROC_CONSIDERED_NOT_CHARGING:  # perfect or dumping to the grid (increase charge to find out)
                    self.logger.debug(f"perfect or dumping to the grid- charge or charge more")
                    if charging_status == "charging":
                        new_car_roc = self.car_ROC_KW + .24 #KW
                        self.set_charging_rate(new_car_roc)
                        return 
                    else:
                        self.set_charging_rate(config.CAR_CHARGE_RATE_MIN)
                        self.start_charging()
                        return
                elif -0.3 <self.home_ROC_KW < config.HOME_ROC_CONSIDERED_NOT_CHARGING:  # a little discharging is OK
                    self.logger.debug(f"a little discharge is perfece- no change")
                    return
                elif self.home_ROC_KW < -.3:     #big discharging  decrease by formula
                    self.logger.debug(f"big discharge- decrease by formula")
                    if charging_status == "charging":
                        new_car_roc = self.car_ROC_KW + self.home_ROC_KW  #*1000/240
                        if new_car_roc>=config.CAR_CHARGE_RATE_MIN:
                             self.set_charging_rate(new_car_roc)
                             return 
                        else:
                             self.stop_charging()
                             return
                return             
             else: #soc still charging
                  optimum_home_ROC=self.calc_optimum_home_ROC() 
                  if charging_status == "charging":
                        available_power = (self.home_ROC_KW - optimum_home_ROC) + self.car_ROC_KW

                        if available_power > config.CAR_CHARGE_RATE_MIN :
                             new_car_roc = available_power # + self.car_ROC_KW
                             self.set_charging_rate(new_car_roc)
                             return
                        else:
                             self.stop_charging()
                             return      
                  else:  # not charging
                        new_car_roc = (self.home_ROC_KW - optimum_home_ROC) #*1000/240   
                        if new_car_roc>=config.CAR_CHARGE_RATE_MIN:                   
                             self.set_charging_rate(new_car_roc)
                             self.start_charging()
                             return
                        return     
                           
    def start_charging(self):
        #self.logger.info("Command: START charging")
        # call wallbox.start_charging() or send CAN command here
        self.wallbox.resume_charging()           

    def stop_charging(self):       
        self.wallbox.pause_charging()

    def set_charging_rate(self,new_rate):
        self.wallbox.set_new_charging_rate(new_rate)

    def get_elevation(self):
        return self.elevation    

 



        
          
      
