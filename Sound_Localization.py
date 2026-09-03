import random
import threading
import time

from sound_functions import whitenoise_generator
from village.custom_classes.task_base import TaskBase
from village.devices.optogrid import OptoGrid
from village.devices.sound_device import sound_device
from village.scripts.time_utils import time_utils



class RaspberryOptogridDemo(TaskBase):
    """No controller involved (BEHAVIOR_CONTROLLER = OTHER): each trial
    generates a fresh random sound (see create_trial) and then just waits on
    a GUI button.

    Click "Click + Sound" (function50, in direct_functions.py) in the
    FUNCTIONS tab while this task is running:
    - If the OptoGrid's battery is above 50%, it registers the click,
      marks the moment in the OptoGrid's IMU stream, and plays the sound
      generated for this trial. Two seconds later, the trial ends.
    - If the battery is 50% or below (or unreadable), it just prints
      "not enough battery" and nothing else happens -- the trial keeps
      waiting for another click.
    """

    def __init__(self):
        super().__init__()

        self.info = """
        Raspberry + OptoGrid Demo
        ----------------------------------------------------------------
        No Bpod. Connects the OptoGrid and starts IMU logging for the whole
        session.

        Each trial generates a 1s whitenoise burst on only the left or only
        the right speaker (picked at random), at a random volume between 0
        and 1 times the speaker's 70dB-calibrated gain. It then waits for a
        GUI button click (function50) to play it -- gated on OptoGrid
        battery level -- then waits 2 more seconds before moving on to the
        next trial.
        """

    def start(self):
        """Starts the OptoGrid connection + IMU logging for the whole
        session. The sound itself is generated fresh every trial (random
        side, random volume) in create_trial, not here.
        """

        # device_name defaults to "OptoGrid 1" -- change it here if yours is
        # named differently.
        self.og = OptoGrid(
            sessions_directory=self.sessions_directory, filename=self.filename
        )
        if self.og.connect():
            self.og.start_imu_logging()
        else:
            print("Warning: could not connect to the OptoGrid")

        # Set by function50 (direct_functions.py) once it has played the
        # sound; create_trial waits on this instead of polling self.task
        # state directly.
        self.sound_played_event = threading.Event()

    def create_trial(self):
        """Generates a fresh random sound for this trial -- whitenoise on
        only the left or only the right speaker (picked at random), with a
        random 0-1 multiplier applied on top of the speaker's 70dB-calibrated
        gain -- then waits for function50 to play it (see
        direct_functions.py), then waits 2 more seconds before ending the
        trial. If the task is stopped while waiting, the loops exit via
        self.should_stop.
        """

        self.side = random.choice(["left", "right"])
        # select a random intensity from 40, 50, 60 or 70 dB
        self.intensity = random.choice([40, 50, 60, 70])
        speaker = 0 if self.side == "left" else 1
        gain = self.calibrations.sound_calibration.get_sound_gain(
            speaker=speaker, dB=self.intensity, sound_name="whitenoise"
        )
        sound = whitenoise_generator(duration=1, gain=gain)
        if self.side == "left":
            sound_device.load(left=sound, right=None)
        else:
            sound_device.load(left=None, right=sound)

        self.sound_played_event.clear()

        t0 = time_utils.now_timestamp()
        self.register_start_trial(raspberry_timestamp=t0, controller_timestamp=t0)

        while not self.should_stop and not self.sound_played_event.is_set():
            self.sound_played_event.wait(timeout=0.05)

        if self.sound_played_event.is_set():
            deadline = time_utils.now_timestamp() + 2
            while not self.should_stop and time_utils.now_timestamp() < deadline:
                time.sleep(0.05)

        self.register_end_trial(time_utils.now_timestamp())

    def after_trial(self):
        self.register_value("sound_side", self.side)
        self.register_value("intensity", self.intensity)
        self.register_value("water", 0)

    def close(self):
        """Stops IMU logging and disconnects the OptoGrid."""

        self.og.stop()