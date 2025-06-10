import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import pyautogui
import keyboard
import requests
import socket
import ipaddress
import json
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import dns.resolver

class PenTestApp:
    def __init__(self, root):
        self.root = root
        
        # Language settings
        self.current_language = "en"  # Default language is English
        self.translations = self.load_translations()
        
        self.root.title(self.get_translation("app_title"))
        self.root.geometry("800x650")
        self.root.resizable(True, True)
        # Set icon
        self.root.iconbitmap("images/sibna.ico")  # Place this after self.root initialization


        
        # Dark theme setup
        self.root.configure(bg="#1e1e1e")
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Configure styles for dark theme
        self.style.configure("TFrame", background="#1e1e1e")
        self.style.configure("TButton", background="#0078d7", foreground="white", font=("Arial", 10, "bold"))
        self.style.map("TButton", background=[("active", "#005fa3")])
        self.style.configure("TLabel", background="#1e1e1e", foreground="#ffffff", font=("Arial", 10))
        self.style.configure("TEntry", fieldbackground="#2d2d2d", foreground="white", font=("Arial", 10))
        self.style.configure("Horizontal.TProgressbar", background="#0078d7")
        self.style.configure("TNotebook", background="#1e1e1e", foreground="white")
        self.style.configure("TNotebook.Tab", background="#2d2d2d", foreground="white", padding=[10, 2])
        self.style.map("TNotebook.Tab", background=[("selected", "#0078d7")])
        
        # Control variables
        self.target = tk.StringVar()
        self.wordlist = tk.StringVar()
        self.port = tk.IntVar(value=80)
        self.delay = tk.DoubleVar(value=0.5)
        self.is_running = False
        self.thread = None
        self.test_results = []
        
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header frame with title and language selector
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=5)
        
        # App title
        title_label = ttk.Label(header_frame, text=self.get_translation("app_title"), font=("Arial", 16, "bold"))
        title_label.pack(side=tk.LEFT, pady=10)
        
        # Language selector
        lang_frame = ttk.Frame(header_frame)
        lang_frame.pack(side=tk.RIGHT, padx=10)
        
        lang_label = ttk.Label(lang_frame, text=self.get_translation("language"))
        lang_label.pack(side=tk.LEFT, padx=5)
        
        self.en_button = ttk.Button(lang_frame, text="English", command=lambda: self.change_language("en"))
        self.en_button.pack(side=tk.LEFT, padx=2)
        
        self.ar_button = ttk.Button(lang_frame, text="العربية", command=lambda: self.change_language("ar"))
        self.ar_button.pack(side=tk.LEFT, padx=2)
        
        # Create tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Password testing tab
        self.password_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.password_frame, text=self.get_translation("password_tab"))
        
        # Port scanning tab
        self.port_scan_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.port_scan_frame, text=self.get_translation("port_scan_tab"))
        
        # SQL Injection tab
        self.sql_injection_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.sql_injection_frame, text=self.get_translation("sql_injection_tab"))
        
        # XSS Testing tab
        self.xss_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.xss_frame, text=self.get_translation("xss_tab"))
        
        # DNS Scanning tab
        self.dns_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.dns_frame, text=self.get_translation("dns_tab"))
        
        # Message sending tab
        self.message_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.message_frame, text=self.get_translation("message_tab"))
        
        # Setup tab contents
        self._setup_password_tab()
        self._setup_port_scan_tab()
        self._setup_sql_injection_tab()
        self._setup_xss_tab()
        self._setup_dns_tab()
        self._setup_message_tab()
        
        # Status area
        self.status_frame = ttk.Frame(self.main_frame, relief=tk.SUNKEN, borderwidth=1)
        self.status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(self.status_frame, text=self.get_translation("ready"), anchor=tk.CENTER)
        self.status_label.pack(fill=tk.X)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.main_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # Results area with save/load buttons
        results_frame = ttk.Frame(self.main_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        results_header = ttk.Frame(results_frame)
        results_header.pack(fill=tk.X)
        
        results_label = ttk.Label(results_header, text=self.get_translation("results"))
        results_label.pack(side=tk.LEFT)
        
        # Save/Load buttons
        save_button = ttk.Button(results_header, text=self.get_translation("save_results"), command=self.save_results)
        save_button.pack(side=tk.RIGHT, padx=5)
        
        load_button = ttk.Button(results_header, text=self.get_translation("load_results"), command=self.load_results)
        load_button.pack(side=tk.RIGHT, padx=5)
        
        # Results text area with scrollbar
        self.results_text = tk.Text(results_frame, height=8, bg="#2d2d2d", fg="white")
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.results_text, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=scrollbar.set)
        
        # Emergency stop hotkey
        keyboard.add_hotkey('esc', self.emergency_stop)
        
        # Initialize charts data
        self.chart_data = {}
    
    def load_translations(self):
        """Load translations for multilingual support"""
        return {
            "en": {
                "app_title": "Fennec",
                "language": "Language:",
                "password_tab": "Password Testing",
                "port_scan_tab": "Port Scanning",
                "sql_injection_tab": "SQL Injection",
                "xss_tab": "XSS Testing",
                "dns_tab": "DNS Scanning",
                "message_tab": "Message Sender",
                "target": "Target (URL/IP):",
                "username": "Username:",
                "wordlist": "Password List:",
                "browse": "Browse",
                "delay": "Delay between attempts (seconds):",
                "start_test": "Start Test",
                "stop_test": "Stop Test",
                "target_ip": "Target IP:",
                "port_range": "Port Range:",
                "to": "to",
                "scan_delay": "Scan Delay (seconds):",
                "start_scan": "Start Scan",
                "message_text": "Message Text:",
                "send_count": "Number of Messages:",
                "message_delay": "Delay between messages (seconds):",
                "input_position": "Message Input Position:",
                "set_position": "Set Position",
                "position_not_set": "Position not set",
                "start_sending": "Start Sending",
                "stop_sending": "Stop Sending",
                "ready": "Ready",
                "results": "Results:",
                "save_results": "Save Results",
                "load_results": "Load Results",
                "error": "Error",
                "enter_valid_target": "Please enter a valid target",
                "select_wordlist": "Please select a password list file",
                "emergency_stop": "Emergency Stop",
                "process_stopped": "Process stopped by ESC key",
                "sql_url": "Target URL:",
                "param_to_test": "Parameter to Test:",
                "test_payloads": "Test Payloads:",
                "start_sql_test": "Start SQL Test",
                "xss_url": "Target URL:",
                "xss_param": "Parameter to Test:",
                "xss_payloads": "XSS Payloads:",
                "start_xss_test": "Start XSS Test",
                "domain": "Domain:",
                "record_types": "Record Types:",
                "start_dns_scan": "Start DNS Scan",
                "chart_view": "Chart View",
                "text_view": "Text View"
            },
            "ar": {
                "app_title": "الفنك",
                "language": "اللغة:",
                "password_tab": "فحص كلمات المرور",
                "port_scan_tab": "فحص المنافذ",
                "sql_injection_tab": "حقن SQL",
                "xss_tab": "فحص XSS",
                "dns_tab": "فحص DNS",
                "message_tab": "إرسال الرسائل",
                "target": "الهدف (URL/IP):",
                "username": "اسم المستخدم:",
                "wordlist": "قائمة كلمات المرور:",
                "browse": "استعراض",
                "delay": "التأخير بين المحاولات (ثواني):",
                "start_test": "بدء الفحص",
                "stop_test": "إيقاف الفحص",
                "target_ip": "الهدف (IP):",
                "port_range": "نطاق المنافذ:",
                "to": "إلى",
                "scan_delay": "التأخير بين الفحوصات (ثواني):",
                "start_scan": "بدء فحص المنافذ",
                "message_text": "نص الرسالة:",
                "send_count": "عدد مرات الإرسال:",
                "message_delay": "التأخير بين الرسائل (ثواني):",
                "input_position": "موقع إدخال الرسائل:",
                "set_position": "تحديد الموقع",
                "position_not_set": "لم يتم تحديد الموقع بعد",
                "start_sending": "بدء الإرسال",
                "stop_sending": "إيقاف الإرسال",
                "ready": "جاهز",
                "results": "النتائج:",
                "save_results": "حفظ النتائج",
                "load_results": "تحميل النتائج",
                "error": "خطأ",
                "enter_valid_target": "الرجاء إدخال هدف صالح",
                "select_wordlist": "الرجاء تحديد ملف قائمة كلمات المرور",
                "emergency_stop": "إيقاف طارئ",
                "process_stopped": "تم إيقاف العملية بواسطة مفتاح ESC",
                "sql_url": "عنوان URL الهدف:",
                "param_to_test": "المعلمة المراد اختبارها:",
                "test_payloads": "حمولات الاختبار:",
                "start_sql_test": "بدء اختبار SQL",
                "xss_url": "عنوان URL الهدف:",
                "xss_param": "المعلمة المراد اختبارها:",
                "xss_payloads": "حمولات XSS:",
                "start_xss_test": "بدء اختبار XSS",
                "domain": "النطاق:",
                "record_types": "أنواع السجلات:",
                "start_dns_scan": "بدء فحص DNS",
                "chart_view": "عرض الرسم البياني",
                "text_view": "عرض النص"
            }
        }
    
    def get_translation(self, key):
        """Get translation for a key in current language"""
        return self.translations.get(self.current_language, {}).get(key, key)
    
    def change_language(self, lang_code):
        """Change the application language"""
        if lang_code in self.translations:
            self.current_language = lang_code
            self.update_ui_language()
    
    def update_ui_language(self):
        """Update all UI elements with the current language"""
        # Update window title
        self.root.title(self.get_translation("app_title"))
        
        # Update tab names
        self.notebook.tab(0, text=self.get_translation("password_tab"))
        self.notebook.tab(1, text=self.get_translation("port_scan_tab"))
        self.notebook.tab(2, text=self.get_translation("sql_injection_tab"))
        self.notebook.tab(3, text=self.get_translation("xss_tab"))
        self.notebook.tab(4, text=self.get_translation("dns_tab"))
        self.notebook.tab(5, text=self.get_translation("message_tab"))
        
        # Recreate all tabs with new language
        self._setup_password_tab()
        self._setup_port_scan_tab()
        self._setup_sql_injection_tab()
        self._setup_xss_tab()
        self._setup_dns_tab()
        self._setup_message_tab()
        
        # Update status
        self.status_label.config(text=self.get_translation("ready"))
    
    def _setup_password_tab(self):
        """Setup password testing tab"""
        # Clear existing widgets
        for widget in self.password_frame.winfo_children():
            widget.destroy()
        
        # Target field
        target_label = ttk.Label(self.password_frame, text=self.get_translation("target"))
        target_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        target_entry = ttk.Entry(self.password_frame, textvariable=self.target, width=40)
        target_entry.grid(row=0, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Username field
        username_label = ttk.Label(self.password_frame, text=self.get_translation("username"))
        username_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(self.password_frame, width=40)
        self.username_entry.grid(row=1, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Wordlist field
        wordlist_label = ttk.Label(self.password_frame, text=self.get_translation("wordlist"))
        wordlist_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        wordlist_entry = ttk.Entry(self.password_frame, textvariable=self.wordlist, width=30)
        wordlist_entry.grid(row=2, column=1, pady=5, padx=5, sticky=tk.W)
        
        browse_button = ttk.Button(self.password_frame, text=self.get_translation("browse"), command=self.browse_wordlist)
        browse_button.grid(row=2, column=2, pady=5, padx=5)
        
        # Delay field
        delay_label = ttk.Label(self.password_frame, text=self.get_translation("delay"))
        delay_label.grid(row=3, column=0, sticky=tk.W, pady=5)
        delay_entry = ttk.Spinbox(self.password_frame, from_=0.1, to=5.0, increment=0.1, textvariable=self.delay, width=10)
        delay_entry.grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Start/Stop buttons
        button_frame = ttk.Frame(self.password_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        self.start_pw_button = ttk.Button(button_frame, text=self.get_translation("start_test"), command=self.start_password_test)
        self.start_pw_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_pw_button = ttk.Button(button_frame, text=self.get_translation("stop_test"), command=self.stop_test, state=tk.DISABLED)
        self.stop_pw_button.pack(side=tk.LEFT, padx=5)
        
        # Chart/Text view toggle
        view_frame = ttk.Frame(self.password_frame)
        view_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        self.chart_button = ttk.Button(view_frame, text=self.get_translation("chart_view"), command=lambda: self.toggle_view("password", "chart"))
        self.chart_button.pack(side=tk.LEFT, padx=5)
        
        self.text_button = ttk.Button(view_frame, text=self.get_translation("text_view"), command=lambda: self.toggle_view("password", "text"))
        self.text_button.pack(side=tk.LEFT, padx=5)
        
        # Chart container
        self.pw_chart_frame = ttk.Frame(self.password_frame)
        self.pw_chart_frame.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=10)
    
    def _setup_port_scan_tab(self):
        """Setup port scanning tab"""
        # Clear existing widgets
        for widget in self.port_scan_frame.winfo_children():
            widget.destroy()
        
        # Target field
        target_label = ttk.Label(self.port_scan_frame, text=self.get_translation("target_ip"))
        target_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        target_entry = ttk.Entry(self.port_scan_frame, textvariable=self.target, width=40)
        target_entry.grid(row=0, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Port range
        port_range_label = ttk.Label(self.port_scan_frame, text=self.get_translation("port_range"))
        port_range_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        port_range_frame = ttk.Frame(self.port_scan_frame)
        port_range_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        self.start_port = tk.IntVar(value=1)
        self.end_port = tk.IntVar(value=1024)
        
        start_port_entry = ttk.Spinbox(port_range_frame, from_=1, to=65535, textvariable=self.start_port, width=10)
        start_port_entry.pack(side=tk.LEFT, padx=5)
        
        range_label = ttk.Label(port_range_frame, text=self.get_translation("to"))
        range_label.pack(side=tk.LEFT, padx=5)
        
        end_port_entry = ttk.Spinbox(port_range_frame, from_=1, to=65535, textvariable=self.end_port, width=10)
        end_port_entry.pack(side=tk.LEFT, padx=5)
        
        # Delay field
        delay_label = ttk.Label(self.port_scan_frame, text=self.get_translation("scan_delay"))
        delay_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        delay_entry = ttk.Spinbox(self.port_scan_frame, from_=0.0, to=1.0, increment=0.1, textvariable=self.delay, width=10)
        delay_entry.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Start/Stop buttons
        button_frame = ttk.Frame(self.port_scan_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.start_port_button = ttk.Button(button_frame, text=self.get_translation("start_scan"), command=self.start_port_scan)
        self.start_port_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_port_button = ttk.Button(button_frame, text=self.get_translation("stop_test"), command=self.stop_test, state=tk.DISABLED)
        self.stop_port_button.pack(side=tk.LEFT, padx=5)
        
        # Chart/Text view toggle
        view_frame = ttk.Frame(self.port_scan_frame)
        view_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        self.chart_button = ttk.Button(view_frame, text=self.get_translation("chart_view"), command=lambda: self.toggle_view("port", "chart"))
        self.chart_button.pack(side=tk.LEFT, padx=5)
        
        self.text_button = ttk.Button(view_frame, text=self.get_translation("text_view"), command=lambda: self.toggle_view("port", "text"))
        self.text_button.pack(side=tk.LEFT, padx=5)
        
        # Chart container
        self.port_chart_frame = ttk.Frame(self.port_scan_frame)
        self.port_chart_frame.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=10)
    
    def _setup_sql_injection_tab(self):
        """Setup SQL injection testing tab"""
        # Clear existing widgets
        for widget in self.sql_injection_frame.winfo_children():
            widget.destroy()
        
        # URL field
        url_label = ttk.Label(self.sql_injection_frame, text=self.get_translation("sql_url"))
        url_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        self.sql_url_entry = ttk.Entry(self.sql_injection_frame, width=50)
        self.sql_url_entry.grid(row=0, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Parameter field
        param_label = ttk.Label(self.sql_injection_frame, text=self.get_translation("param_to_test"))
        param_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        self.sql_param_entry = ttk.Entry(self.sql_injection_frame, width=20)
        self.sql_param_entry.grid(row=1, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Payloads field
        payloads_label = ttk.Label(self.sql_injection_frame, text=self.get_translation("test_payloads"))
        payloads_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        # Default SQL injection payloads
        default_payloads = "' OR '1'='1\n' OR 1=1--\n' OR 1=1#\n'; DROP TABLE users--\n1' OR '1' = '1\n' UNION SELECT username, password FROM users--"
        
        self.sql_payloads_text = tk.Text(self.sql_injection_frame, height=6, width=50, bg="#2d2d2d", fg="white")
        self.sql_payloads_text.grid(row=2, column=1, pady=5, padx=5, sticky=tk.W)
        self.sql_payloads_text.insert(tk.END, default_payloads)
        
        sql_scroll = ttk.Scrollbar(self.sql_injection_frame, command=self.sql_payloads_text.yview)
        sql_scroll.grid(row=2, column=2, sticky='nsew')
        self.sql_payloads_text.config(yscrollcommand=sql_scroll.set)
        
        # Delay field
        delay_label = ttk.Label(self.sql_injection_frame, text=self.get_translation("delay"))
        delay_label.grid(row=3, column=0, sticky=tk.W, pady=5)
        self.sql_delay_var = tk.DoubleVar(value=1.0)
        delay_entry = ttk.Spinbox(self.sql_injection_frame, from_=0.5, to=5.0, increment=0.5, textvariable=self.sql_delay_var, width=10)
        delay_entry.grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Start/Stop buttons
        button_frame = ttk.Frame(self.sql_injection_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        self.start_sql_button = ttk.Button(button_frame, text=self.get_translation("start_sql_test"), command=self.start_sql_injection_test)
        self.start_sql_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_sql_button = ttk.Button(button_frame, text=self.get_translation("stop_test"), command=self.stop_test, state=tk.DISABLED)
        self.stop_sql_button.pack(side=tk.LEFT, padx=5)
        
        # Chart/Text view toggle
        view_frame = ttk.Frame(self.sql_injection_frame)
        view_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        self.chart_button = ttk.Button(view_frame, text=self.get_translation("chart_view"), command=lambda: self.toggle_view("sql", "chart"))
        self.chart_button.pack(side=tk.LEFT, padx=5)
        
        self.text_button = ttk.Button(view_frame, text=self.get_translation("text_view"), command=lambda: self.toggle_view("sql", "text"))
        self.text_button.pack(side=tk.LEFT, padx=5)
        
        # Chart container
        self.sql_chart_frame = ttk.Frame(self.sql_injection_frame)
        self.sql_chart_frame.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=10)
    
    def _setup_xss_tab(self):
        """Setup XSS testing tab"""
        # Clear existing widgets
        for widget in self.xss_frame.winfo_children():
            widget.destroy()
        
        # URL field
        url_label = ttk.Label(self.xss_frame, text=self.get_translation("xss_url"))
        url_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        self.xss_url_entry = ttk.Entry(self.xss_frame, width=50)
        self.xss_url_entry.grid(row=0, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Parameter field
        param_label = ttk.Label(self.xss_frame, text=self.get_translation("xss_param"))
        param_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        self.xss_param_entry = ttk.Entry(self.xss_frame, width=20)
        self.xss_param_entry.grid(row=1, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Payloads field
        payloads_label = ttk.Label(self.xss_frame, text=self.get_translation("xss_payloads"))
        payloads_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        # Default XSS payloads
        default_payloads = "<script>alert('XSS')</script>\n<img src=x onerror=alert('XSS')>\n<body onload=alert('XSS')>\n<svg onload=alert('XSS')>\n"+"javascript:alert('XSS')\n<iframe src=javascript:alert('XSS')>"
        
        self.xss_payloads_text = tk.Text(self.xss_frame, height=6, width=50, bg="#2d2d2d", fg="white")
        self.xss_payloads_text.grid(row=2, column=1, pady=5, padx=5, sticky=tk.W)
        self.xss_payloads_text.insert(tk.END, default_payloads)
        
        xss_scroll = ttk.Scrollbar(self.xss_frame, command=self.xss_payloads_text.yview)
        xss_scroll.grid(row=2, column=2, sticky='nsew')
        self.xss_payloads_text.config(yscrollcommand=xss_scroll.set)
        
        # Delay field
        delay_label = ttk.Label(self.xss_frame, text=self.get_translation("delay"))
        delay_label.grid(row=3, column=0, sticky=tk.W, pady=5)
        self.xss_delay_var = tk.DoubleVar(value=1.0)
        delay_entry = ttk.Spinbox(self.xss_frame, from_=0.5, to=5.0, increment=0.5, textvariable=self.xss_delay_var, width=10)
        delay_entry.grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Start/Stop buttons
        button_frame = ttk.Frame(self.xss_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        self.start_xss_button = ttk.Button(button_frame, text=self.get_translation("start_xss_test"), command=self.start_xss_test)
        self.start_xss_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_xss_button = ttk.Button(button_frame, text=self.get_translation("stop_test"), command=self.stop_test, state=tk.DISABLED)
        self.stop_xss_button.pack(side=tk.LEFT, padx=5)
        
        # Chart/Text view toggle
        view_frame = ttk.Frame(self.xss_frame)
        view_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        self.chart_button = ttk.Button(view_frame, text=self.get_translation("chart_view"), command=lambda: self.toggle_view("xss", "chart"))
        self.chart_button.pack(side=tk.LEFT, padx=5)
        
        self.text_button = ttk.Button(view_frame, text=self.get_translation("text_view"), command=lambda: self.toggle_view("xss", "text"))
        self.text_button.pack(side=tk.LEFT, padx=5)
        
        # Chart container
        self.xss_chart_frame = ttk.Frame(self.xss_frame)
        self.xss_chart_frame.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=10)
    
    def _setup_dns_tab(self):
        """Setup DNS scanning tab"""
        # Clear existing widgets
        for widget in self.dns_frame.winfo_children():
            widget.destroy()
        
        # Domain field
        domain_label = ttk.Label(self.dns_frame, text=self.get_translation("domain"))
        domain_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        self.domain_entry = ttk.Entry(self.dns_frame, width=40)
        self.domain_entry.grid(row=0, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Record types
        record_label = ttk.Label(self.dns_frame, text=self.get_translation("record_types"))
        record_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        record_frame = ttk.Frame(self.dns_frame)
        record_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        self.record_types = {}
        record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA', 'CNAME']
        
        for i, record in enumerate(record_types):
            var = tk.BooleanVar(value=True if record in ['A', 'MX', 'NS'] else False)
            self.record_types[record] = var
            cb = ttk.Checkbutton(record_frame, text=record, variable=var)
            cb.grid(row=i//4, column=i%4, padx=5, sticky=tk.W)
        
        # Delay field
        delay_label = ttk.Label(self.dns_frame, text=self.get_translation("delay"))
        delay_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        self.dns_delay_var = tk.DoubleVar(value=0.5)
        delay_entry = ttk.Spinbox(self.dns_frame, from_=0.1, to=2.0, increment=0.1, textvariable=self.dns_delay_var, width=10)
        delay_entry.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Start/Stop buttons
        button_frame = ttk.Frame(self.dns_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.start_dns_button = ttk.Button(button_frame, text=self.get_translation("start_dns_scan"), command=self.start_dns_scan)
        self.start_dns_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_dns_button = ttk.Button(button_frame, text=self.get_translation("stop_test"), command=self.stop_test, state=tk.DISABLED)
        self.stop_dns_button.pack(side=tk.LEFT, padx=5)
        
        # Chart/Text view toggle
        view_frame = ttk.Frame(self.dns_frame)
        view_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        self.chart_button = ttk.Button(view_frame, text=self.get_translation("chart_view"), command=lambda: self.toggle_view("dns", "chart"))
        self.chart_button.pack(side=tk.LEFT, padx=5)
        
        self.text_button = ttk.Button(view_frame, text=self.get_translation("text_view"), command=lambda: self.toggle_view("dns", "text"))
        self.text_button.pack(side=tk.LEFT, padx=5)
        
        # Chart container
        self.dns_chart_frame = ttk.Frame(self.dns_frame)
        self.dns_chart_frame.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=10)
    
    def _setup_message_tab(self):
        """Setup message sending tab"""
        # Clear existing widgets
        for widget in self.message_frame.winfo_children():
            widget.destroy()
        
        # Message text field
        self.message = tk.StringVar()
        message_label = ttk.Label(self.message_frame, text=self.get_translation("message_text"))
        message_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        message_entry = ttk.Entry(self.message_frame, textvariable=self.message, width=40)
        message_entry.grid(row=0, column=1, pady=5, padx=5)
        
        # Send count field
        self.count = tk.IntVar(value=1)
        count_label = ttk.Label(self.message_frame, text=self.get_translation("send_count"))
        count_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        count_entry = ttk.Spinbox(self.message_frame, from_=1, to=1000, textvariable=self.count, width=10)
        count_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Delay field
        delay_label = ttk.Label(self.message_frame, text=self.get_translation("message_delay"))
        delay_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        delay_entry = ttk.Spinbox(self.message_frame, from_=0.5, to=10.0, increment=0.5, textvariable=self.delay, width=10)
        delay_entry.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Position button
        position_frame = ttk.Frame(self.message_frame)
        position_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        position_label = ttk.Label(position_frame, text=self.get_translation("input_position"))
        position_label.pack(side=tk.LEFT, padx=5)
        
        self.position_button = ttk.Button(position_frame, text=self.get_translation("set_position"), command=self.set_position)
        self.position_button.pack(side=tk.LEFT, padx=5)
        
        self.position_info = ttk.Label(position_frame, text=self.get_translation("position_not_set"))
        self.position_info.pack(side=tk.LEFT, padx=20)
        
        # Start/Stop buttons
        button_frame = ttk.Frame(self.message_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        self.start_msg_button = ttk.Button(button_frame, text=self.get_translation("start_sending"), command=self.start_sending)
        self.start_msg_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_msg_button = ttk.Button(button_frame, text=self.get_translation("stop_sending"), command=self.stop_test, state=tk.DISABLED)
        self.stop_msg_button.pack(side=tk.LEFT, padx=5)
        
        self.mouse_position = (0, 0)  # Mouse position for sending messages
    
    def browse_wordlist(self):
        """Browse for password list file"""
        filename = filedialog.askopenfilename(
            title=self.get_translation("wordlist"),
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.wordlist.set(filename)
    
    def set_position(self):
        """Set message input position"""
        self.status_label.config(text="Click on the message input area in 3 seconds...")
        self.root.update()
        
        # Delay to give user time to switch to target window
        time.sleep(3)
        
        # Get current cursor position
        self.mouse_position = pyautogui.position()
        self.position_info.config(text=f"Position set: {self.mouse_position}")
        self.status_label.config(text=self.get_translation("ready"))
    
    def emergency_stop(self):
        """Emergency stop using ESC key"""
        if self.is_running:
            self.stop_test()
            messagebox.showinfo(self.get_translation("emergency_stop"), self.get_translation("process_stopped"))
    
    def start_password_test(self):
        """Start password testing"""
        # Validate inputs
        if not self.target.get().strip():
            messagebox.showerror(self.get_translation("error"), self.get_translation("enter_valid_target"))
            return
        
        if not self.wordlist.get().strip():
            messagebox.showerror(self.get_translation("error"), self.get_translation("select_wordlist"))
            return
        
        # Disable start button and enable stop button
        self.start_pw_button.config(state=tk.DISABLED)
        self.stop_pw_button.config(state=tk.NORMAL)
        
        # Set running state
        self.is_running = True
        
        # Start testing in a separate thread
        self.thread = threading.Thread(target=self.password_test)
        self.thread.daemon = True
        self.thread.start()
    
    def password_test(self):
        """Simulate password testing"""
        target = self.target.get()
        username = self.username_entry.get()
        wordlist_path = self.wordlist.get()
        delay = self.delay.get()
        
        try:
            with open(wordlist_path, 'r') as file:
                passwords = file.read().splitlines()
            
            # Setup progress bar
            self.progress["maximum"] = len(passwords)
            self.progress["value"] = 0
            
            self.log_result(f"Starting password test on {target} using {len(passwords)} passwords...")
            
            success_count = 0
            attempt_count = 0
            
            for i, password in enumerate(passwords):
                # Check running state
                if not self.is_running:
                    break
                
                # Update status
                self.status_label.config(text=f"Testing password {i+1} of {len(passwords)}")
                
                # Simulate login attempt
                self.log_result(f"Attempt: {username}:{password}")
                attempt_count += 1
                
                # Simulate random success (for educational purposes only)
                if len(password) > 8 and any(c.isdigit() for c in password) and i > len(passwords) * 0.8:
                    self.log_result(f"[SUCCESS] Found valid password: {username}:{password}", "success")
                    success_count += 1
                    break
                
                # Update progress bar
                self.progress["value"] = i + 1
                self.root.update_idletasks()
                
                # Wait before next attempt
                time.sleep(delay)
            
            if self.is_running:
                self.status_label.config(text="Password testing completed")
                self.is_running = False
                
                # Update chart data
                self.chart_data["password"] = {
                    "labels": ["Success", "Failed"],
                    "values": [success_count, attempt_count - success_count]
                }
                
                # Enable start button and disable stop button
                self.start_pw_button.config(state=tk.NORMAL)
                self.stop_pw_button.config(state=tk.DISABLED)
                
        except Exception as e:
            self.log_result(f"Error: {str(e)}", "error")
            self.is_running = False
            self.start_pw_button.config(state=tk.NORMAL)
            self.stop_pw_button.config(state=tk.DISABLED)
    
    def start_port_scan(self):
        """Start port scanning"""
        # Validate inputs
        if not self.target.get().strip():
            messagebox.showerror(self.get_translation("error"), self.get_translation("enter_valid_target"))
            return
        
        try:
            ipaddress.ip_address(self.target.get())
        except ValueError:
            messagebox.showerror(self.get_translation("error"), self.get_translation("enter_valid_target"))
            return
        
        if self.start_port.get() > self.end_port.get():
            messagebox.showerror(self.get_translation("error"), "Start port must be less than or equal to end port")
            return
        
        # Disable start button and enable stop button
        self.start_port_button.config(state=tk.DISABLED)
        self.stop_port_button.config(state=tk.NORMAL)
        
        # Set running state
        self.is_running = True
        
        # Start scanning in a separate thread
        self.thread = threading.Thread(target=self.port_scan)
        self.thread.daemon = True
        self.thread.start()
    
    def port_scan(self):
        """Scan for open ports"""
        target = self.target.get()
        start_port = self.start_port.get()
        end_port = self.end_port.get()
        delay = self.delay.get()
        
        # Setup progress bar
        total_ports = end_port - start_port + 1
        self.progress["maximum"] = total_ports
        self.progress["value"] = 0
        
        self.log_result(f"Starting port scan on {target} from port {start_port} to {end_port}...")
        
        open_ports = []
        closed_ports = []
        
        for port in range(start_port, end_port + 1):
            # Check running state
            if not self.is_running:
                break
            
            # Update status
            self.status_label.config(text=f"Scanning port {port} of {end_port}")
            
            try:
                # Create socket
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                
                # Try to connect
                result = s.connect_ex((target, port))
                
                # If port is open
                if result == 0:
                    service = self.get_common_service(port)
                    self.log_result(f"Port {port} ({service}): Open", "success")
                    open_ports.append(port)
                else:
                    closed_ports.append(port)
                
                # Close socket
                s.close()
                
            except Exception as e:
                self.log_result(f"Error scanning port {port}: {str(e)}", "error")
                closed_ports.append(port)
            
            # Update progress bar
            self.progress["value"] = port - start_port + 1
            self.root.update_idletasks()
            
            # Wait before next scan
            time.sleep(delay)
        
        if self.is_running:
            self.log_result(f"Port scan completed. Found {len(open_ports)} open ports.")
            self.status_label.config(text="Port scan completed")
            self.is_running = False
            
            # Update chart data
            self.chart_data["port"] = {
                "labels": ["Open", "Closed"],
                "values": [len(open_ports), len(closed_ports)]
            }
            
            # Enable start button and disable stop button
            self.start_port_button.config(state=tk.NORMAL)
            self.stop_port_button.config(state=tk.DISABLED)
    
    def start_sql_injection_test(self):
        """Start SQL injection testing"""
        # Validate inputs
        url = self.sql_url_entry.get().strip()
        param = self.sql_param_entry.get().strip()
        
        if not url:
            messagebox.showerror(self.get_translation("error"), "Please enter a valid URL")
            return
        
        if not param:
            messagebox.showerror(self.get_translation("error"), "Please enter a parameter to test")
            return
        
        # Get payloads
        payloads = self.sql_payloads_text.get("1.0", tk.END).strip().split('\n')
        if not payloads:
            messagebox.showerror(self.get_translation("error"), "Please enter at least one payload")
            return
        
        # Disable start button and enable stop button
        self.start_sql_button.config(state=tk.DISABLED)
        self.stop_sql_button.config(state=tk.NORMAL)
        
        # Set running state
        self.is_running = True
        
        # Start testing in a separate thread
        self.thread = threading.Thread(target=self.sql_injection_test, args=(url, param, payloads))
        self.thread.daemon = True
        self.thread.start()
    
    def sql_injection_test(self, url, param, payloads):
        """Simulate SQL injection testing"""
        delay = self.sql_delay_var.get()
        
        # Setup progress bar
        self.progress["maximum"] = len(payloads)
        self.progress["value"] = 0
        
        self.log_result(f"Starting SQL injection test on {url} with parameter {param}...")
        
        vulnerable_count = 0
        not_vulnerable_count = 0
        error_count = 0
        
        for i, payload in enumerate(payloads):
            # Check running state
            if not self.is_running:
                break
            
            # Update status
            self.status_label.config(text=f"Testing payload {i+1} of {len(payloads)}")
            
            try:
                # Construct test URL
                test_url = f"{url}?{param}={payload}"
                self.log_result(f"Testing: {test_url}")
                
                # Simulate request (for educational purposes only)
                # In a real tool, this would make an actual request and analyze the response
                time.sleep(delay)  # Simulate request time
                
                # Simulate detection (random for demonstration)
                import random
                result = random.choice(["vulnerable", "not_vulnerable", "error"])
                
                if result == "vulnerable":
                    self.log_result(f"[VULNERABLE] Payload: {payload}", "success")
                    vulnerable_count += 1
                elif result == "error":
                    self.log_result(f"[ERROR] Server error with payload: {payload}", "error")
                    error_count += 1
                else:
                    self.log_result(f"[NOT VULNERABLE] Payload: {payload}")
                    not_vulnerable_count += 1
                
            except Exception as e:
                self.log_result(f"Error: {str(e)}", "error")
                error_count += 1
            
            # Update progress bar
            self.progress["value"] = i + 1
            self.root.update_idletasks()
            
            # Wait before next test
            time.sleep(delay)
        
        if self.is_running:
            self.log_result(f"SQL injection test completed. Found {vulnerable_count} potential vulnerabilities.")
            self.status_label.config(text="SQL injection test completed")
            self.is_running = False
            
            # Update chart data
            self.chart_data["sql"] = {
                "labels": ["Vulnerable", "Not Vulnerable", "Error"],
                "values": [vulnerable_count, not_vulnerable_count, error_count]
            }
            
            # Enable start button and disable stop button
            self.start_sql_button.config(state=tk.NORMAL)
            self.stop_sql_button.config(state=tk.DISABLED)
    
    def start_xss_test(self):
        """Start XSS testing"""
        # Validate inputs
        url = self.xss_url_entry.get().strip()
        param = self.xss_param_entry.get().strip()
        
        if not url:
            messagebox.showerror(self.get_translation("error"), "Please enter a valid URL")
            return
        
        if not param:
            messagebox.showerror(self.get_translation("error"), "Please enter a parameter to test")
            return
        
        # Get payloads
        payloads = self.xss_payloads_text.get("1.0", tk.END).strip().split('\n')
        if not payloads:
            messagebox.showerror(self.get_translation("error"), "Please enter at least one payload")
            return
        
        # Disable start button and enable stop button
        self.start_xss_button.config(state=tk.DISABLED)
        self.stop_xss_button.config(state=tk.NORMAL)
        
        # Set running state
        self.is_running = True
        
        # Start testing in a separate thread
        self.thread = threading.Thread(target=self.xss_test, args=(url, param, payloads))
        self.thread.daemon = True
        self.thread.start()
    
    def xss_test(self, url, param, payloads):
        """اختبار ثغرات XSS"""
        delay = self.xss_delay_var.get()
        
        # إعداد شريط التقدم
        self.progress["maximum"] = len(payloads)
        self.progress["value"] = 0
        
        self.log_result(f"بدء اختبار XSS على {url} باستخدام {len(payloads)} نموذج...")
        
        vulnerable_count = 0
        not_vulnerable_count = 0
        error_count = 0
        
        # التحقق من وجود بروتوكول HTTP/HTTPS
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'http://' + url
        
        for i, payload in enumerate(payloads):
            # التحقق من حالة التشغيل
            if not self.is_running:
                break
            
            # تحديث حالة الاختبار
            self.status_label.config(text=f"اختبار نموذج XSS {i+1} من {len(payloads)}")
            
            try:
                # إنشاء URL الاختبار
                test_url = f"{url}?{param}={payload}"
                self.log_result(f"اختبار: {test_url}")
                
                # إرسال الطلب
                response = requests.get(test_url, timeout=5)
                
                # التحقق من وجود النموذج في الاستجابة
                if payload in response.text:
                    self.log_result(f"[ثغرة محتملة] تم العثور على النموذج في الاستجابة: {payload}", "success")
                    vulnerable_count += 1
                else:
                    self.log_result(f"[غير معرض للثغرة] لم يتم العثور على النموذج في الاستجابة")
                    not_vulnerable_count += 1
                    
            except Exception as e:
                self.log_result(f"خطأ أثناء اختبار النموذج: {str(e)}", "error")
                error_count += 1
            
            # تحديث شريط التقدم
            self.progress["value"] = i + 1
            self.root.update_idletasks()
            
            # انتظار قبل الاختبار التالي
            time.sleep(delay)
        
        if self.is_running:
            self.log_result(f"اكتمل اختبار XSS. تم العثور على {vulnerable_count} ثغرة محتملة.")
            self.status_label.config(text="اكتمل اختبار XSS")
            self.is_running = False
            
            # تحديث بيانات الرسم البياني
            self.chart_data["xss"] = {
                "labels": ["معرض للثغرة", "غير معرض للثغرة", "خطأ"],
                "values": [vulnerable_count, not_vulnerable_count, error_count]
            }
            
            # تفعيل زر البدء وتعطيل زر الإيقاف
            self.start_xss_button.config(state=tk.NORMAL)
            self.stop_xss_button.config(state=tk.DISABLED)
    def start_dns_scan(self):
        """Start DNS scanning"""
        # Validate inputs
        domain = self.domain_entry.get().strip()
        
        if not domain:
            messagebox.showerror(self.get_translation("error"), "Please enter a valid domain")
            return
        
        # Check if at least one record type is selected
        selected_records = [record for record, var in self.record_types.items() if var.get()]
        if not selected_records:
            messagebox.showerror(self.get_translation("error"), "Please select at least one record type")
            return
        
        # Disable start button and enable stop button
        self.start_dns_button.config(state=tk.DISABLED)
        self.stop_dns_button.config(state=tk.NORMAL)
        
        # Set running state
        self.is_running = True
        
        # Start scanning in a separate thread
        self.thread = threading.Thread(target=self.dns_scan, args=(domain, selected_records))
        self.thread.daemon = True
        self.thread.start()
    
    def dns_scan(self, domain, record_types):
        """Scan DNS records for a domain"""
        delay = self.dns_delay_var.get()
        
        # Setup progress bar
        self.progress["maximum"] = len(record_types)
        self.progress["value"] = 0
        
        self.log_result(f"Starting DNS scan for {domain} with record types: {', '.join(record_types)}...")
        
        # Import DNS resolver
        try:
            import dns.resolver
        except ImportError:
            self.log_result("Error: dnspython module not found. Please install it using 'pip install dnspython'", "error")
            self.is_running = False
            self.start_dns_button.config(state=tk.NORMAL)
            self.stop_dns_button.config(state=tk.DISABLED)
            return
        
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5
        
        record_counts = {}
        total_records = 0
        
        for i, record_type in enumerate(record_types):
            # Check running state
            if not self.is_running:
                break
            
            # Update status
            self.status_label.config(text=f"Scanning {record_type} records for {domain}")
            
            try:
                # Query DNS records
                answers = resolver.resolve(domain, record_type)
                
                # Log results
                record_count = len(answers)
                record_counts[record_type] = record_count
                total_records += record_count
                
                self.log_result(f"Found {record_count} {record_type} records for {domain}:", "success")
                
                for rdata in answers:
                    if record_type == 'MX':
                        self.log_result(f"  {record_type}: {rdata.exchange} (priority: {rdata.preference})")
                    elif record_type == 'SOA':
                        self.log_result(f"  {record_type}: {rdata.mname} (serial: {rdata.serial})")
                    else:
                        self.log_result(f"  {record_type}: {rdata}")
                
            except dns.resolver.NoAnswer:
                self.log_result(f"No {record_type} records found for {domain}")
                record_counts[record_type] = 0
            except dns.resolver.NXDOMAIN:
                self.log_result(f"Domain {domain} does not exist", "error")
                break
            except Exception as e:
                self.log_result(f"Error querying {record_type} records: {str(e)}", "error")
                record_counts[record_type] = 0
            
            # Update progress bar
            self.progress["value"] = i + 1
            self.root.update_idletasks()
            
            # Wait before next query
            time.sleep(delay)
        
        if self.is_running:
            self.log_result(f"DNS scan completed. Found {total_records} total records across {len(record_types)} record types.")
            self.status_label.config(text="DNS scan completed")
            self.is_running = False
            
            # Update chart data
            self.chart_data["dns"] = {
                "labels": list(record_counts.keys()),
                "values": list(record_counts.values())
            }
            
            # Enable start button and disable stop button
            self.start_dns_button.config(state=tk.NORMAL)
            self.stop_dns_button.config(state=tk.DISABLED)
    def stop_test(self):
        """Stop any running test"""
        self.is_running = False
        self.status_label.config(text=self.get_translation("stopped"))
        
        # Enable all start buttons and disable all stop buttons
        self.start_pw_button.config(state=tk.NORMAL)
        self.stop_pw_button.config(state=tk.DISABLED)
        
        self.start_port_button.config(state=tk.NORMAL)
        self.stop_port_button.config(state=tk.DISABLED)
        
        self.start_sql_button.config(state=tk.NORMAL)
        self.stop_sql_button.config(state=tk.DISABLED)
        
        self.start_xss_button.config(state=tk.NORMAL)
        self.stop_xss_button.config(state=tk.DISABLED)
        
        self.start_dns_button.config(state=tk.NORMAL)
        self.stop_dns_button.config(state=tk.DISABLED)
        
        self.start_msg_button.config(state=tk.NORMAL)
        self.stop_msg_button.config(state=tk.DISABLED)
    def start_sending(self):
        """Start sending messages"""
        # Validate inputs
        if not self.message.get().strip():
            messagebox.showerror(self.get_translation("error"), "Please enter a message")
            return
        
        if self.mouse_position == (0, 0):
            messagebox.showerror(self.get_translation("error"), "Please set the message input position first")
            return
        
        # Disable start button and enable stop button
        self.start_msg_button.config(state=tk.DISABLED)
        self.stop_msg_button.config(state=tk.NORMAL)
        
        # Set running state
        self.is_running = True
        
        # Start sending in a separate thread
        self.thread = threading.Thread(target=self.send_messages)
        self.thread.daemon = True
        self.thread.start()
    
    def send_messages(self):
        """Send messages to the specified position"""
        message = self.message.get()
        count = self.count.get()
        delay = self.delay.get()
        
        # Setup progress bar
        self.progress["maximum"] = count
        self.progress["value"] = 0
        
        self.log_result(f"Starting to send {count} messages: '{message}'...")
        
        try:
            for i in range(count):
                # Check running state
                if not self.is_running:
                    break
                
                # Update status
                self.status_label.config(text=f"Sending message {i+1} of {count}")
                
                # Move cursor to position and type message
                pyautogui.moveTo(self.mouse_position[0], self.mouse_position[1])
                pyautogui.click()
                pyautogui.typewrite(message)
                pyautogui.press('enter')
                
                # Log result
                self.log_result(f"Sent message {i+1}: {message}")
                
                # Update progress bar
                self.progress["value"] = i + 1
                self.root.update_idletasks()
                
                # Wait before next message
                time.sleep(delay)
            
            if self.is_running:
                self.status_label.config(text="Message sending completed")
                self.is_running = False
                
                # Enable start button and disable stop button
                self.start_msg_button.config(state=tk.NORMAL)
                self.stop_msg_button.config(state=tk.DISABLED)
                
        except Exception as e:
            self.log_result(f"Error: {str(e)}", "error")
            self.is_running = False
            self.start_msg_button.config(state=tk.NORMAL)
            self.stop_msg_button.config(state=tk.DISABLED)
    
    def stop_test(self):
        """Stop any running test"""
        self.is_running = False
        self.status_label.config(text=self.get_translation("stopped"))
        
        # Enable all start buttons and disable all stop buttons
        self.start_pw_button.config(state=tk.NORMAL)
        self.stop_pw_button.config(state=tk.DISABLED)
        
        self.start_port_button.config(state=tk.NORMAL)
        self.stop_port_button.config(state=tk.DISABLED)
        
        self.start_sql_button.config(state=tk.NORMAL)
        self.stop_sql_button.config(state=tk.DISABLED)
        
        self.start_xss_button.config(state=tk.NORMAL)
        self.stop_xss_button.config(state=tk.DISABLED)
        
        self.start_dns_button.config(state=tk.NORMAL)
        self.stop_dns_button.config(state=tk.DISABLED)
        
        self.start_msg_button.config(state=tk.NORMAL)
        self.stop_msg_button.config(state=tk.DISABLED)
    
    def log_result(self, message, tag=None):
        """Log result to the results text area"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.insert(tk.END, message + "\n")
        
        # Apply tag if specified
        if tag:
            start_index = self.results_text.index("end-2c linestart")
            end_index = self.results_text.index("end-1c")
            self.results_text.tag_add(tag, start_index, end_index)
        
        self.results_text.config(state=tk.DISABLED)
        self.results_text.see(tk.END)
    
    def get_common_service(self, port):
        """Get common service name for a port"""
        common_services = {
            20: "FTP (Data)",
            21: "FTP (Control)",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            110: "POP3",
            143: "IMAP",
            443: "HTTPS",
            465: "SMTPS",
            587: "SMTP (Submission)",
            993: "IMAPS",
            995: "POP3S",
            3306: "MySQL",
            3389: "RDP"
        }
        return common_services.get(port, "Unknown")
    
    def toggle_view(self, test_type, view_type):
        """Toggle between chart and text view"""
        # Get the chart frame for this test type
        chart_frame = getattr(self, f"{test_type}_chart_frame")
        
        # Clear the chart frame
        for widget in chart_frame.winfo_children():
            widget.destroy()
        
        # If chart data exists for this test type
        if test_type in self.chart_data:
            data = self.chart_data[test_type]
            
            if view_type == "chart":
                # Create a pie chart
                fig, ax = plt.subplots(figsize=(5, 4), facecolor='#2d2d2d')
                
                # Set colors for different test types
                if test_type == "password":
                    colors = ['#4CAF50', '#F44336']  # Green for success, red for failure
                elif test_type == "port":
                    colors = ['#2196F3', '#9E9E9E']  # Blue for open, gray for closed
                elif test_type in ["sql", "xss"]:
                    colors = ['#FF9800', '#4CAF50', '#F44336']  # Orange for vulnerable, green for safe, red for error
                else:  # DNS
                    colors = plt.cm.tab20.colors  # Multiple colors
                
                # Create the pie chart
                wedges, texts, autotexts = ax.pie(
                    data["values"], 
                    labels=data["labels"], 
                    autopct='%1.1f%%',
                    colors=colors,
                    startangle=90,
                    wedgeprops={'linewidth': 1, 'edgecolor': 'white'},
                    textprops={'color': 'white'}
                )
                
                # Set title with white text
                ax.set_title(f"{test_type.upper()} Test Results", color='white')
                
                # Create canvas and add to frame
                canvas = FigureCanvasTkAgg(fig, master=chart_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
            else:  # Text view
                # Create a text widget
                text_widget = tk.Text(chart_frame, bg="#2d2d2d", fg="white", height=10)
                text_widget.pack(fill=tk.BOTH, expand=True)
                
                # Add data to text widget
                for label, value in zip(data["labels"], data["values"]):
                    text_widget.insert(tk.END, f"{label}: {value}\n")
                
                text_widget.config(state=tk.DISABLED)
    
    def save_results(self):
        """Save test results to a file"""
        filename = filedialog.asksaveasfilename(
            title=self.get_translation("save_results"),
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            defaultextension=".txt"
        )
        
        if filename:
            try:
                with open(filename, "w") as file:
                    # Get all results from the text widget
                    content = self.results_text.get("1.0", tk.END)
                    file.write(content)
                
                self.log_result(f"Results saved to: {filename}", "success")
            except Exception as e:
                messagebox.showerror(self.get_translation("error"), f"Failed to save results: {str(e)}")
    
    def load_results(self):
        """Load test results from a file"""
        filename = filedialog.askopenfilename(
            title=self.get_translation("load_results"),
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, "r") as file:
                    content = file.read()
                
                self.results_text.config(state=tk.NORMAL)
                self.results_text.delete("1.0", tk.END)
                self.results_text.insert(tk.END, content)
                self.results_text.config(state=tk.DISABLED)
                
                self.log_result(f"Results loaded from: {filename}", "success")
            except Exception as e:
                messagebox.showerror(self.get_translation("error"), f"Failed to load results: {str(e)}")

# Create the main window
if __name__ == "__main__":
    root = tk.Tk()
    app = PenTestApp(root)
    root.mainloop()