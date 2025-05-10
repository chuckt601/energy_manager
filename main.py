# main.py
from multiprocessing import Process, Manager
#from system.controller import EnergyManager
from dashboard.app import run_dashboard
import config

from system.can_interface import CANBus
from system.wallbox_interface import WallboxCharger

import time
from datetime import datetime, timedelta, timezone, time as dt_time
import logging


#can_latest_data = None
#wallbox_latest_data = None

def run_controller(can_data, wallbox_data):
    can = CANBus(logger)
    wallbox = WallboxCharger(config.WALLBOX_USER,config.WALLBOX_PASSWORD,config.WALLBOX_CHARGER_ID, logger)
    #manager = EnergyManager(can, wallbox)
    #global can_latest_data, wallbox_latest_data

    
    while True:
        #manager.evaluate()
        #can_data     = can.get_latest_data()
        #wallbox_data = wallbox.get_latest_data()
        can_data.update(can.get_latest_data())
        wallbox_data.update(wallbox.get_latest_data())

        print(f"Can data: {can_data}")
        print(f"Wallbox data: {wallbox_data}")
        time.sleep(5)

def setup_logger():
    logger = logging.getLogger("energy_manager")
    logger.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    # File handler
    fh = logging.FileHandler("logfile.log")
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger


if __name__ == "__main__":
    
    # Setup logger
    logger = setup_logger()
    with Manager() as manager:
        can_data = manager.dict()
        wallbox_data = manager.dict()
        controller_process = Process(target=run_controller, args=(can_data,wallbox_data))
        dashboard_process = Process(target=run_dashboard, args=(can_data, wallbox_data))

        controller_process.start()
        dashboard_process.start()

        #controller_process.join()
        #dashboard_process.join()

        while True:
            time.sleep(1)  # keep the main thread alive

