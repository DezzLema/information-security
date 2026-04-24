import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import math
import threading
import os


PM_A = 16807
PM_M = 2147483647

S_TABLE = [
    0xa3,0xd7,0x09,0x83,0xf8,0x48,0xf6,0xf4,0xb3,0x21,0x15,0x78,0x99,0xb1,0xaf,0xf9,
    0xe7,0x2d,0x4d,0x8a,0xce,0x4c,0xca,0x2e,0x52,0x95,0xd9,0x1e,0x4e,0x38,0x44,0x28,
    0x0a,0xdf,0x02,0xa0,0x17,0xf1,0x60,0x68,0x12,0xb7,0x7a,0xc3,0xe9,0xfa,0x3d,0x53,
    0x96,0x84,0x6b,0xba,0xf2,0x63,0x9a,0x19,0x7c,0xae,0xe5,0xf5,0xf7,0x16,0x6a,0xa2,
    0x39,0xb6,0x7b,0x0f,0xc1,0x93,0x81,0x1b,0xee,0xb4,0x1a,0xea,0xd0,0x91,0x2f,0xb8,
    0x55,0xb9,0xda,0x85,0x3f,0x41,0xbf,0xe0,0x5a,0x58,0x80,0x5f,0x66,0x0b,0xd8,0x90,
    0x35,0xd5,0xc0,0xa7,0x33,0x06,0x65,0x69,0x45,0x00,0x94,0x56,0x6d,0x98,0x9b,0x76,
    0x97,0xfc,0xb2,0xc2,0xb0,0xfe,0xdb,0x20,0xe1,0xeb,0xd6,0xe4,0xdd,0x47,0x4a,0x1d,
    0x42,0xed,0x9e,0x6e,0x49,0x3c,0xcd,0x43,0x27,0xd2,0x07,0xd4,0xde,0xc7,0x67,0x18,
    0x89,0xcb,0x30,0x1f,0x8d,0xc6,0x8f,0xaa,0xc8,0x74,0xdc,0xc9,0x5d,0x5c,0x31,0xa4,
    0x70,0x88,0x61,0x2c,0x9f,0x0d,0x2b,0x87,0x50,0x82,0x54,0x64,0x26,0x7d,0x03,0x40,
    0x34,0x4b,0x1c,0x73,0xd1,0xc4,0xfd,0x3b,0xcc,0xfb,0x7f,0xab,0xe6,0x3e,0x5b,0xa5,
    0xad,0x04,0x23,0x9c,0x14,0x51,0x22,0xf0,0x29,0x79,0x71,0x7e,0xff,0x8c,0x0e,0xe2,
    0x0c,0xef,0xbc,0x72,0x75,0x6f,0x37,0xa1,0xec,0xd3,0x8e,0x62,0x8b,0x86,0x10,0xe8,
    0x08,0x77,0x11,0xbe,0x92,0x4f,0x24,0xc5,0x32,0x36,0x9d,0xcf,0xf3,0xa6,0xbb,0xac,
    0x5e,0x6c,0xa9,0x13,0x57,0x25,0xb5,0xe3,0xbd,0xa8,0x3a,0x01,0x05,0x59,0x2a,0x46
]


def lrot14(x):
    x &= 0xFFFFFFFF
    return ((x << 14) | (x >> 18)) & 0xFFFFFFFF

def rrot14(x):
    x &= 0xFFFFFFFF
    return ((x << 18) | (x >> 14)) & 0xFFFFFFFF

def mahash8(data: bytes) -> int:
    length = len(data)
    hash1 = length & 0xFFFFFFFF
    hash2 = length & 0xFFFFFFFF

    for i, byte in enumerate(data):
        idx = (byte + i) & 255
        val = S_TABLE[idx]

        hash1 = (hash1 + val) & 0xFFFFFFFF
        hash1 = lrot14((hash1 + ((hash1 << 6) ^ (hash1 >> 11))) & 0xFFFFFFFF)

        hash2 = (hash2 + val) & 0xFFFFFFFF
        hash2 = rrot14((hash2 + ((hash2 << 6) ^ (hash2 >> 11))) & 0xFFFFFFFF)

        sh1 = hash1
        sh2 = hash2
        hash1 = (((sh1 >> 16) & 0xffff) | ((sh2 & 0xffff) << 16)) & 0xFFFFFFFF
        hash2 = (((sh2 >> 16) & 0xffff) | ((sh1 & 0xffff) << 16)) & 0xFFFFFFFF

    return (hash1 ^ hash2) & 0xFFFFFFFF


def park_miller_generator(seed: int, length: int) -> bytes:
    result = bytearray()
    x = seed
    byte_val = 0
    bit_count = 0
    needed = length

    while needed > 0:
        x = (PM_A * x) % PM_M
        byte_val = (byte_val << 1) | (x & 1)
        bit_count += 1
        if bit_count == 8:
            result.append(byte_val)
            byte_val = 0
            bit_count = 0
            needed -= 1

    return bytes(result)


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(math.isqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def bbs_generator(p: int, q: int, seed: int, length: int) -> bytes:
    if not is_prime(p):
        raise ValueError(f"p = {p} не является простым числом")
    if not is_prime(q):
        raise ValueError(f"q = {q} не является простым числом")
    if p % 4 != 3:
        raise ValueError(f"p = {p} не удовлетворяет условию p ≡ 3 (mod 4)")
    if q % 4 != 3:
        raise ValueError(f"q = {q} не удовлетворяет условию q ≡ 3 (mod 4)")
    if p == q:
        raise ValueError("p и q должны быть различными числами")

    N = p * q
    if gcd(seed, N) != 1:
        raise ValueError(f"seed не взаимно прост с N = {N}")

    result = bytearray()
    u = (seed * seed) % N
    byte_val = 0
    bit_count = 0
    needed = length

    while needed > 0:
        u = (u * u) % N
        byte_val = (byte_val << 1) | (u % 2)
        bit_count += 1
        if bit_count == 8:
            result.append(byte_val)
            byte_val = 0
            bit_count = 0
            needed -= 1

    return bytes(result)


def stream_cipher(data: bytes, key_seed: int, generator: str,
                  bbs_p: int = 383, bbs_q: int = 503,
                  progress_callback=None) -> bytes:
    chunk_size = 65536
    total = len(data)
    result = bytearray()

    offset = 0
    processed = 0

    if generator == "park_miller":
        x = key_seed
        while offset < total:
            chunk = data[offset:offset + chunk_size]
            keystream = bytearray()
            for _ in range(len(chunk)):
                x = (PM_A * x) % PM_M
                byte_val = 0
                for _ in range(8):
                    x = (PM_A * x) % PM_M
                    byte_val = (byte_val << 1) | (x & 1)
                keystream.append(byte_val)
            for b, k in zip(chunk, keystream):
                result.append(b ^ k)
            offset += chunk_size
            processed += len(chunk)
            if progress_callback:
                progress_callback(processed, total)
    else:
        N = bbs_p * bbs_q
        u = (key_seed * key_seed) % N
        while offset < total:
            chunk = data[offset:offset + chunk_size]
            keystream = bytearray()
            for _ in range(len(chunk)):
                byte_val = 0
                for _ in range(8):
                    u = (u * u) % N
                    byte_val = (byte_val << 1) | (u % 2)
                keystream.append(byte_val)
            for b, k in zip(chunk, keystream):
                result.append(b ^ k)
            offset += chunk_size
            processed += len(chunk)
            if progress_callback:
                progress_callback(processed, total)

    return bytes(result)


def password_to_seed(password: str) -> int:
    data = password.encode("utf-8")
    h = mahash8(data)
    seed = h % (PM_M - 1)
    if seed == 0:
        seed = 1
    return seed


def on_generator_switch():
    if generator_var.get() == "park_miller":
        bbs_frame.pack_forget()
        pm_frame.pack(fill=tk.X, pady=2)
    else:
        pm_frame.pack_forget()
        bbs_frame.pack(fill=tk.X, pady=2)


def update_hash_display(*args):
    pw = password_entry.get()
    if pw:
        h = mahash8(pw.encode("utf-8"))
        hash_label.config(text=f"MaHash8: 0x{h:08X}  (seed: {password_to_seed(pw)})")
    else:
        hash_label.config(text="MaHash8: —")


def do_cipher(mode: str):
    input_path = input_path_var.get().strip()
    output_path = output_path_var.get().strip()
    password = password_entry.get()

    if not input_path:
        messagebox.showerror("Ошибка", "Укажите входной файл.")
        return
    if not output_path:
        messagebox.showerror("Ошибка", "Укажите выходной файл.")
        return
    if not password:
        messagebox.showerror("Ошибка", "Введите пароль.")
        return

    gen = generator_var.get()
    seed = password_to_seed(password)

    bbs_p_val = bbs_q_val = None
    if gen == "bbs":
        try:
            bbs_p_val = int(bbs_p_entry.get())
            bbs_q_val = int(bbs_q_entry.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Параметры p и q должны быть целыми числами.")
            return

    encrypt_btn.config(state=tk.DISABLED)
    decrypt_btn.config(state=tk.DISABLED)
    progress_var.set(0)
    log_text.config(state=tk.NORMAL)
    log_text.delete("1.0", tk.END)

    verb = "Шифрование" if mode == "encrypt" else "Дешифрование"
    log_text.insert(tk.END, f"{verb} начато...\n")
    log_text.insert(tk.END, f"Генератор: {'Парка-Миллера' if gen == 'park_miller' else 'BBS'}\n")
    log_text.insert(tk.END, f"Хеш пароля (MaHash8): 0x{mahash8(password.encode()):08X}\n")
    log_text.insert(tk.END, f"Seed генератора: {seed}\n")
    log_text.insert(tk.END, f"Входной файл: {os.path.basename(input_path)}\n\n")
    log_text.config(state=tk.DISABLED)

    def run():
        try:
            with open(input_path, "rb") as f:
                data = f.read()

            file_size = len(data)
            status_label.config(text=f"Статус: {verb}... (0 / {file_size} байт)")

            def progress_cb(done, total):
                pct = int(done / total * 100) if total else 100
                progress_var.set(pct)
                status_label.config(text=f"Статус: {verb}... ({done} / {total} байт)")
                root.update_idletasks()

            result = stream_cipher(data, seed, gen, bbs_p_val, bbs_q_val, progress_cb)

            with open(output_path, "wb") as f:
                f.write(result)

            progress_var.set(100)
            log_text.config(state=tk.NORMAL)
            log_text.insert(tk.END, f"{verb} завершено.\n")
            log_text.insert(tk.END, f"Обработано байт: {file_size}\n")
            log_text.insert(tk.END, f"Результат сохранён: {os.path.basename(output_path)}\n")
            log_text.config(state=tk.DISABLED)
            status_label.config(text=f"Статус: Готово — {file_size} байт обработано")

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            status_label.config(text="Статус: Ошибка")
            log_text.config(state=tk.NORMAL)
            log_text.insert(tk.END, f"Ошибка: {e}\n")
            log_text.config(state=tk.DISABLED)
        finally:
            encrypt_btn.config(state=tk.NORMAL)
            decrypt_btn.config(state=tk.NORMAL)

    t = threading.Thread(target=run)
    t.daemon = True
    t.start()


def browse_input():
    path = filedialog.askopenfilename(title="Выберите входной файл",
                                      filetypes=[("Все файлы", "*.*")])
    if path:
        input_path_var.set(path)
        if not output_path_var.get():
            base, ext = os.path.splitext(path)
            output_path_var.set(base + "_out" + ext)


def browse_output():
    path = filedialog.asksaveasfilename(title="Выберите выходной файл",
                                        filetypes=[("Все файлы", "*.*")])
    if path:
        output_path_var.set(path)


root = tk.Tk()
root.title("Лаб 3 — Потоковый шифр + MaHash8")
root.geometry("820x620")
root.minsize(700, 500)

top_frame = tk.Frame(root, padx=10, pady=8)
top_frame.pack(fill=tk.X)

tk.Label(top_frame, text="Генератор:").pack(side=tk.LEFT)
generator_var = tk.StringVar(value="park_miller")
tk.Radiobutton(top_frame, text="Парка-Миллера",
               variable=generator_var, value="park_miller",
               command=on_generator_switch).pack(side=tk.LEFT, padx=(4, 8))
tk.Radiobutton(top_frame, text="BBS",
               variable=generator_var, value="bbs",
               command=on_generator_switch).pack(side=tk.LEFT, padx=(0, 16))

pm_frame = tk.Frame(root, padx=10)
tk.Label(pm_frame, text="[ a = 16807 = 7⁵,  m = 2147483647 = 2³¹ − 1 ]",
         fg="gray").pack(side=tk.LEFT)

bbs_frame = tk.Frame(root, padx=10)
tk.Label(bbs_frame, text="p (простое, p≡3 mod 4):").grid(row=0, column=0, sticky="e", padx=(0, 4))
bbs_p_entry = tk.Entry(bbs_frame, width=10)
bbs_p_entry.grid(row=0, column=1, sticky="w", padx=(0, 14))
bbs_p_entry.insert(0, "383")
tk.Label(bbs_frame, text="q (простое, q≡3 mod 4):").grid(row=0, column=2, sticky="e", padx=(0, 4))
bbs_q_entry = tk.Entry(bbs_frame, width=10)
bbs_q_entry.grid(row=0, column=3, sticky="w")
bbs_q_entry.insert(0, "503")
tk.Label(bbs_frame, text="[ N = p·q,  uᵢ = uᵢ₋₁² mod N,  xᵢ = uᵢ mod 2 ]",
         fg="gray").grid(row=1, column=0, columnspan=4, sticky="w", pady=(2, 0))

pm_frame.pack(fill=tk.X, pady=2)

pw_frame = tk.Frame(root, padx=10, pady=6)
pw_frame.pack(fill=tk.X)

tk.Label(pw_frame, text="Пароль:").pack(side=tk.LEFT)
password_var = tk.StringVar()
password_entry = tk.Entry(pw_frame, textvariable=password_var, width=28, show="*")
password_entry.pack(side=tk.LEFT, padx=(4, 10))

show_pw_var = tk.BooleanVar(value=False)
def toggle_pw():
    password_entry.config(show="" if show_pw_var.get() else "*")
tk.Checkbutton(pw_frame, text="Показать", variable=show_pw_var,
               command=toggle_pw).pack(side=tk.LEFT)

hash_label = tk.Label(pw_frame, text="MaHash8: —", fg="gray", font=("Courier", 9))
hash_label.pack(side=tk.LEFT, padx=(16, 0))

password_var.trace_add("write", update_hash_display)

file_frame = tk.Frame(root, padx=10, pady=4)
file_frame.pack(fill=tk.X)

input_path_var = tk.StringVar()
output_path_var = tk.StringVar()

tk.Label(file_frame, text="Входной файл:").grid(row=0, column=0, sticky="e", padx=(0, 4))
tk.Entry(file_frame, textvariable=input_path_var, width=50).grid(row=0, column=1, sticky="ew", padx=(0, 4))
tk.Button(file_frame, text="Обзор…", command=browse_input).grid(row=0, column=2)

tk.Label(file_frame, text="Выходной файл:").grid(row=1, column=0, sticky="e", padx=(0, 4), pady=(4, 0))
tk.Entry(file_frame, textvariable=output_path_var, width=50).grid(row=1, column=1, sticky="ew", padx=(0, 4), pady=(4, 0))
tk.Button(file_frame, text="Обзор…", command=browse_output).grid(row=1, column=2, pady=(4, 0))

file_frame.columnconfigure(1, weight=1)

action_frame = tk.Frame(root, padx=10, pady=6)
action_frame.pack(fill=tk.X)

encrypt_btn = tk.Button(action_frame, text="Зашифровать",
                        command=lambda: do_cipher("encrypt"),
                        font=("TkDefaultFont", 10), padx=12)
encrypt_btn.pack(side=tk.LEFT, padx=(0, 8))

decrypt_btn = tk.Button(action_frame, text="Дешифровать",
                        command=lambda: do_cipher("decrypt"),
                        font=("TkDefaultFont", 10), padx=12)
decrypt_btn.pack(side=tk.LEFT)

progress_var = tk.IntVar(value=0)
progress_bar = tk.Canvas(action_frame, height=16, bg="#e0e0e0", relief=tk.SUNKEN, bd=1)
progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(16, 0))

def draw_progress(*args):
    progress_bar.delete("all")
    w = progress_bar.winfo_width()
    h = progress_bar.winfo_height()
    pct = progress_var.get()
    fill_w = int(w * pct / 100)
    if fill_w > 0:
        progress_bar.create_rectangle(0, 0, fill_w, h, fill="#4a90d9", outline="")
    if pct > 0:
        progress_bar.create_text(w // 2, h // 2, text=f"{pct}%", font=("TkDefaultFont", 8))

progress_var.trace_add("write", draw_progress)
progress_bar.bind("<Configure>", draw_progress)

log_frame = tk.Frame(root, padx=10, pady=4)
log_frame.pack(fill=tk.BOTH, expand=True)

tk.Label(log_frame, text="Журнал:").pack(anchor=tk.W)
log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED,
                                     bg="#f0f0f0", font=("Courier", 9), height=10)
log_text.pack(fill=tk.BOTH, expand=True)

bottom_frame = tk.Frame(root, relief=tk.SUNKEN, bd=1)
bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
status_label = tk.Label(bottom_frame, text="Статус: Готово", anchor=tk.W, padx=10)
status_label.pack(fill=tk.X)

if __name__ == "__main__":
    root.mainloop()
