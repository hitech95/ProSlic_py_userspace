import select
import os
import traceback
import threading
import logging
import gpiod
from gpiod.line import Edge

def edge_type_str(event):
    if event.event_type is event.Type.RISING_EDGE:
        return "Rising"
    if event.event_type is event.Type.FALLING_EDGE:
        return "Falling"
    return "Unknown"

class GPIOManager(object):
    def __init__(self, path, irq_pin, interrupt_event):
        self.logger = logging.getLogger("GPIOManager")
        self.logger.debug("__init__")

        # Threading event
        self.interrupt_event = interrupt_event

        # Default states
        self.irq_thread = None
        self.reset_state = False

        # Setup the IRQ GPIO if provided
        self.irq_gpio = gpiod.request_lines(
            path, 
            consumer="GPIOManager",
            config={
                irq_pin: gpiod.LineSettings(edge_detection=Edge.FALLING)
            }
        )

    def __str__(self):
        return f"GPIOManager(name={self.name})"

    def setup(self):
        self.logger.debug("setup()")
        try:
            # gpiod C bindings thread signaling
            self.done_fd = os.eventfd(0)

            self.poll = select.poll()
            self.poll.register(self.irq_gpio.fd, select.POLLIN)
            self.poll.register(self.done_fd, select.POLLIN)
        
            self.irq_thread = threading.Thread(target=self.callback_irq)
            self.irq_thread.start()
        except:
            traceback.print_exc()

    def callback_irq(self):
        running = True
        try:
            while running:
                # Wait for a fd to have data
                # depending on what fd is ready it can be exit event or gpio event
                for fd, _ in self.poll.poll():
                    if fd == self.done_fd:
                        # Exit signal received
                        running = False
                        break
                    elif fd == self.irq_gpio.fd: 
                        # Blocks until at least one event is available
                        for event in self.irq_gpio.read_edge_events():
                            # FIXME: this is hardcoded disabled as it is very annoing
                            # self.logger.debug(f"line: {event.line_offset} type: Falling event #{event.line_seqno}")
                            self.interrupt_event.set()
        except Exception as ex:
            self.logger.error(ex)
            self.logger.debug("Customise the example configuration to suit your situation")
        self.logger.info("background thread exiting...")

    def close(self):
        self.logger.debug("Attempting to close")

        # Wait for the IRQ callback thread to finish
        if self.irq_thread.is_alive():
            # Set the stop event to signal the thread to stop
            os.eventfd_write(self.done_fd, 1)
            self.irq_thread.join()

        # Cleanup FD
        os.close(self.done_fd)
        # Cleanup GPIOs
        self.irq_gpio.release()
        self.logger.debug("Closed")