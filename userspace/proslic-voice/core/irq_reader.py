import logging
import os
import queue
import select
import time
import threading
import traceback

from abc import ABC, abstractmethod
from typing import Any

class IrqReader(ABC):
    def __init__(self, name: str, interrupt_queue: queue.Queue, device: Any):
        self._logger = logging.getLogger(name)
        
        self._name = name
        self._interrupt_queue = interrupt_queue
        self._device = device

        # thread signaling
        self._fd = None
        self._done_fd = None
        self._poll = select.poll()

        # Thread
        self._thread = threading.Thread(target=self._irq_run)

        self._logger.debug("__init__")
        pass

    def __str__(self):
        return f"{self._name}(device={self._device})"

    @abstractmethod
    def _callback_irq(self):
        """This method is called when the fd notify data (IRQ) is availabe."""
        pass

    def setup(self):
        """Initialize resources and start IRQ monitoring."""
        try:
            # Event FD for signaling thread exit
            self._done_fd = os.eventfd(0)
            
            # Register poll events
            self._poll.register(self._fd, select.POLLIN)
            self._poll.register(self._done_fd, select.POLLIN)

            # Start thread if exist!
            self._thread.start()
            return True
        except Exception as e:
            self._logger.fatal("Failed to set up Char dev IRQ reader")
            self._logger.exception(e)
            traceback.print_exc()
            self.close()
            return False

    def close(self):
        """Clean up resources and stop IRQ monitoring."""
        try:
            if self._thread and self._thread.is_alive():
                os.eventfd_write(self._done_fd, 1)
                self._thread.join()

            if self._poll:                
                    self._poll.unregister(self._fd)
                    self._poll.unregister(self._done_fd)                

            if self._fd is not None:
                os.close(self._fd)
            if self._done_fd is not None:
                os.close(self._done_fd)
        except Exception:
            pass

    def _irq_run(self):
        running = True

        self._logger.debug("Starting IRQ polling thread")
        try:
            while running:
                for fd, _ in self._poll.poll():
                    if fd == self._done_fd:
                        running = False
                        break
                    elif fd == self._fd:
                        self._callback_irq()
        except Exception as e:
            self._logger.error("Unexpected error in IRQ polling loop")
            self._logger.exception(e)
            traceback.print_exc()
        self._logger.info("Background thread exiting...")

    def _emit(self, data = None):
        # Push the data to the IRQ process queue of PhoneManager
        self._interrupt_queue.put({
            "device": self._device,
            "timestamp": time.time(),
            "source": self._name,
            "data": data
        })

    
