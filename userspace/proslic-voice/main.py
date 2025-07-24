#!/usr/bin/env python3
import logging
import signal
import traceback

# from ringer import Ringer
from config import Config
from manager import PhoneManager
from cli import PhoneCLI

# Device node
DEVICE = "/dev/proslic"

cli = None

# Basic configuration
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more verbosity
    # format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    format="[%(levelname)s] %(name)s: %(message)s",
    # handlers=[
    #     logging.StreamHandler(),  # Log to console
    #     # logging.FileHandler("myapp.log")  # Also log to file
    # ]
)

def signal_handler(sig, frame):
    global cli

    print("\nCtrl+C (SIGINT) caught, stopping...")
    if cli:
        cli.do_exit(None)

def begin():
    global cli

    config = Config()
    logger = logging.getLogger(__name__)
    logger.debug("begin()")

    with open(DEVICE, "r+b", buffering=0) as devfile:
        devices = config.begin()

        if not devices:
            return
        
        logger.debug(f"Device paths: {devices}")
        pm = PhoneManager(config, devfile)
        try:
            logger.info("Starting PhoneManager...")
            if not pm.begin(devices):
                logger.critical(f"Unable to initialize PhoneManager")
                return
            
            logger.info(f"PhoneManager Initialized with {pm.getChannelCount()} channels")

            cli = PhoneCLI(pm)
            cli.cmdloop()

            logger.error(f"[Main] before cleanup")

        except Exception as e:
            logger.error(f"[Main] Error during work: {e}")
            traceback.print_exc()
        finally:
            # Cleanup
            logger.error(f"[Main] cleanup")
            pm.close()
            logging.shutdown()
        return

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    begin()