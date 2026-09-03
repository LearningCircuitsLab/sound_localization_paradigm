import numpy as np
from village.settings import settings

"""Sound generation functions for the auditory experiments."""
def white_noise(duration: float, amplitude: float) -> np.ndarray:
    fs = settings.get("SAMPLERATE")  # Sampling frequency
    n_samples = int(fs * duration)
    noise = np.random.randn(n_samples) * amplitude
    return noise


sound_calibration_functions = [
    white_noise,
]
