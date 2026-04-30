import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import struct
import os

PM_A = 16807
PM_M = 2147483647
BLOCK_SIZE = 5

S_TABLE = [
    0xa3, 0xd7, 0x09, 0x83, 0xf8, 0x48, 0xf6, 0xf4, 0xb3, 0x21, 0x15, 0x78, 0x99, 0xb1, 0xaf, 0xf9,
    0xe7, 0x2d, 0x4d, 0x8a, 0xce, 0x4c, 0xca, 0x2e, 0x52, 0x95, 0xd9, 0x1e, 0x4e, 0x38, 0x44, 0x28,
    0x0a, 0xdf, 0x02, 0xa0, 0x17, 0xf1, 0x60, 0x68, 0x12, 0xb7, 0x7a, 0xc3, 0xe9, 0xfa, 0x3d, 0x53,
    0x96, 0x84, 0x6b, 0xba, 0xf2, 0x63, 0x9a, 0x19, 0x7c, 0xae, 0xe5, 0xf5, 0xf7, 0x16, 0x6a, 0xa2,
    0x39, 0xb6, 0x7b, 0x0f, 0xc1, 0x93, 0x81, 0x1b, 0xee, 0xb4, 0x1a, 0xea, 0xd0, 0x91, 0x2f, 0xb8,
    0x55, 0xb9, 0xda, 0x85, 0x3f, 0x41, 0xbf, 0xe0, 0x5a, 0x58, 0x80, 0x5f, 0x66, 0x0b, 0xd8, 0x90,
    0x35, 0xd5, 0xc0, 0xa7, 0x33, 0x06, 0x65, 0x69, 0x45, 0x00, 0x94, 0x56, 0x6d, 0x98, 0x9b, 0x76,
    0x97, 0xfc, 0xb2, 0xc2, 0xb0, 0xfe, 0xdb, 0x20, 0xe1, 0xeb, 0xd6, 0xe4, 0xdd, 0x47, 0x4a, 0x1d,
    0x42, 0xed, 0x9e, 0x6e, 0x49, 0x3c, 0xcd, 0x43, 0x27, 0xd2, 0x07, 0xd4, 0xde, 0xc7, 0x67, 0x18,
    0x89, 0xcb, 0x30, 0x1f, 0x8d, 0xc6, 0x8f, 0xaa, 0xc8, 0x74, 0xdc, 0xc9, 0x5d, 0x5c, 0x31, 0xa4,
    0x70, 0x88, 0x61, 0x2c, 0x9f, 0x0d, 0x2b, 0x87, 0x50, 0x82, 0x54, 0x64, 0x26, 0x7d, 0x03, 0x40,
    0x34, 0x4b, 0x1c, 0x73, 0xd1, 0xc4, 0xfd, 0x3b, 0xcc, 0xfb, 0x7f, 0xab, 0xe6, 0x3e, 0x5b, 0xa5,
    0xad, 0x04, 0x23, 0x9c, 0x14, 0x51, 0x22, 0xf0, 0x29, 0x79, 0x71, 0x7e, 0xff, 0x8c, 0x0e, 0xe2,
    0x0c, 0xef, 0xbc, 0x72, 0x75, 0x6f, 0x37, 0xa1, 0xec, 0xd3, 0x8e, 0x62, 0x8b, 0x86, 0x10, 0xe8,
    0x08, 0x77, 0x11, 0xbe, 0x92, 0x4f, 0x24, 0xc5, 0x32, 0x36, 0x9d, 0xcf, 0xf3, 0xa6, 0xbb, 0xac,
    0x5e, 0x6c, 0xa9, 0x13, 0x57, 0x25, 0xb5, 0xe3, 0xbd, 0xa8, 0x3a, 0x01, 0x05, 0x59, 0x2a, 0x46
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
        sh1, sh2 = hash1, hash2
        hash1 = (((sh1 >> 16) & 0xffff) | ((sh2 & 0xffff) << 16)) & 0xFFFFFFFF
        hash2 = (((sh2 >> 16) & 0xffff) | ((sh1 & 0xffff) << 16)) & 0xFFFFFFFF
    return (hash1 ^ hash2) & 0xFFFFFFFF


def password_to_seed(password: str) -> int:
    h = mahash8(password.encode("utf-8"))
    seed = h % (PM_M - 1)
    return seed if seed != 0 else 1


def pm_next(x: int) -> int:
    return (PM_A * x) % PM_M


def det(mat, n):
    if n == 1:
        return mat[0][0]
    if n == 2:
        return mat[0][0] * mat[1][1] - mat[0][1] * mat[1][0]
    result = 0
    for c in range(n):
        sub = [[mat[r][cc] for cc in range(n) if cc != c] for r in range(1, n)]
        result += ((-1) ** c) * mat[0][c] * det(sub, n - 1)
    return result


def generate_matrix(seed: int, size: int):
    x = seed
    while True:
        mat = []
        for _ in range(size):
            row = []
            for _ in range(size):
                x = pm_next(x)
                row.append((x % 251) + 1)
            mat.append(row)
        d = det(mat, size)
        if d != 0 and abs(d) < 2 ** 31:
            return mat, x
        x = pm_next(x)


def cofactor_matrix(mat, n):
    cof = []
    for r in range(n):
        row = []
        for c in range(n):
            sub = [[mat[rr][cc] for cc in range(n) if cc != c] for rr in range(n) if rr != r]
            row.append(((-1) ** (r + c)) * det(sub, n - 1))
        cof.append(row)
    return cof


def transpose_mat(mat, n):
    return [[mat[c][r] for c in range(n)] for r in range(n)]


def mat_vec_mul(mat, vec, n):
    return [sum(mat[r][c] * vec[c] for c in range(n)) for r in range(n)]


def decrypt_block_mat(adj_t, d, vec, n):
    return [round(sum(adj_t[r][c] * vec[c] for c in range(n)) / d) for r in range(n)]


def xor_blocks(a: list, b: list) -> list:
    return [x ^ y for x, y in zip(a, b)]


def pad_data(data: bytes, block_size: int) -> bytes:
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)


def unpad_data(data: bytes, block_size: int) -> bytes:
    if not data:
        raise ValueError("Пустые данные")
    pad_len = data[-1]
    if pad_len == 0 or pad_len > block_size:
        raise ValueError("Неверный padding — возможно, неправильный пароль")
    return data[:-pad_len]


def make_iv(seed: int, block_size: int) -> list:
    x = seed
    iv = []
    for _ in range(block_size):
        x = pm_next(x)
        iv.append(x % 256)
    return iv


def encrypt_cbc(data: bytes, seed: int, progress_callback=None) -> bytes:
    n = BLOCK_SIZE
    padded = pad_data(data, n)
    num_blocks = len(padded) // n
    iv = make_iv(seed, n)
    prev = iv
    x = seed
    result = bytearray(bytes(iv))
    for i in range(num_blocks):
        block = list(padded[i * n:(i + 1) * n])
        xored = xor_blocks(block, prev)
        mat, x = generate_matrix(x, n)
        enc = mat_vec_mul(mat, xored, n)
        for v in enc:
            result.extend(struct.pack(">i", v))
        prev = [v % 256 for v in enc]
        if progress_callback:
            progress_callback(i + 1, num_blocks)
    return bytes(result)


def decrypt_cbc(data: bytes, seed: int, progress_callback=None) -> bytes:
    n = BLOCK_SIZE
    enc_block_size = n * 4
    if len(data) < n:
        raise ValueError("Файл слишком короткий")
    iv = list(data[:n])
    ciphertext = data[n:]
    if len(ciphertext) % enc_block_size != 0:
        raise ValueError("Длина шифртекста повреждена — возможно, неправильный пароль")
    num_blocks = len(ciphertext) // enc_block_size
    prev = iv
    x = seed
    result = bytearray()
    matrices = []
    tmp_x = x
    for _ in range(num_blocks):
        mat, tmp_x = generate_matrix(tmp_x, n)
        matrices.append(mat)
    for i in range(num_blocks):
        raw = ciphertext[i * enc_block_size:(i + 1) * enc_block_size]
        enc = [struct.unpack(">i", raw[j * 4:(j + 1) * 4])[0] for j in range(n)]
        mat = matrices[i]
        d = det(mat, n)
        cof = cofactor_matrix(mat, n)
        adj_t = transpose_mat(cof, n)
        dec = decrypt_block_mat(adj_t, d, enc, n)
        plain = xor_blocks(dec, prev)
        result.extend(bytes([v % 256 for v in plain]))
        prev = [v % 256 for v in enc]
        if progress_callback:
            progress_callback(i + 1, num_blocks)
    return unpad_data(bytes(result), n)


def update_hash_display(*args):
    pw = password_var.get()
    if pw:
        h = mahash8(pw.encode("utf-8"))
        hash_label.config(text=f"MaHash8: 0x{h:08X}  (seed: {password_to_seed(pw)})")
    else:
        hash_label.config(text="MaHash8: —")


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


def do_cipher(mode: str):
    input_path = input_path_var.get().strip()
    output_path = output_path_var.get().strip()
    password = password_var.get()

    if not input_path:
        messagebox.showerror("Ошибка", "Укажите входной файл.")
        return
    if not output_path:
        messagebox.showerror("Ошибка", "Укажите выходной файл.")
        return
    if not password:
        messagebox.showerror("Ошибка", "Введите пароль.")
        return

    seed = password_to_seed(password)

    encrypt_btn.config(state=tk.DISABLED)
    decrypt_btn.config(state=tk.DISABLED)
    progress_var.set(0)
    log_text.config(state=tk.NORMAL)
    log_text.delete("1.0", tk.END)

    verb = "Шифрование" if mode == "encrypt" else "Дешифрование"
    log_text.insert(tk.END, f"{verb} начато...\n")
    log_text.insert(tk.END, f"Алгоритм: матричное шифрование, блок {BLOCK_SIZE} байт, режим CBC\n")
    log_text.insert(tk.END, f"Матрица: {BLOCK_SIZE}x{BLOCK_SIZE}, элементы из генератора Парка-Миллера\n")
    log_text.insert(tk.END, f"Хеш пароля (MaHash8): 0x{mahash8(password.encode()):08X}\n")
    log_text.insert(tk.END, f"Seed: {seed}\n")
    log_text.insert(tk.END, f"Входной файл: {os.path.basename(input_path)}\n\n")
    log_text.config(state=tk.DISABLED)

    def run():
        try:
            with open(input_path, "rb") as f:
                data = f.read()

            file_size = len(data)
            status_label.config(text=f"Статус: {verb}... (0 блоков)")

            def progress_cb(done, total):
                pct = int(done / total * 100) if total else 100
                progress_var.set(pct)
                status_label.config(text=f"Статус: {verb}... ({done} / {total} блоков)")
                root.update_idletasks()

            if mode == "encrypt":
                result = encrypt_cbc(data, seed, progress_cb)
            else:
                result = decrypt_cbc(data, seed, progress_cb)

            with open(output_path, "wb") as f:
                f.write(result)

            progress_var.set(100)
            log_text.config(state=tk.NORMAL)
            log_text.insert(tk.END, f"{verb} завершено.\n")
            log_text.insert(tk.END, f"Входной размер: {file_size} байт\n")
            log_text.insert(tk.END, f"Выходной размер: {len(result)} байт\n")
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


root = tk.Tk()
root.title("Лаб 4 — Матричный шифр (CBC) + MaHash8")
root.geometry("820x620")
root.minsize(700, 500)

info_frame = tk.Frame(root, padx=10, pady=8)
info_frame.pack(fill=tk.X)

tk.Label(info_frame,
         text=f"[ Матричное шифрование {BLOCK_SIZE}x{BLOCK_SIZE}, блок {BLOCK_SIZE} байт, режим CBC, матрица из генератора Парка-Миллера ]",
         fg="gray").pack(side=tk.LEFT)

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
tk.Entry(file_frame, textvariable=output_path_var, width=50).grid(row=1, column=1, sticky="ew", padx=(0, 4),
                                                                  pady=(4, 0))
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