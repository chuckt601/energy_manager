# main.py
from multiprocessing import Process, Manager
from system.controller import EnergyManager
from dashboard.app import run_dashboard
import config

from system.can_interface import CANBus
from system.wallbox_interface import WallboxCharger
#from system.controller import EnergyManager

import time
from datetime import datetime, timedelta, timezone, time as dt_time
import logging
import colorlog
from logging.handlers import RotatingFileHandler
import csv
import os
import math


#can_latest_data = None
#wallbox_latest_data = None
elevation=0.0

def run_controller(can_data, wallbox_data,charging_mode):
    can = CANBus(logger)
    wallbox = WallboxCharger(config.WALLBOX_USER,config.WALLBOX_PASSWORD,config.WALLBOX_CHARGER_ID, logger)
    manager = EnergyManager(can_data,wallbox_data, wallbox, charging_mode, logger)
    time.sleep(20) #allow data collections threads to fill    
    
    while True:            
        can_data.update(can.get_latest_data())  #puts latest can data in shared space
        wallbox_data.update(wallbox.get_latest_data())
        manager.evaluate() 
        elevation = manager.get_elevation()
        log_charge_data(can_data,wallbox_data,elevation)
        trim_log_file(config.LOG_FILE) 
        time.sleep(config.UPDATE_INTERVAL)        
              
        
        
        


def setup_logger():
    logger = logging.getLogger("energy_manager")
    logger.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
        log_colors={
            "DEBUG":    "cyan",
            "INFO":     "green",
            "WARNING":  "yellow",
            "ERROR":    "red",
            "CRITICAL": "bold_red",
        }
    )
    ch.setFormatter(formatter)
    #ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    # File handler
    #fh = logging.FileHandler("logs/energy_manager.log")
    fh = RotatingFileHandler("logs/energy_manager.log", maxBytes=5*1024*1024, backupCount=3)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    
    


    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger

def log_charge_data(can_data, wallbox_data, elevation):
    # Create file with headers if not exists
    if not os.path.exists(config.LOG_FILE):
        with open(config.LOG_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "can_home_battery_charge_rate", "car_roc", "elevation"])

    timestamp = datetime.now().isoformat()
    can_rate = can_data.get("home_battery_charge_rate", 0)    
    car_rate = wallbox_data.get("current_car_charging_rate", 0)
    if wallbox_data.get("car_charger_status") != "CHARGING":
        car_rate = 0
    elevation=elevation*math.pi/180
    with open(config.LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, can_rate, car_rate, elevation])



def trim_log_file(filepath, max_age_hours=24):
    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    rows_to_keep = []

    with open(filepath, newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        for row in reader:
            try:
                timestamp = datetime.fromisoformat(row['timestamp'])
                if timestamp >= cutoff:
                    rows_to_keep.append(row)
            except Exception as e:
                print(f"Skipping row due to error: {e}")

    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_to_keep)


if __name__ == "__main__":
    
    # Setup logger
    logger = setup_logger()
    logger.warning(f"Starting Energy Manager=========================================")
    with Manager() as manager:
        can_data = manager.dict()
        wallbox_data = manager.dict()
        charging_mode = manager.Namespace()
        charging_mode.value = "solar"  # default

        controller_process = Process(target=run_controller, args=(can_data,wallbox_data,charging_mode))
        dashboard_process = Process(target=run_dashboard, args=(can_data, wallbox_data,charging_mode,logger,config))

        dashboard_process.start()        
        controller_process.start()

        #controller_process.join()
        #dashboard_process.join()

        while True:
            time.sleep(1)  # keep the main thread alive

