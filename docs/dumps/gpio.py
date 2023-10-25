import gpiod
import time
import threading

class GPIOManager:
    def __init__(self):
        self.reset_gpio = None
        self.irq_gpio = None
        self.irq_callback = None
        self.reset_state = False

    def setup(self, reset_pin, irq_pin=-1):
        # Open the GPIO chip
        chip = gpiod.Chip("gpiochip0")

        # Setup the reset GPIO as an output, initially low
        self.reset_gpio = chip.get_line(reset_pin)
        self.reset_gpio.request(consumer="example", type=gpiod.LINE_REQ_DIR_OUT)
        self.reset_gpio.set_value(0)

        # Setup the IRQ GPIO if provided
        if irq_pin != -1:
            self.irq_gpio = chip.get_line(irq_pin)
            self.irq_gpio.request(consumer="example", type=gpiod.LINE_REQ_DIR_IN)
            self.irq_gpio.event_recv(timeout=0)  # Clear any existing events
            self.irq_gpio.request_events(gpiod.EVENT_TYPE_RISING_EDGE)
            self.irq_callback = threading.Thread(target=self.callback_irq)
            self.irq_callback.start()

    def callback_irq(self):
        while True:
            event = self.irq_gpio.event_wait(timeout=None)
            if event:
                print("IRQ Event detected!")
                # Call the user-defined callback function
                self.callbackIRQ()

    def set_reset(self, state):
        # Set the reset GPIO to the specified state
        self.reset_gpio.set_value(state)
        self.reset_state = state

    def callbackIRQ(self):
        # User-defined callback function when IRQ event occurs
        print("Custom IRQ Callback")

    def close(self):
        # Cleanup GPIOs
        if self.reset_gpio:
            self.reset_gpio.release()
        if self.irq_gpio:
            self.irq_gpio.release()
        if self.irq_callback:
            self.irq_callback.join()

# Example usage
def main():
    # Instantiate GPIOManager
    gpio_manager = GPIOManager()

    # Setup GPIOs
    gpio_manager.setup(reset_pin=17, irq_pin=27)

    # Set the reset GPIO to high (enabled)
    gpio_manager.set_reset(True)

    try:
        while True:
            # Your main application code goes here
            time.sleep(1)
    except KeyboardInterrupt:
        # Cleanup on keyboard interrupt
        gpio_manager.close()

if __name__ == "__main__":
    main()
