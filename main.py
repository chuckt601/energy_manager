# main.py
from multiprocessing import Process, Manager
from system.controller import EnergyManager
from dashboard.app import run_dashboard
import config

from system.can_interface import CANBus
from system.wallbox_interface import WallboxCharger

import time
from datetime import datetime, timedelta, timezone, time as dt_time
import logging
import colorlog
from logging.handlers import RotatingFileHandler


#can_latest_data = None
#wallbox_latest_data = None

def run_controller(can_data, wallbox_data,charging_mode):
    can = CANBus(logger)
    wallbox = WallboxCharger(config.WALLBOX_USER,config.WALLBOX_PASSWORD,config.WALLBOX_CHARGER_ID, logger)
    manager = EnergyManager(can_data,wallbox_data, wallbox, charging_mode, logger)
    time.sleep(5) #allow data collections threads to fill

    
    while True:
               
        can_data.update(can.get_latest_data())  #puts latest can data in shared space
        wallbox_data.update(wallbox.get_latest_data())
        time.sleep(config.UPDATE_INTERVAL)
        #logger.info(f"current mode= {charging_mode.value}")
        #logger.info(f"Can data: {can_data}")
        #logger.info(f"Wallbox data: {wallbox_data}")
        manager.evaluate() 


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


if __name__ == "__main__":
    
    # Setup logger
    logger = setup_logger()
    logger.warning(f"Starting Energy Manager")
    with Manager() as manager:
        can_data = manager.dict()
        wallbox_data = manager.dict()
        charging_mode = manager.Namespace()
        charging_mode.value = "solar"  # default

        controller_process = Process(target=run_controller, args=(can_data,wallbox_data,charging_mode))
        dashboard_process = Process(target=run_dashboard, args=(can_data, wallbox_data,charging_mode,logger))

        dashboard_process.start()        
        controller_process.start()

        #controller_process.join()
        #dashboard_process.join()

        while True:
            time.sleep(1)  # keep the main thread alive

