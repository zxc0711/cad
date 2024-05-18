import os
import sqlite3
from PyPDF2 import PdfFileReader
from docx import Document as DocxDocument
from tkinter import filedialog
from tkinter import messagebox
import tkinter as tk
import customtkinter as ctk
from datetime import datetime

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password


class Document:
    def __init__(self, name, content, added_by, timestamp):
        self.name = name
        self.content = content
        self.added_by = added_by
        self.timestamp = timestamp


class SedSystem:
    def __init__(self):
        self.conn = sqlite3.connect('sed_database.db')
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.users = []
        self.documents = []
        self.current_user = None

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                          id INTEGER PRIMARY KEY,
                          username TEXT NOT NULL,
                          password TEXT NOT NULL)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS documents (
                          id INTEGER PRIMARY KEY,
                          name TEXT NOT NULL,
                          content TEXT NOT NULL,
                          added_by INTEGER NOT NULL,
                          timestamp TEXT NOT NULL,
                          FOREIGN KEY (added_by) REFERENCES users(id))''')
        self.conn.commit()

    def register_user(self, username, password):
        try:
            self.cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            row = self.cursor.fetchone()
            if row:
                messagebox.showerror("Ошибка", "Пользователь с таким именем уже существует.")
                return False
            self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            self.conn.commit()
            messagebox.showinfo("Успех", "Регистрация успешно завершена.")
            return True
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
            return False

    def login_user(self, username, password):
        try:
            self.cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            row = self.cursor.fetchone()
            if row:
                self.current_user = User(row[1], row[2])
                messagebox.showinfo("Успех", f"Добро пожаловать, {username}!")
                return True
            messagebox.showerror("Ошибка", "Неверное имя пользователя или пароль.")
            return False
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
            return False

    def logout_user(self):
        self.current_user = None
        messagebox.showinfo("Успех", "Выход выполнен успешно.")

    def add_document(self, name, content, attachment_path=None):
        try:
            if attachment_path:
                # Определение типа файла и чтение его содержимого
                file_extension = os.path.splitext(attachment_path)[1].lower()
                if file_extension == ".pdf":
                    with open(attachment_path, "rb") as f:
                        pdf_reader = PdfFileReader(f)
                        for page_num in range(pdf_reader.numPages):
                            content += pdf_reader.getPage(page_num).extractText()

                elif file_extension == ".docx":
                    docx_doc = DocxDocument(attachment_path)
                    for paragraph in docx_doc.paragraphs:
                        content += paragraph.text

                # Удаление временного файла после чтения содержимого
                os.remove(attachment_path)

            # Добавление документа в базу данных
            self.cursor.execute("INSERT INTO documents (name, content, added_by, timestamp) VALUES (?, ?, ?, ?)",
                                (name, content, self.current_user.id, datetime.now()))
            self.conn.commit()
            messagebox.showinfo("Успех", "Документ добавлен.")
            return True
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
            return False

    def search_document(self, keyword):
        try:
            self.cursor.execute("SELECT * FROM documents WHERE content LIKE ?", ('%' + keyword + '%',))
            found_documents = self.cursor.fetchall()
            if found_documents:
                return found_documents
            else:
                messagebox.showinfo("Информация", "Документы не найдены.")
                return None
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
            return None


def register():
    username = register_username_entry.get()
    password = register_password_entry.get()
    sed.register_user(username, password)
    status_label.configure(text="")


def login():
    username = login_username_entry.get()
    password = login_password_entry.get()
    if sed.login_user(username, password):
        login_window.destroy()
        main_window.deiconify()


def logout():
    sed.logout_user()
    main_window.withdraw()
    login_window.deiconify()
    status_label.configure(text="")


def add_document(name, content, attachment_path=None):
    sed.add_document(name, content, attachment_path)
    refresh_document_list()


def search_document():
    keyword = search_entry.get()
    found_docs = sed.search_document(keyword)
    if found_docs:
        result_text.configure(state=tk.NORMAL)
        result_text.delete("1.0", tk.END)
        for doc in found_docs:
            result_text.insert(tk.END, f"ID: {doc[0]}, Название: {doc[1]}, Добавлен: {doc[4]}\n\n{doc[2]}\n\n")
        result_text.configure(state=tk.DISABLED)
        status_label.configure(text="Документы найдены.")


def refresh_document_list():
    result_text.configure(state=tk.NORMAL)
    result_text.delete("1.0", tk.END)
    sed.cursor.execute("SELECT * FROM documents")
    documents = sed.cursor.fetchall()
    for doc in documents:
        result_text.insert(tk.END, f"ID: {doc[0]}, Название: {doc[1]}, Добавлен: {doc[4]}\n\n{doc[2]}\n\n")
    result_text.configure(state=tk.DISABLED)
    status_label.configure(text="Документы загружены.")

def attach_file():
    attachment_path = filedialog.askopenfilename()
    attachment_label.configure(text=os.path.basename(attachment_path))

sed = SedSystem()

# Создание главного окна и окна входа
main_window = ctk.CTk()
main_window.title("Система электронного документооборота")
main_window.withdraw()

login_window = ctk.CTk()
login_window.title("Вход")

# Фреймы в окне входа
register_frame = ctk.CTkFrame(login_window)
register_frame.pack(padx=20, pady=10)

login_frame = ctk.CTkFrame(login_window)
login_frame.pack(padx=20, pady=10)

# Регистрация пользователя
register_label = ctk.CTkLabel(register_frame, text="Регистрация")
register_label.pack()

register_username_label = ctk.CTkLabel(register_frame, text="Имя пользователя:")
register_username_label.pack(anchor=ctk.W)
register_username_entry = ctk.CTkEntry(register_frame)
register_username_entry.pack()

register_password_label = ctk.CTkLabel(register_frame, text="Пароль:")
register_password_label.pack(anchor=ctk.W)
register_password_entry = ctk.CTkEntry(register_frame, show="*")
register_password_entry.pack()

register_button = ctk.CTkButton(register_frame, text="Зарегистрироваться", command=register)
register_button.pack(pady=5)

# Вход пользователя
login_label = ctk.CTkLabel(login_frame, text="Вход")
login_label.pack()

login_username_label = ctk.CTkLabel(login_frame, text="Имя пользователя:")
login_username_label.pack(anchor=ctk.W)
login_username_entry = ctk.CTkEntry(login_frame)
login_username_entry.pack()

login_password_label = ctk.CTkLabel(login_frame, text="Пароль:")
login_password_label.pack(anchor=ctk.W)
login_password_entry = ctk.CTkEntry(login_frame, show="*")
login_password_entry.pack()

login_button = ctk.CTkButton(login_frame, text="Войти", command=login)
login_button.pack(pady=5)

# Основной интерфейс
# Ввод имени документа
name_label = ctk.CTkLabel(main_window, text="Имя документа:")
name_label.pack(anchor=ctk.W)
name_entry = ctk.CTkEntry(main_window, width=50)
name_entry.pack()

# Ввод содержания документа
content_label = ctk.CTkLabel(main_window, text="Содержание:")
content_label.pack(anchor=ctk.W)

# Создание виджета Text для ввода содержания документа
content_text = tk.Text(main_window, width=50, height=10)
content_text.pack()

# Создание прокрутки для текстового поля
content_scrollbar = ctk.CTkScrollbar(main_window, command=content_text.yview)
content_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
content_text.configure(yscrollcommand=content_scrollbar.set)

# Кнопка добавления документа
add_button = ctk.CTkButton(main_window, text="Добавить документ", command=lambda: add_document(name_entry.get(), content_text.get("1.0", tk.END), attachment_label.cget("text")))
add_button.pack(pady=5)

# Поиск документа
search_label = ctk.CTkLabel(main_window, text="Поиск документа по ключевому слову:")
search_label.pack(anchor=ctk.W)

search_entry = ctk.CTkEntry(main_window, width=40)
search_entry.pack(anchor=ctk.W)

search_button = ctk.CTkButton(main_window, text="Найти", command=search_document)
search_button.pack(anchor=ctk.E)

# Результаты поиска
result_text = tk.Text(main_window, width=50, height=10)
result_text.pack()

# Создание прокрутки для текстового поля с результатами поиска
result_scrollbar = ctk.CTkScrollbar(main_window, command=result_text.yview)
result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
result_text.configure(yscrollcommand=result_scrollbar.set)

# Кнопка выхода
logout_button = ctk.CTkButton(main_window, text="Выход", command=logout)
logout_button.pack()

# Статусная метка
status_label = ctk.CTkLabel(main_window, text="")
status_label.pack(side=tk.BOTTOM, fill=tk.X)

# Метка для отображения имени прикрепленного файла
attachment_label = ctk.CTkLabel(main_window, text="")
attachment_label.pack(anchor=ctk.W)

# Кнопка для прикрепления файла
attach_button = ctk.CTkButton(main_window, text="Прикрепить файл", command=attach_file)
attach_button.pack(anchor=ctk.E)

login_window.mainloop()
main_window.mainloop()
