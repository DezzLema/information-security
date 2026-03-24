import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import math
import time
import threading



THRESHOLD = 1.82138636



# генератор парка-миллера
PM_A = 16807          # Множитель a = 7^5
PM_M = 2147483647     # Модуль m = 2^31 - 1


def park_miller_generator(seed: int, length: int) -> str:
    if not (1 <= seed <= PM_M - 1):
        raise ValueError(f"Seed должен быть в диапазоне [1, {PM_M - 1}]")

    bits = []
    x = seed
    for _ in range(length):
        x = (PM_A * x) % PM_M
        bits.append(str(x & 1))
    return ''.join(bits)


# bbs
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


def bbs_generator(p: int, q: int, seed: int, length: int) -> str:
    if not is_prime(p):
        raise ValueError(f"p = {p} не является простым числом")
    if not is_prime(q):
        raise ValueError(f"q = {q} не является простым числом")
    if p % 4 != 3:
        raise ValueError(f"p = {p} не удовлетворяет условию p = 3 (mod 4)")
    if q % 4 != 3:
        raise ValueError(f"q = {q} не удовлетворяет условию q = 3 (mod 4)")
    if p == q:
        raise ValueError("p и q должны быть различными числами")

    N = p * q

    if gcd(seed, N) != 1:
        raise ValueError(f"seed должен быть взаимно прост с N = p*q = {N}")
    if not (1 <= seed <= N - 1):
        raise ValueError(f"seed должен быть в диапазоне [1, {N - 1}]")

    bits = []
    u = (seed * seed) % N

    for _ in range(length):
        u = (u * u) % N
        bits.append(str(u % 2))

    return ''.join(bits)

def frequency_test(bit_sequence):
    n = len(bit_sequence)
    if n == 0:
        return False, 0, "Последовательность пуста"

    X = [2 * int(bit) - 1 for bit in bit_sequence]
    Sn = sum(X)
    statistic = abs(Sn) / math.sqrt(n)

    passed = statistic <= THRESHOLD
    msg = f"Статистика S = {statistic:.6f}. "
    msg += "Тест пройден." if passed else "Тест НЕ пройден."
    return passed, statistic, msg


def runs_test(bit_sequence):
    n = len(bit_sequence)
    if n == 0:
        return False, 0, "Последовательность пуста"

    ones_count = bit_sequence.count('1')
    pi = ones_count / n

    if pi == 0 or pi == 1:
        return False, float('inf'), \
            "Последовательность состоит только из 0 или только из 1. Тест не применим."

    Vn = 1
    for i in range(n - 1):
        if bit_sequence[i] != bit_sequence[i + 1]:
            Vn += 1

    numerator = abs(Vn - 2 * n * pi * (1 - pi))
    denominator = 2 * math.sqrt(2 * n * pi * (1 - pi))
    statistic = numerator / denominator

    passed = statistic <= THRESHOLD
    msg = f"π (частота единиц) = {pi:.6f}\n"
    msg += f"Vn (количество серий) = {Vn}\n"
    msg += f"Статистика S = {statistic:.6f}. "
    msg += "Тест пройден." if passed else "Тест НЕ пройден."
    return passed, statistic, msg


def random_excursions_variant_test(bit_sequence):
    n = len(bit_sequence)
    if n == 0:
        return False, [], "Последовательность пуста"

    X = [2 * int(bit) - 1 for bit in bit_sequence]

    cumulative = []
    s = 0
    for xi in X:
        s += xi
        cumulative.append(s)

    S_prime = [0] + cumulative + [0]

    zero_count = S_prime.count(0)
    L = zero_count - 1

    if L == 0:
        return False, [], (
            "Последовательность S' не содержит возвратов в 0 (L = 0). "
            "Тест не применим — попробуйте более длинную последовательность."
        )

    states = list(range(-9, 0)) + list(range(1, 10))
    xi = {j: 0 for j in states}
    for val in S_prime:
        if val in xi:
            xi[val] += 1

    results = []
    all_passed = True
    for j in states:
        xi_j = xi[j]
        denominator = math.sqrt(2 * L * (4 * abs(j) - 2))
        if denominator == 0:
            Y_j = float('inf')
            passed_j = False
        else:
            Y_j = abs(xi_j - L) / denominator
            passed_j = Y_j <= THRESHOLD
        if not passed_j:
            all_passed = False
        results.append((j, xi_j, Y_j, passed_j))

    msg = f"L (число циклов / возвратов в 0) = {L}\n\n"
    msg += f"{'Состояние':>10}  {'xi_j':>8}  {'Y_j':>12}  {'Результат'}\n"
    msg += "-" * 52 + "\n"
    for (j, xi_j, Y_j, passed_j) in results:
        status = "Пройден" if passed_j else "НЕ пройден"
        msg += f"{j:>10}  {xi_j:>8}  {Y_j:>12.6f}  {status}\n"

    msg += "\n"
    if all_passed:
        msg += "Все 18 статистик прошли порог. Тест пройден."
    else:
        failed = [j for (j, _, _, p) in results if not p]
        msg += f"Тест НЕ пройден. Статистики не прошли для состояний: {failed}"

    return all_passed, results, msg


def load_sequence_from_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        sequence = ''.join(ch for ch in content if ch in '01')
        return sequence
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{e}")
        return None


def save_sequence_to_file(sequence, filepath):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(sequence)
        return True
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")
        return False

def generate_and_display():
    try:
        length = int(length_entry.get())
        if length <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Ошибка", "Длина последовательности должна быть положительным целым числом.")
        return

    if length > 100000:
        if not messagebox.askyesno(
            "Подтверждение",
            f"Вы хотите сгенерировать {length} бит. "
            "Отображение такого объёма может замедлить программу. Продолжить?"
        ):
            return

    gen = generator_var.get()
    status_label.config(text="Статус: Генерация…")
    root.update()

    def run():
        try:
            if gen == "park_miller":
                seed = int(pm_seed_entry.get())
                sequence = park_miller_generator(seed, length)
            else:
                p    = int(bbs_p_entry.get())
                q    = int(bbs_q_entry.get())
                seed = int(bbs_seed_entry.get())
                sequence = bbs_generator(p, q, seed, length)

            text_area.delete("1.0", tk.END)
            text_area.insert(tk.END, sequence)

            result_text.config(state=tk.NORMAL)
            result_text.delete("1.0", tk.END)
            result_text.config(state=tk.DISABLED)

            gen_name = "Парка-Миллера" if gen == "park_miller" else "BBS"
            status_label.config(
                text=f"Статус: Готово (сгенерировано {length} бит, генератор {gen_name})"
            )

        except ValueError as e:
            messagebox.showerror("Ошибка параметров", str(e))
            status_label.config(text="Статус: Ошибка генерации")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            status_label.config(text="Статус: Ошибка генерации")

    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()


def run_tests():
    sequence = text_area.get("1.0", tk.END).strip()
    if not sequence:
        messagebox.showwarning("Предупреждение", "Сначала сгенерируйте или загрузите последовательность.")
        return

    if not all(bit in '01' for bit in sequence):
        messagebox.showerror("Ошибка", "Последовательность должна содержать только символы 0 и 1.")
        return

    def test_thread():
        result_text.config(state=tk.NORMAL)
        result_text.delete("1.0", tk.END)
        result_text.insert(tk.END, "Тестирование…\n")
        result_text.update()
        root.update()

        time.sleep(0.1)

        # частотный тест
        freq_passed, freq_stat, freq_msg = frequency_test(sequence)
        result_text.insert(tk.END, "\n--- ЧАСТОТНЫЙ ТЕСТ ---\n")
        result_text.insert(tk.END, freq_msg + "\n")

        if not freq_passed:
            result_text.insert(
                tk.END,
                "\nЧастотный тест не пройден. Дальнейшие тесты не выполняются.\n"
            )
            result_text.config(state=tk.DISABLED)
            status_label.config(text="Статус: Готово (Частотный тест провален)")
            return

        # Тест на серии
        runs_passed, runs_stat, runs_msg = runs_test(sequence)
        result_text.insert(tk.END, "\nТЕСТ НА ПОСЛЕДОВАТЕЛЬНОСТЬ ОДИНАКОВЫХ БИТ\n")
        result_text.insert(tk.END, runs_msg + "\n")

        # Расширенный тест
        status_label.config(text="Статус: Расширенный тест…")
        root.update()

        rev_passed, rev_results, rev_msg = random_excursions_variant_test(sequence)
        result_text.insert(tk.END, "\nРАСШИРЕННЫЙ ТЕСТ НА ПРОИЗВОЛЬНЫЕ ОТКЛОНЕНИЯ\n")
        result_text.insert(tk.END, rev_msg + "\n")

        # Итог
        all_ok = freq_passed and runs_passed and rev_passed
        result_text.insert(tk.END, "\n" + "=" * 50 + "\n")
        if all_ok:
            result_text.insert(tk.END, "Последовательность успешно прошла все три теста.\n")
        else:
            failed_tests = []
            if not freq_passed:
                failed_tests.append("Частотный тест")
            if not runs_passed:
                failed_tests.append("Тест на серии")
            if not rev_passed:
                failed_tests.append("Расширенный тест")
            result_text.insert(
                tk.END,
                f"Последовательность не прошла: {', '.join(failed_tests)}.\n"
            )

        result_text.config(state=tk.DISABLED)
        status_label.config(text="Статус: Готово")

    thread = threading.Thread(target=test_thread)
    thread.daemon = True
    thread.start()
    status_label.config(text="Статус: Тестирование…")


def load_file():
    filepath = filedialog.askopenfilename(
        title="Выберите файл с последовательностью",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    if not filepath:
        return

    status_label.config(text="Статус: Загрузка…")
    root.update()

    sequence = load_sequence_from_file(filepath)
    if sequence is not None:
        text_area.delete("1.0", tk.END)
        text_area.insert(tk.END, sequence)
        length_entry.delete(0, tk.END)
        length_entry.insert(0, str(len(sequence)))
        status_label.config(text=f"Статус: Загружено {len(sequence)} бит")
        result_text.config(state=tk.NORMAL)
        result_text.delete("1.0", tk.END)
        result_text.config(state=tk.DISABLED)


def save_file():
    sequence = text_area.get("1.0", tk.END).strip()
    if not sequence:
        messagebox.showwarning("Предупреждение", "Нет последовательности для сохранения.")
        return

    filepath = filedialog.asksaveasfilename(
        title="Сохранить последовательность",
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    if not filepath:
        return

    if save_sequence_to_file(sequence, filepath):
        messagebox.showinfo("Успех", "Файл успешно сохранён.")


def clear_all():
    text_area.delete("1.0", tk.END)
    result_text.config(state=tk.NORMAL)
    result_text.delete("1.0", tk.END)
    result_text.config(state=tk.DISABLED)
    length_entry.delete(0, tk.END)
    length_entry.insert(0, "10000")
    status_label.config(text="Статус: Готово")


def on_generator_switch():
    if generator_var.get() == "park_miller":
        bbs_frame.pack_forget()
        pm_frame.pack(fill=tk.X)
    else:
        pm_frame.pack_forget()
        bbs_frame.pack(fill=tk.X)

root = tk.Tk()
root.title("лаб 2")
root.geometry("900x700")
root.minsize(800, 600)

top_frame = tk.Frame(root, padx=10, pady=10)
top_frame.pack(fill=tk.X)

tk.Label(top_frame, text="Генератор:").pack(side=tk.LEFT)

generator_var = tk.StringVar(value="park_miller")

tk.Radiobutton(top_frame, text="Парка-Миллера",
               variable=generator_var, value="park_miller",
               command=on_generator_switch).pack(side=tk.LEFT, padx=(4, 8))

tk.Radiobutton(top_frame, text="BBS",
               variable=generator_var, value="bbs",
               command=on_generator_switch).pack(side=tk.LEFT, padx=(0, 16))

tk.Label(top_frame, text="Длина последовательности (бит):").pack(side=tk.LEFT)
length_entry = tk.Entry(top_frame, width=10)
length_entry.pack(side=tk.LEFT, padx=5)
length_entry.insert(0, "10000")

tk.Button(top_frame, text="Сгенерировать",     command=generate_and_display).pack(side=tk.LEFT, padx=5)
tk.Button(top_frame, text="Загрузить из файла", command=load_file).pack(side=tk.LEFT, padx=5)
tk.Button(top_frame, text="Сохранить в файл",   command=save_file).pack(side=tk.LEFT, padx=5)
tk.Button(top_frame, text="Очистить",            command=clear_all).pack(side=tk.LEFT, padx=5)

test_frame = tk.Frame(root, padx=10, pady=2)
test_frame.pack(fill=tk.X)
tk.Button(test_frame, text="Запустить тесты", command=run_tests,
          font=("TkDefaultFont", 10), padx=10).pack(side=tk.LEFT)

pm_frame = tk.Frame(root, padx=10, pady=4)

tk.Label(pm_frame, text="Seed (1 … 2147483646):").pack(side=tk.LEFT)
pm_seed_entry = tk.Entry(pm_frame, width=15)
pm_seed_entry.pack(side=tk.LEFT, padx=5)
pm_seed_entry.insert(0, "123456789")

tk.Label(pm_frame, text="    [ a = 16807 = 7^5,  m = 2147483647 = 2^31 - 1 ]",
         fg="gray").pack(side=tk.LEFT)


bbs_frame = tk.Frame(root, padx=10, pady=4)

tk.Label(bbs_frame, text="p (простое, p=3 mod 4):").grid(row=0, column=0, sticky="e", padx=(0, 4))
bbs_p_entry = tk.Entry(bbs_frame, width=10)
bbs_p_entry.grid(row=0, column=1, sticky="w", padx=(0, 14))
bbs_p_entry.insert(0, "383")

tk.Label(bbs_frame, text="q (простое, q=3 mod 4):").grid(row=0, column=2, sticky="e", padx=(0, 4))
bbs_q_entry = tk.Entry(bbs_frame, width=10)
bbs_q_entry.grid(row=0, column=3, sticky="w", padx=(0, 14))
bbs_q_entry.insert(0, "503")

tk.Label(bbs_frame, text="Seed (НОД(seed, p*q)=1):").grid(row=0, column=4, sticky="e", padx=(0, 4))
bbs_seed_entry = tk.Entry(bbs_frame, width=10)
bbs_seed_entry.grid(row=0, column=5, sticky="w")
bbs_seed_entry.insert(0, "101355")

tk.Label(bbs_frame, text="[ N = p*q,  u_i = u_{i-1}^2 mod N,  x_i = u_i mod 2 ]",
         fg="gray").grid(row=1, column=0, columnspan=6, sticky="w", pady=(2, 0))

pm_frame.pack(fill=tk.X)

main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

left_frame = tk.Frame(main_frame)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

tk.Label(left_frame, text="Последовательность (биты):").pack(anchor=tk.W)
text_area = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, font=("Courier", 10))
text_area.pack(fill=tk.BOTH, expand=True)

right_frame = tk.Frame(main_frame, width=400)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

tk.Label(right_frame, text="Результаты тестов:").pack(anchor=tk.W)
result_text = scrolledtext.ScrolledText(
    right_frame, wrap=tk.WORD, state=tk.DISABLED,
    bg="#f0f0f0", font=("Courier", 9)
)
result_text.pack(fill=tk.BOTH, expand=True)

bottom_frame = tk.Frame(root, relief=tk.SUNKEN, bd=1)
bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

status_label = tk.Label(bottom_frame, text="Статус: Готово", anchor=tk.W, padx=10)
status_label.pack(fill=tk.X)


if __name__ == "__main__":
    root.mainloop()