import time
import queue

from typing import IO, Any

from core.irq_reader import IrqReader

class IRQCharDevReader(IrqReader):
    def __init__(self, interrupt_queue: queue.Queue, device_id: Any, device_file: IO[bytes], ):
        super().__init__("IRQ_CharDevReader", interrupt_queue, device_id)

        self._dev_file = device_file
        self._fd = device_file.fileno()

        pass

    def setup(self):
        self._logger.debug("setup()")
        super().setup()

    def close(self):
        self._logger.debug("Attempting to close")
        super().close()
        self._logger.debug("Closed")

    def _callback_irq(self):
        self._logger.debug("IRQ received")
        try:
            self._logger.debug(f"Attempting to read received IRQ")

            # Read the interrupt data to clear IRQ0 to easily identify wich registers/channel to query
            data = self._dev_file.read(1)
            self._logger.debug(f"IRQ received: value={hex(data)}")

            # Push the data to the IRQ process queue of PhoneManager
            self.emit(data)
        except BlockingIOError:
            # No data to read yet
            pass
        except Exception as e:
            self._logger.error("Error reading from proslic device")
            self._logger.exception(e)
