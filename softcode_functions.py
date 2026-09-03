from village.devices.sound_device import sound_device
import time_utils
from gpiozero import LED
from village.custom_classes.direct_functions_base import DirectFunctionsBase

class DirectFunctions(DirectFunctionsBase):
    def function1(self):
        """Click + Sound"""
        # Gated on the OptoGrid's battery level. self.task.og is the OptoGrid
        # instance created (and connected/logging) in the running task's
        # start() -- see raspberry_optogrid_demo.py.
        og = self.task.og
        battery_mv = og.read_battery_mv()

        # Battery range is roughly 3500 (empty) to 4200 mV (full) -- keep
        # going only above 3900 mV.
        if battery_mv is not None and battery_mv > 3900:
            print(f":) enough battery: {battery_mv} mV")
            # 1. Register the click as a Raspberry-side event.
            self.task.register_raspberry_event(
                "button_click", time_utils.now_timestamp()
            )
            # 2. Mark this moment in the OptoGrid's own IMU data stream.
            og.sync(self.task.current_trial)
            # 3. Play the sound loaded in the task's start().
            sound_device.play()
            # Let create_trial's waiting loop know the sound was played.
            self.task.sound_played_event.set()
        else:
            print(f"NOT enough battery: {battery_mv} mV")
