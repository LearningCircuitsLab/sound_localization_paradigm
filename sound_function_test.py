"""Manual test harness for `white_noise_with_gain_ramp`.

The script first draws simple plots with tkinter, then plays the sound using an
optional audio backend if one is available. If Python audio packages are not
installed, it falls back to standard Linux or Windows playback tools from WSL.
"""

from __future__ import annotations

import importlib
import math
import os
import random
import shutil
import subprocess
import tempfile
import wave
from array import array
from tkinter import BOTH, Canvas, LEFT, RIGHT, Tk, ttk


def white_noise_with_gain_ramp(duration: float, initial_gain: float, ending_gain: float) -> list[float]:
	fs = 192000  # Sampling frequency
	n_samples = int(fs * duration)
	noise = [random.gauss(0.0, 1.0) for _ in range(n_samples)]
	gain_ramp = [
		initial_gain + (ending_gain - initial_gain) * index / max(1, n_samples - 1)
		for index in range(n_samples)
	]
	return [sample * gain for sample, gain in zip(noise, gain_ramp)]

def moving_rms(signal, window_samples: int):
	"""Return a simple moving RMS envelope for plotting."""

	window_samples = max(1, int(window_samples))
	squared = [float(value) ** 2 for value in signal]
	prefix = [0.0]
	for value in squared:
		prefix.append(prefix[-1] + value)

	n_samples = len(squared)
	half_window = window_samples // 2
	envelope = []
	for index in range(n_samples):
		start = max(0, index - half_window)
		end = min(n_samples, start + window_samples)
		if end - start < window_samples:
			start = max(0, end - window_samples)
		mean_square = (prefix[end] - prefix[start]) / max(1, end - start)
		envelope.append(math.sqrt(mean_square))
	return envelope


def draw_series(canvas: Canvas, values, *, color: str, y_min: float, y_max: float) -> None:
	width = int(canvas.cget("width"))
	height = int(canvas.cget("height"))
	padding = 16
	usable_width = max(1, width - 2 * padding)
	usable_height = max(1, height - 2 * padding)

	sample_stride = max(1, len(values) // 2000)
	sampled = list(values[::sample_stride])
	if sampled[-1] != values[-1]:
		sampled = sampled + [values[-1]]

	points: list[float] = []
	for index, value in enumerate(sampled):
		x = padding + (index / max(1, len(sampled) - 1)) * usable_width
		normalized = 0.0 if y_max == y_min else (float(value) - y_min) / (y_max - y_min)
		y = padding + (1.0 - normalized) * usable_height
		points.extend((x, y))

	canvas.create_line(*points, fill=color, width=1)


def build_plot_window(signal, envelope, expected_ramp, duration: float):
	root = Tk()
	root.title("white_noise_with_gain_ramp test")

	title = ttk.Label(
		root,
		text="Plot first, then play the sound",
		font=("TkDefaultFont", 13, "bold"),
		padding=(12, 12),
	)
	title.pack(fill="x")

	waveform_canvas = Canvas(root, width=1200, height=300, background="white")
	waveform_canvas.pack(fill=BOTH, expand=True, padx=12, pady=(0, 8))
	waveform_canvas.create_text(12, 12, anchor="nw", text="Waveform", fill="#333333")
	waveform_canvas.create_line(16, 150, 1184, 150, fill="#d0d0d0")
	draw_series(waveform_canvas, signal, color="#2b6cb0", y_min=-1.0, y_max=1.0)

	ramp_canvas = Canvas(root, width=1200, height=300, background="white")
	ramp_canvas.pack(fill=BOTH, expand=True, padx=12, pady=(0, 12))
	ramp_canvas.create_text(12, 12, anchor="nw", text="Gain ramp and moving RMS", fill="#333333")
	ramp_canvas.create_line(16, 150, 1184, 150, fill="#d0d0d0")

	max_level = max(max(expected_ramp), max(envelope), 1e-9)
	draw_series(ramp_canvas, expected_ramp, color="#c05621", y_min=0.0, y_max=max_level)
	draw_series(ramp_canvas, envelope, color="#2f855a", y_min=0.0, y_max=max_level)

	button_row = ttk.Frame(root, padding=(12, 0, 12, 12))
	button_row.pack(fill="x")

	status = ttk.Label(button_row, text="Close this window or press Play to hear the sound.")
	status.pack(side=LEFT)

	def close_and_play() -> None:
		root.destroy()

	ttk.Button(button_row, text="Play", command=close_and_play).pack(side=RIGHT)
	ttk.Button(button_row, text="Close", command=root.destroy).pack(side=RIGHT, padx=(0, 8))

	return root


def play_audio(signal, sample_rate: int) -> None:
	"""Play audio using a general-purpose playback library if installed."""

	peak = max((abs(float(value)) for value in signal), default=0.0)
	if peak > 0:
		audio = [float(value) / peak for value in signal]
	else:
		audio = [float(value) for value in signal]

	try:
		sounddevice = importlib.import_module("sounddevice")
	except ImportError:
		sounddevice = None

	if sounddevice is not None:
		sounddevice.play(audio, samplerate=sample_rate)
		sounddevice.wait()
		return

	try:
		simpleaudio = importlib.import_module("simpleaudio")
	except ImportError:
		simpleaudio = None

	if simpleaudio is not None:
		pcm = array(
			"h",
			(
				int(max(-1.0, min(1.0, value)) * 32767)
				for value in audio
			),
		)
		simpleaudio.play_buffer(pcm, 1, 2, sample_rate).wait_done()
		return

	with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
		wav_path = temp_file.name

	pcm = array(
		"h",
		(
			int(max(-1.0, min(1.0, value)) * 32767)
			for value in audio
		),
	)

	try:
		with wave.open(wav_path, "wb") as wav_file:
			wav_file.setnchannels(1)
			wav_file.setsampwidth(2)
			wav_file.setframerate(sample_rate)
			wav_file.writeframes(pcm.tobytes())

		for command in ("powershell.exe", "pwsh", "aplay", "paplay", "ffplay"):
			player = shutil.which(command)
			if player is None:
				continue

			if command in {"powershell.exe", "pwsh"}:
				escaped_path = wav_path.replace("'", "''")
				player_args = [
					player,
					"-NoProfile",
					"-Command",
					f"(New-Object Media.SoundPlayer '{escaped_path}').PlaySync()",
				]
			elif command == "ffplay":
				player_args = [player, "-nodisp", "-autoexit", wav_path]
			else:
				player_args = [player, wav_path]

			subprocess.run(player_args, check=False)
			return
	finally:
		try:
			os.unlink(wav_path)
		except FileNotFoundError:
			pass

	raise RuntimeError(
		"Install 'sounddevice' or 'simpleaudio', or make a system player "
		"available in WSL such as powershell.exe, pwsh, aplay, paplay, or ffplay."
	)


def main() -> None:
	duration = 0.25
	initial_gain = 0.1
	ending_gain = 0.5
	sample_rate = 192000

	signal = white_noise_with_gain_ramp(
		duration=duration,
		initial_gain=initial_gain,
		ending_gain=ending_gain,
	)

	expected_ramp = [
		initial_gain + (ending_gain - initial_gain) * index / max(1, len(signal) - 1)
		for index in range(len(signal))
	]
	envelope = moving_rms(signal, max(1, int(0.01 * sample_rate)))

	root = build_plot_window(signal, envelope, expected_ramp, duration)
	root.mainloop()

	play_audio(signal, sample_rate)


if __name__ == "__main__":
	main()

