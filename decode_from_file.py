import numpy as np
import sounddevice as sd
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from scipy.fft import rfft, rfftfreq
import wave
samplerate = 44100
bit_duration = 0.1
f0 = 1000
f1 = 2000
threshold = 50
samples_per_bit = int(samplerate * bit_duration)

def bits_to_text(bits):
    chars = [bits[i:i+8] for i in range(0, len(bits), 8)]
    try:
        return ''.join(chr(int(b, 2)) for b in chars)
    except:
        return "bit E"

def load_wav(filename):
    with wave.open(filename, 'rb') as wf:
        frames = wf.readframes(wf.getnframes())
        signal = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
        signal /= 32767.0
    return signal

def play_signal(signal):
    sd.play(signal, samplerate)
    sd.wait()

def decode_signal(signal):
    bits = []
    for i in range(0, len(signal) - samples_per_bit + 1, samples_per_bit):
        chunk = signal[i:i+samples_per_bit]
        fft_vals = np.abs(rfft(chunk))
        freqs = rfftfreq(len(chunk), 1 / samplerate)

        idx_f0 = np.argmin(np.abs(freqs - f0))
        idx_f1 = np.argmin(np.abs(freqs - f1))

        mag_f0 = fft_vals[idx_f0]
        mag_f1 = fft_vals[idx_f1]

        if mag_f1 > mag_f0 and mag_f1 > threshold:
            bits.append('1')
        elif mag_f0 > mag_f1 and mag_f0 > threshold:
            bits.append('0')
        else:
            bits.append('?')
    return ''.join(bits)

def open_and_decode():
    filename = filedialog.askopenfilename(title="انتخاب فایل WAV", filetypes=[("WAV files", "*.wav")])
    if not filename:
        return
    signal = load_wav(filename)
    threading.Thread(target=lambda: play_signal(signal), daemon=True).start()

    bits = decode_signal(signal)
    cleaned_bits = ''.join(b for b in bits if b in '01')
    text = bits_to_text(cleaned_bits)
    messagebox.showinfo(" متن رمزگشایی شده", f" متن:\n{text}\n\nبیت‌ها:\n{bits}")
root = tk.Tk()
root.title("🔓 باز کردن فایل WAV و رمزگشایی")

tk.Button(root, text="📂 بازکردن فایل WAV", command=open_and_decode, width=40).pack(pady=20)

root.mainloop()
