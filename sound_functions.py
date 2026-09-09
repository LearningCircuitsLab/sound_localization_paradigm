import numpy as np
from village.settings import settings

"""Sound generation functions for the auditory experiments."""
def white_noise(duration: float, gain: float) -> np.ndarray:
    fs = settings.get("SAMPLERATE")  # Sampling frequency
    n_samples = int(fs * duration)
    noise = np.random.randn(n_samples) * gain
    return noise

# create a function that does white noise starting at a lower gain and ending at a higher gain over the duration of the sound
def white_noise_with_gain_ramp(duration: float, initial_gain: float, ending_gain: float) -> np.ndarray:
    fs = settings.get("SAMPLERATE")  # Sampling frequency
    n_samples = int(fs * duration)
    noise = np.random.randn(n_samples)
    gain_ramp = np.linspace(initial_gain, ending_gain, n_samples)
    return noise * gain_ramp

sound_calibration_functions = [
    white_noise,
]
