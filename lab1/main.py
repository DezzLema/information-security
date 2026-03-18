import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import random
import math
import time
import threading


# --- Константы тестов ---
THRESHOLD = 1.82138636  # Пороговое значение для успешного прохождения тестов

# --- Функции тестирования (ядро лабораторной работы) ---

def frequency_test(bit_sequence):
    """
    Частотный тест (Monobit Test).
    Оценивает пропорцию нулей и единиц в последовательности.
    Возвращает: (passed, statistic, message)
    """
    n = len(bit_sequence)
    if n == 0:
        return False, 0, "Последовательность пуста"

    # Шаг 1: Преобразование 0/1 в -1/1
    X = [2 * int(bit) - 1 for bit in bit_sequence]

    # Шаг 2: Вычисление суммы Sn
    Sn = sum(X)

    # Шаг 3: Вычисление статистики S = |Sn| / sqrt(n)
    statistic = abs(Sn) / math.sqrt(n)

    # Шаг 4: Сравнение с порогом
    passed = statistic <= THRESHOLD
    msg = f"Статистика S = {statistic:.6f}. "
    msg += "Тест пройден." if passed else "Тест НЕ пройден."
    return passed, statistic, msg


def runs_test(bit_sequence):
    """
    Тест на последовательность одинаковых бит (Runs Test).
    Анализирует количество цепочек (подряд идущих одинаковых бит).
    Возвращает: (passed, statistic, message)
    """
    n = len(bit_sequence)
    if n == 0:
        return False, 0, "Последовательность пуста"

    # Шаг 1: Вычисление частоты единиц π
    ones_count = bit_sequence.count('1')
    pi = ones_count / n

    # Предварительная проверка (чтобы избежать деления на ноль)
    if pi == 0 or pi == 1:
        return False, float('inf'), "Последовательность состоит только из 0 или только из 1. Тест не применим."

    # Шаг 2: Вычисление Vn (количество цепочек)
    Vn = 1  # Начинаем с 1, так как первая цепочка считается
    for i in range(n - 1):
        if bit_sequence[i] != bit_sequence[i + 1]:
            Vn += 1

    # Шаг 3: Вычисление статистики S
    numerator = abs(Vn - 2 * n * pi * (1 - pi))
    denominator = 2 * math.sqrt(2 * n * pi * (1 - pi))
    statistic = numerator / denominator

    # Шаг 4: Сравнение с порогом
    passed = statistic <= THRESHOLD
    msg = f"π (частота единиц) = {pi:.6f}\n"
    msg += f"Vn (количество цепочек) = {Vn}\n"
    msg += f"Статистика S = {statistic:.6f}. "
    msg += "Тест пройден." if passed else "Тест НЕ пройден."
    return passed, statistic, msg


# --- Вспомогательные функции ---

def generate_sequence(length):
    """Генерирует псевдослучайную последовательность бит (строку из 0 и 1)."""
    return ''.join(str(random.randint(0, 1)) for _ in range(length))


def load_sequence_from_file(filepath):
    """Загружает последовательность из текстового файла, игнорируя пробелы и переводы строк."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        # Оставляем только символы '0' и '1'
        sequence = ''.join([ch for ch in content if ch in '01'])
        return sequence
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{e}")
        return None


def save_sequence_to_file(sequence, filepath):
    """Сохраняет последовательность в текстовый файл."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(sequence)
        return True
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")
        return False



def run_tests():
    """Запускает тесты в отдельном потоке, чтобы не блокировать GUI."""
    sequence = text_area.get("1.0", tk.END).strip()
    if not sequence:
        messagebox.showwarning("Предупреждение", "Сначала сгенерируйте или загрузите последовательность.")
        return

    if not all(bit in '01' for bit in sequence):
        messagebox.showerror("Ошибка", "Последовательность должна содержать только символы 0 и 1.")
        return

    # Запуск тестирования в отдельном потоке
    def test_thread():
        # Очистка и обновление статуса
        result_text.config(state=tk.NORMAL)
        result_text.delete("1.0", tk.END)
        result_text.insert(tk.END, "Тестирование...\n")
        result_text.update()
        root.update()

        # Имитация длительного процесса (если последовательность большая)
        time.sleep(0.1)

        # Частотный тест
        freq_passed, freq_stat, freq_msg = frequency_test(sequence)
        result_text.insert(tk.END, "\n--- ЧАСТОТНЫЙ ТЕСТ ---\n")
        result_text.insert(tk.END, freq_msg + "\n")

        # Если частотный тест не пройден, останавливаемся (по примечанию в лабораторной)
        if not freq_passed:
            result_text.insert(tk.END, "\n⚠️ Частотный тест не пройден. Дальнейшие тесты не выполняются.\n")
            result_text.config(state=tk.DISABLED)
            status_label.config(text="Статус: Готово (Частотный тест провален)")
            return

        # Тест на последовательности одинаковых бит
        runs_passed, runs_stat, runs_msg = runs_test(sequence)
        result_text.insert(tk.END, "\n--- ТЕСТ НА ПОСЛЕДОВАТЕЛЬНОСТЬ ОДИНАКОВЫХ БИТ ---\n")
        result_text.insert(tk.END, runs_msg + "\n")

        # Финальный вердикт
        if freq_passed and runs_passed:
            verdict = "Последовательность успешно прошла оба теста."
        else:
            verdict = "❌ Последовательность НЕ прошла один из тестов."
        result_text.insert(tk.END, "\n" + "="*50 + "\n")
        result_text.insert(tk.END, verdict + "\n")
        result_text.config(state=tk.DISABLED)
        status_label.config(text="Статус: Готово")

    thread = threading.Thread(target=test_thread)
    thread.daemon = True
    thread.start()
    status_label.config(text="Статус: Тестирование...")


def generate_and_display():
    """Генерирует последовательность и отображает её в текстовом поле."""
    try:
        length = int(length_entry.get())
        if length <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Ошибка", "Длина последовательности должна быть положительным целым числом.")
        return

    # Проверка на слишком большую длину для отображения
    if length > 100000:
        if not messagebox.askyesno("Подтверждение", f"Вы хотите сгенерировать {length} бит. Отображение такого объема может замедлить программу. Продолжить?"):
            return

    status_label.config(text="Статус: Генерация...")
    root.update()

    # Генерация в отдельном потоке, чтобы не блокировать интерфейс
    def generate_thread():
        sequence = generate_sequence(length)
        text_area.delete("1.0", tk.END)
        text_area.insert(tk.END, sequence)
        status_label.config(text="Статус: Готово (сгенерировано)")
        result_text.config(state=tk.NORMAL)
        result_text.delete("1.0", tk.END)
        result_text.config(state=tk.DISABLED)

    thread = threading.Thread(target=generate_thread)
    thread.daemon = True
    thread.start()


def load_file():
    """Загружает последовательность из файла."""
    filepath = filedialog.askopenfilename(
        title="Выберите файл с последовательностью",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    if not filepath:
        return

    status_label.config(text="Статус: Загрузка...")
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
    """Сохраняет текущую последовательность в файл."""
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
        messagebox.showinfo("Успех", "Файл успешно сохранен.")


def clear_all():
    """Очищает все поля."""
    text_area.delete("1.0", tk.END)
    result_text.config(state=tk.NORMAL)
    result_text.delete("1.0", tk.END)
    result_text.config(state=tk.DISABLED)
    length_entry.delete(0, tk.END)
    length_entry.insert(0, "10000")
    status_label.config(text="Статус: Готово")


# gui
root = tk.Tk()
root.title("лаба 1")
root.geometry("900x700")
root.minsize(800, 600)

# --- Верхняя панель с настройками ---
top_frame = tk.Frame(root, padx=10, pady=10)
top_frame.pack(fill=tk.X)

tk.Label(top_frame, text="Длина последовательности (бит):").pack(side=tk.LEFT)
length_entry = tk.Entry(top_frame, width=15)
length_entry.pack(side=tk.LEFT, padx=5)
length_entry.insert(0, "10000")  # По умолчанию 10000 бит

generate_btn = tk.Button(top_frame, text="Сгенерировать", command=generate_and_display)
generate_btn.pack(side=tk.LEFT, padx=5)

load_btn = tk.Button(top_frame, text="Загрузить из файла", command=load_file)
load_btn.pack(side=tk.LEFT, padx=5)

save_btn = tk.Button(top_frame, text="Сохранить в файл", command=save_file)
save_btn.pack(side=tk.LEFT, padx=5)

clear_btn = tk.Button(top_frame, text="Очистить", command=clear_all)
clear_btn.pack(side=tk.LEFT, padx=5)

test_btn = tk.Button(top_frame, text="Запустить тесты", command=run_tests, bg="lightblue")
test_btn.pack(side=tk.LEFT, padx=20)

# --- Основная область: последовательность и результаты ---
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

# Левая часть - последовательность
left_frame = tk.Frame(main_frame)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

tk.Label(left_frame, text="Последовательность (биты):").pack(anchor=tk.W)
text_area = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, font=("Courier", 10))
text_area.pack(fill=tk.BOTH, expand=True)

# Правая часть - результаты тестов
right_frame = tk.Frame(main_frame, width=350)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

tk.Label(right_frame, text="Результаты тестов:").pack(anchor=tk.W)
result_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, state=tk.DISABLED, bg="#f0f0f0")
result_text.pack(fill=tk.BOTH, expand=True)

# --- Нижняя панель статуса ---
bottom_frame = tk.Frame(root, relief=tk.SUNKEN, bd=1)
bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

status_label = tk.Label(bottom_frame, text="Статус: Готово", anchor=tk.W, padx=10)
status_label.pack(fill=tk.X)

# --- Запуск главного цикла ---
if __name__ == "__main__":
    root.mainloop()