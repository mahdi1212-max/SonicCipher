import numpy as np
import sounddevice as sd
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
import threading
from scipy.fft import rfft, rfftfreq
import wave
samplerate = 44100
bit_duration = 0.1
f0 = 1000
f1 = 2000
threshold = 50 
samples_per_bit = int(samplerate * bit_duration)
def text_to_bits(text):
    return ''.join(f'{ord(c):08b}' for c in text)

def bits_to_text(bits):
    chars = [bits[i:i+8] for i in range(0, len(bits), 8)]
    try:
        return ''.join(chr(int(b, 2)) for b in chars)
    except:
        return "[خطا در تبدیل بیت]"
def generate_tone(bit):
    t = np.linspace(0, bit_duration, samples_per_bit, False)
    freq = f1 if bit == '1' else f0
    tone = 0.5 * np.sin(2 * np.pi * freq * t)
    return tone
def encode_text(text):
    bits = text_to_bits(text)
    signal = np.concatenate([generate_tone(b) for b in bits])
    return signal

def save_wav(filename, signal):
    signal_int16 = np.int16(signal / np.max(np.abs(signal)) * 32767)
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(signal_int16.tobytes())

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

def send_text():
    text = simpledialog.askstring("ارسال پیام", "متن خود را وارد کنید:")
    if not text:
        return
    signal = encode_text(text)
    threading.Thread(target=lambda: play_signal(signal), daemon=True).start()

    save_path = filedialog.asksaveasfilename(title="ذخیره فایل WAV", defaultextension=".wav",
                                             filetypes=[("WAV files", "*.wav")])
    if save_path:
        save_wav(save_path, signal)
        messagebox.showinfo("ذخیره شد", f"فایل ذخیره شد:\n{save_path}")

def start_decoding_from_file():
    filename = filedialog.askopenfilename(title="بازکردن فایل WAV", filetypes=[("WAV files", "*.wav")])
    if not filename:
        return
    signal = load_wav(filename)
    threading.Thread(target=lambda: play_signal(signal), daemon=True).start()

    bits = decode_signal(signal)
    cleaned_bits = ''.join(b for b in bits if b in '01')
    text = bits_to_text(cleaned_bits)
    messagebox.showinfo("متن رمزگشایی شده", f"📝 متن:\n{text}\n\nبیت‌ها:\n{bits}")

# GUI
root = tk.Tk()
root.title("🎧 رمزگذار و رمزگشای صوتی")

tk.Button(root, text="📤 ارسال پیام (تولید و ذخیره WAV)", command=send_text, width=40).pack(pady=10)
tk.Button(root, text="📥 بازکردن فایل WAV و رمزگشایی", command=start_decoding_from_file, width=40).pack(pady=10)

root.mainloop()
