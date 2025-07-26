import gpiod
import queue

from gpiod.line import Edge
from typing import Any

from core.irq_reader import IrqReader

class IRQGPIOReader(IrqReader):
    def __init__(self, interrupt_queue: queue.Queue, device_id: Any, pin: int, path = "/dev/gpiochip0"):
        super().__init__("IRQ_GPIOReader", interrupt_queue, device_id)

        self._gpio_chip = path
        self._gpio_pin = pin
        self._gpio = None

        pass

    def setup(self):
        self._logger.debug("setup()")

        # Setup the IRQ GPIO
        self._gpio = gpiod.request_lines(
            self._gpio_chip, 
            consumer = self.name,
            config = {
                self._gpio_pin: gpiod.LineSettings(edge_detection=Edge.FALLING)
            }
        )

        # Assign gpio file descriptor
        self._fd = self._gpio.fd

        super().setup()

    def close(self):
        self._logger.debug("Attempting to close")
        super().close()
        self._logger.debug("Closed")

    def _callback_irq(self):
        # Blocks until at least one event is available
        for event in self._gpio.read_edge_events():
            # FIXME: this is hardcoded disabled as it is very polluting
            # self._logger.debug(f"gpio: {event.line_offset} type: Falling event #{event.line_seqno}")

            # Push the data to the IRQ process queue of PhoneManager
            self._emit()
            break
