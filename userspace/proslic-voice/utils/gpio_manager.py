import time
import traceback
import threading

import gpiod


class GPIOManager(object):
    def __init__(self, name, reset_pin, irq_pin=-1):
        print("GPIOManager.__init__")

        # Default states
        self.name = name
        self.irq_callback = None
        self.reset_state = False

        # Open the GPIO chip
        chip = gpiod.Chip("gpiochip0")
        self.reset_gpio = chip.get_line(reset_pin)

        # Setup the IRQ GPIO if provided
        self.irq_gpio = None
        if irq_pin != -1:
            self.irq_gpio = chip.get_line(irq_pin)

        # Thread signaling
        self.stop_event = threading.Event()

    def __str__(self):
        return f"GPIOManager(name={self.name})"

    def _setup(self):
        try:
            # Setup the reset GPIO as an output, initially low
            self.reset_gpio.request(
                consumer=self.name, type=gpiod.LINE_REQ_DIR_OUT)
            # self.reset_gpio.set_value(0)

            # Setup the IRQ GPIO if provided
            if self.irq_gpio != None:
                self.irq_gpio.request(consumer=self.name,
                                      type=gpiod.LINE_REQ_EV_FALLING_EDGE)
                self.irq_callback = threading.Thread(target=self.callback_irq)
                self.irq_callback.start()
        except:
            traceback.print_exc()

    def callback_irq(self):
        while not self.stop_event.is_set():
            if self.irq_gpio.event_wait(sec=60):
                event = self.irq_gpio.event_read()
                print("IRQ Event detected!")
                # Call the user-defined callback function
                self.callbackIRQ(event)

    def setReset(self, state):
        # Set the reset GPIO to the specified state
        self.reset_gpio.set_value(state)
        self.reset_state = state

    def callbackIRQ(self, event):
        # User-defined callback function when IRQ event occurs
        print("Custom IRQ Callback", event.type)

    def close(self):
        # Set the stop event to signal the thread to stop
        self.stop_event.set()
        # Cleanup GPIOs
        if self.reset_gpio:
            self.reset_gpio.release()
        if self.irq_gpio:
            self.irq_gpio.release()
        # Wait for the IRQ callback thread to finish
        if self.irq_callback and self.irq_callback.is_alive():
            self.irq_callback.join()
