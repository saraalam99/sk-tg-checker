import os
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
from dotenv import load_dotenv
from telegram_phone_number_checker import TelegramPhoneNumberChecker
import asyncio
import csv
import random

# Load environment variables
load_dotenv()

class TelegramCheckerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("TG DATA CHECKER")
        self.geometry("600x600")
        self.configure(bg='#2C3E50')

        self.delay = 1  # Default delay between requests in seconds
        self.sleep_time = 10  # Default sleep time in seconds
        self.use_proxies = tk.BooleanVar(value=False)
        
        # Load proxies
        self.proxies = self.load_proxies("proxies.txt")
        
        # Load accounts
        self.accounts = self.load_accounts()
        print(f"Loaded accounts: {self.accounts}")  # Debug print to check loaded accounts

        self.create_widgets()

    def load_proxies(self, file_path):
        proxies = []
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                proxies = [line.strip() for line in f if line.strip()]
        return proxies

    def load_accounts(self):
        accounts = []
        for i in range(1, 6):  # Assuming up to 5 accounts for rotation
            api_id = os.getenv(f"API_ID_{i}")
            api_hash = os.getenv(f"API_HASH_{i}")
            phone_number = os.getenv(f"PHONE_NUMBER_{i}")
            print(f"Loaded API_ID_{i}: {api_id}, API_HASH_{i}: {api_hash}, PHONE_NUMBER_{i}: {phone_number}")  # Debug print
            if api_id and api_hash and phone_number:
                accounts.append((api_id, api_hash, phone_number))
        return accounts

    def create_widgets(self):
        # Banner
        banner = tk.Label(self, text="TG DATA CHECKER", font=("Arial", 20, "bold"), fg="#ECF0F1", bg='#2C3E50')
        banner.pack(pady=10)

        # Configuration Button
        self.config_button = tk.Button(self, text="Configuration", command=self.open_config, font=("Arial", 12), bg='#3498DB', fg='#ECF0F1')
        self.config_button.pack(pady=10)

        # Use Proxies Checkbutton
        self.proxies_checkbutton = tk.Checkbutton(self, text="Use Proxies", variable=self.use_proxies, font=("Arial", 12), bg='#2C3E50', fg='#ECF0F1', selectcolor='#2C3E50')
        self.proxies_checkbutton.pack(pady=10)

        # Input Textbox
        self.input_text = tk.Text(self, height=10, width=50, bg='#ECF0F1', fg='#2C3E50', font=("Arial", 12))
        self.input_text.pack(pady=10)

        # Check Numbers Button
        self.check_button = tk.Button(self, text="Check Numbers", command=self.start_checking, font=("Arial", 12), bg='#3498DB', fg='#ECF0F1')
        self.check_button.pack(pady=10)

        # Output Text Area
        self.output_text = tk.Text(self, height=10, width=50, state=tk.DISABLED, bg='#ECF0F1', fg='#2C3E50', font=("Arial", 12))
        self.output_text.pack(pady=10)

        # Progress Bar
        self.progress_bar = ttk.Progressbar(self, orient='horizontal', mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=10)

    def open_config(self):
        config_window = tk.Toplevel(self)
        config_window.title("Configuration")
        config_window.geometry("300x200")
        config_window.configure(bg='#2C3E50')

        tk.Label(config_window, text="Set delay between requests (seconds):", font=("Arial", 12), fg="#ECF0F1", bg='#2C3E50').pack(pady=10)
        delay_var = tk.StringVar(value=str(self.delay))
        delay_entry = tk.Entry(config_window, textvariable=delay_var, font=("Arial", 12), bg='#ECF0F1', fg='#2C3E50')
        delay_entry.pack(pady=10)

        tk.Label(config_window, text="Set sleep time (seconds):", font=("Arial", 12), fg="#ECF0F1", bg='#2C3E50').pack(pady=10)
        sleep_var = tk.StringVar(value=str(self.sleep_time))
        sleep_entry = tk.Entry(config_window, textvariable=sleep_var, font=("Arial", 12), bg='#ECF0F1', fg='#2C3E50')
        sleep_entry.pack(pady=10)

        def save_config():
            try:
                self.delay = int(delay_var.get())
                self.sleep_time = int(sleep_var.get())
                config_window.destroy()
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numbers.")

        save_button = tk.Button(config_window, text="Save", command=save_config, font=("Arial", 12), bg='#3498DB', fg='#ECF0F1')
        save_button.pack(pady=10)

    def start_checking(self):
        self.check_button.config(state=tk.DISABLED)
        phone_numbers = self.input_text.get("1.0", tk.END).strip().split("\n")
        phone_numbers = [num.strip() for num in phone_numbers if num.strip()]

        if not phone_numbers:
            messagebox.showwarning("Input Error", "Please enter phone numbers to check.")
            self.check_button.config(state=tk.NORMAL)
            return

        Thread(target=self.check_numbers, args=(phone_numbers,)).start()

    def get_proxy(self):
        if self.use_proxies.get() and self.proxies:
            return random.choice(self.proxies)
        return None

    def get_account(self):
        if self.accounts:
            return random.choice(self.accounts)
        return None

    def check_numbers(self, phone_numbers):
        account = self.get_account()
        if not account:
            messagebox.showerror("Configuration Error", "No Telegram account details found.")
            self.check_button.config(state=tk.NORMAL)
            return

        api_id, api_hash, phone_number = account
        proxy = self.get_proxy()

        async def run_checker():
            async with TelegramPhoneNumberChecker(api_id, api_hash, phone_number) as checker:
                results = await checker.check_numbers(phone_numbers)

                self.progress_bar["maximum"] = len(phone_numbers)
                self.save_results(results)
                for i, result in enumerate(results):
                    self.display_result(result)
                    self.progress_bar["value"] = i + 1
                    self.update_idletasks()
                    await asyncio.sleep(self.delay)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_checker())
        self.check_button.config(state=tk.NORMAL)

    def save_results(self, results):
        try:
            with open("registered.csv", mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Phone Number", "Status", "Username", "Last Seen"])
                for result in results:
                    if result["status"] == "Registered":
                        writer.writerow([result["number"], result["status"], result.get("username", "N/A"), result.get("last_seen", "N/A")])
        except Exception as e:
            messagebox.showerror("Save Results Error", f"Error saving results: {e}")
            print(f"Save Results Error: {e}")

    def display_result(self, result):
        try:
            self.output_text.config(state=tk.NORMAL)
            self.output_text.insert(tk.END, f"{result['number']}: {result['status']} - {result.get('username', 'N/A')} (Last seen: {result.get('last_seen', 'N/A')})\n")
            self.output_text.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Display Result Error", f"Error displaying result: {e}")
            print(f"Display Result Error: {e}")

if __name__ == "__main__":
    try:
        app = TelegramCheckerApp()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Application Error", f"Error in main application loop: {e}")
        print(f"Application Error: {e}")
