import numpy as np
import sounddevice as sd
import tkinter as tk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.fft import rfft, rfftfreq
from scipy.io import wavfile
import threading
import queue
samplerate = 44100
bit_duration = 0.1
f0 = 500
f1 = 800
threshold = 300
samples_per_bit = int(samplerate * bit_duration)

q = queue.Queue()
received_bits = []
is_listening = False
audio_buffer = np.zeros(samples_per_bit)

def decode_chunk(chunk):
    fft_vals = np.abs(rfft(chunk))
    freqs = rfftfreq(len(chunk), 1/samplerate)

    idx_f0 = np.argmin(np.abs(freqs - f0))
    idx_f1 = np.argmin(np.abs(freqs - f1))

    mag_f0 = fft_vals[idx_f0]
    mag_f1 = fft_vals[idx_f1]

    if mag_f1 > mag_f0 and mag_f1 > threshold:
        return '1'
    elif mag_f0 > mag_f1 and mag_f0 > threshold:
        return '0'
    else:
        return None

def bits_to_text(bits):
    chars = [bits[i:i+8] for i in range(0, len(bits), 8)]
    try:
        return ''.join(chr(int(b, 2)) for b in chars)
    except:
        return "[خطا در تبدیل بیت]"

def audio_callback(indata, frames, time_, status):
    if status:
        print("خطا:", status)
    q.put(indata[:, 0].copy())

def listener(text_widget, status_label):
    global received_bits, is_listening, audio_buffer
    buffer = np.array([], dtype=np.float32)

    while is_listening:
        try:
            data = q.get(timeout=1)
        except queue.Empty:
            continue

        buffer = np.concatenate((buffer, data))
        audio_buffer = data

        while len(buffer) >= samples_per_bit:
            chunk = buffer[:samples_per_bit]
            buffer = buffer[samples_per_bit:]
            bit = decode_chunk(chunk)
            if bit is not None:
                received_bits.append(bit)
                if len(received_bits) % 8 == 0:
                    current_text = bits_to_text(''.join(received_bits))
                    text_widget.delete(1.0, tk.END)
                    text_widget.insert(tk.END, current_text)
                    status_label.config(text=f"بیت‌ها: {''.join(received_bits[-8:])}")

def start_listening(text_widget, status_label, start_btn, stop_btn):
    global is_listening, received_bits, stream
    if is_listening:
        return
    received_bits = []
    is_listening = True
    start_btn.config(state=tk.DISABLED)
    stop_btn.config(state=tk.NORMAL)
    status_label.config(text="در حال دریافت...")

    stream = sd.InputStream(samplerate=samplerate, channels=1,
                            blocksize=samples_per_bit,
                            callback=audio_callback)
    stream.start()

    threading.Thread(target=listener, args=(text_widget, status_label), daemon=True).start()

def stop_listening(status_label, start_btn, stop_btn):
    global is_listening, stream
    if not is_listening:
        return
    is_listening = False
    stream.stop()
    stream.close()
    status_label.config(text="توقف دریافت")
    start_btn.config(state=tk.NORMAL)
    stop_btn.config(state=tk.DISABLED)

def update_plot(line, canvas):
    line.set_ydata(audio_buffer)
    canvas.draw()
    if is_listening:
        canvas.get_tk_widget().after(50, update_plot, line, canvas)

def process_wav_file(text_widget, status_label, fig2_ax):
    filepath = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
    if not filepath:
        return

    # try:
    #     rate, data = wavfile.read(filepath)
    #     if len(data.shape) > 1:
    #         data = data[:, 0]  # فقط یک کانال

    #     data = data / np.max(np.abs(data))  # نرمال‌سازی

    #     fig2_ax.clear()
    #     fig2_ax.plot(data, color='purple')
    #     fig2_ax.set_title("نمودار کامل فایل صوتی")
    #     fig2_ax.set_xticks([])
    #     fig2_ax.set_yticks([])
    #     fig2_ax.figure.canvas.draw()

    #     bits = []
    #     i = 0
    #     while i + samples_per_bit <= len(data):
    #         chunk = data[i:i + samples_per_bit]
    #         bit = decode_chunk(chunk)
    #         if bit is not None:
    #             bits.append(bit)
    #         i += samples_per_bit

    #     text = bits_to_text(''.join(bits))
    #     text_widget.delete(1.0, tk.END)
    #     text_widget.insert(tk.END, text)
    #     status_label.config(text=f"تعداد بیت‌ها: {len(bits)}")

    # except Exception as e:
    #     status_label.config(text=f"خطا در پردازش فایل: {e}")

def main():
    global audio_buffer

    root = tk.Tk()
    root.title("رمزگشای زنده")

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    text_widget = ScrolledText(frame, width=50, height=10, font=("Consolas", 13))
    text_widget.pack(pady=5)

    status_label = tk.Label(frame, text="منتظر شروع...", font=("Arial", 11))
    status_label.pack(pady=5)

    btn_frame = tk.Frame(frame)
    btn_frame.pack()

    start_btn = tk.Button(btn_frame, text="🎧 شروع دریافت زنده", width=20,
                          command=lambda: start_listening(text_widget, status_label, start_btn, stop_btn))
    start_btn.pack(side=tk.LEFT, padx=5)

    stop_btn = tk.Button(btn_frame, text="🛑 توقف", width=10, state=tk.DISABLED,
                         command=lambda: stop_listening(status_label, start_btn, stop_btn))
    stop_btn.pack(side=tk.LEFT, padx=5)

    # load_btn = tk.Button(frame, text="📁 بارگذاری فایل WAV و رمزگشایی",
    #                      command=lambda: process_wav_file(text_widget, status_label, fig2_ax))
    # load_btn.pack(pady=5)

    # نمودار زنده
    fig, ax = plt.subplots(figsize=(5, 2))
    x = np.arange(0, samples_per_bit)
    line, = ax.plot(x, np.zeros_like(x))
    ax.set_ylim([-1, 1])
    ax.set_title("موج ورودی زنده")
    ax.set_xticks([])
    ax.set_yticks([])

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.get_tk_widget().pack(pady=10)
    update_plot(line, canvas)

    # # نمودار فایل بارگذاری‌شده
    # fig2, fig2_ax = plt.subplots(figsize=(5, 2))
    # canvas2 = FigureCanvasTkAgg(fig2, master=frame)
    # canvas2.get_tk_widget().pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()
