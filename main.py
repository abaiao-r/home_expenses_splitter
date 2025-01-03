import subprocess
import sys
import json
from datetime import datetime

try:
    from prettytable import PrettyTable
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "prettytable"])
    from prettytable import PrettyTable

from person import Person
from expense import Expense
from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar

class ExpenseManager:
    def __init__(self):
        self.persons = []

    def add_person(self, name: str, pays_for_two: bool = False):
        if any(person.name == name for person in self.persons):
            raise ValueError(f"Person {name} already exists.")
        person = Person(name, pays_for_two)
        self.persons.append(person)

    def add_expense(self, person_name: str, invoice_id: str, description: str, value: float, expense_date: date):
        person = next((p for p in self.persons if p.name == person_name), None)
        if person:
            expense = Expense(invoice_id, description, value, expense_date)
            person.add_expense(expense)

    def get_expenses_by_month(self):
        expenses_by_month = {}
        for person in self.persons:
            for expense in person.expenses:
                month = expense.expense_date.strftime("%b %Y").upper()
                if month not in expenses_by_month:
                    expenses_by_month[month] = []
                expenses_by_month[month].append(expense)
        return expenses_by_month

    def calculate_totals(self):
        if not self.persons:
            raise ValueError("No persons available to calculate totals.")
        
        expenses_by_month = self.get_expenses_by_month()
        totals_by_month = {}
        balances_by_month = {}

        for month, expenses in expenses_by_month.items():
            total_expenses = sum(expense.value for expense in expenses)
            num_persons = sum(2 if person.pays_for_two else 1 for person in self.persons)
            split_amount = total_expenses / num_persons

            totals = []
            balances = {}
            for person in self.persons:
                total_paid = sum(expense.value for expense in person.expenses if expense.expense_date.strftime("%b %Y").upper() == month)
                should_pay = split_amount * (2 if person.pays_for_two else 1)
                difference = total_paid - should_pay
                totals.append((person.name, total_paid, should_pay, difference))
                balances[person.name] = difference

            totals_by_month[month] = totals
            balances_by_month[month] = balances

        return totals_by_month, balances_by_month

    def calculate_settlements(self, balances_by_month):
        settlements_by_month = {}
        for month, balances in balances_by_month.items():
            settlements = []
            creditors = [(name, balance) for name, balance in balances.items() if balance > 0]
            debtors = [(name, -balance) for name, balance in balances.items() if balance < 0]

            creditors.sort(key=lambda x: x[1], reverse=True)
            debtors.sort(key=lambda x: x[1], reverse=True)

            while creditors and debtors:
                creditor_name, creditor_balance = creditors.pop(0)
                debtor_name, debtor_balance = debtors.pop(0)

                amount = min(creditor_balance, debtor_balance)
                settlements.append((debtor_name, creditor_name, amount))

                if creditor_balance > debtor_balance:
                    creditors.insert(0, (creditor_name, creditor_balance - amount))
                elif debtor_balance > creditor_balance:
                    debtors.insert(0, (debtor_name, debtor_balance - amount))

            settlements_by_month[month] = settlements

        return settlements_by_month

    def save_data(self, filepath):
        data = [person.to_dict() for person in self.persons]
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)

    def load_data(self, filepath):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                self.persons = [Person.from_dict(person) for person in data]
        except FileNotFoundError:
            self.persons = []

    def delete_person(self, name: str):
        self.persons = [person for person in self.persons if person.name != name]

    def erase_all_data(self):
        self.persons = []

class ExpenseApp:
    def __init__(self, root):
        self.manager = ExpenseManager()
        self.root = root
        self.root.title("Expense Manager")

        self.data_filepath = "expenses_data.json"
        self.manager.load_data(self.data_filepath)

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10 10 10 10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        self.person_listbox = tk.Listbox(main_frame, height=10)
        self.person_listbox.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
        self.person_listbox.bind('<<ListboxSelect>>', self.on_person_select)

        self.add_person_button = ttk.Button(main_frame, text="Add Person", command=self.show_add_person_window)
        self.add_person_button.grid(row=1, column=0, padx=5, pady=5)

        self.erase_all_button = ttk.Button(main_frame, text="Erase All", command=self.erase_all_data)
        self.erase_all_button.grid(row=1, column=1, padx=5, pady=5)

        self.view_totals_button = ttk.Button(main_frame, text="View Totals", command=self.show_totals_window)
        self.view_totals_button.grid(row=2, column=0, columnspan=4, padx=5, pady=5)

        self.month_var = tk.StringVar()
        self.month_dropdown = ttk.Combobox(main_frame, textvariable=self.month_var)
        self.month_dropdown.grid(row=3, column=0, columnspan=4, padx=5, pady=5)
        self.month_dropdown.bind("<<ComboboxSelected>>", self.update_month_selection)

        self.update_person_listbox()
        self.update_month_dropdown()

    def update_person_listbox(self):
        self.person_listbox.delete(0, tk.END)
        if not self.manager.persons:
            self.person_listbox.insert(tk.END, "No users available.")
        else:
            for person in self.manager.persons:
                self.person_listbox.insert(tk.END, person.name)

    def update_month_dropdown(self):
        expenses_by_month = self.manager.get_expenses_by_month()
        months = sorted(expenses_by_month.keys(), key=lambda x: datetime.strptime(x, "%b %Y"))
        self.month_dropdown['values'] = months
        if months:
            self.month_var.set(months[0])

    def show_add_person_window(self):
        self.add_person_window = tk.Toplevel(self.root)
        self.add_person_window.title("Add Person")

        add_person_frame = ttk.Frame(self.add_person_window, padding="10 10 10 10")
        add_person_frame.grid(row=0, column=0, sticky="nsew")

        self.name_label = ttk.Label(add_person_frame, text="Name:")
        self.name_label.grid(row=0, column=0, padx=5, pady=5)
        self.name_entry = ttk.Entry(add_person_frame)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)

        self.pays_for_two_var = tk.BooleanVar()
        self.pays_for_two_check = ttk.Checkbutton(add_person_frame, text="Pays for Two", variable=self.pays_for_two_var)
        self.pays_for_two_check.grid(row=0, column=2, padx=5, pady=5)

        self.add_person_button = ttk.Button(add_person_frame, text="Add Person", command=self.add_person)
        self.add_person_button.grid(row=1, column=0, columnspan=3, padx=5, pady=5)

    def add_person(self):
        name = self.name_entry.get()
        pays_for_two = self.pays_for_two_var.get()
        if name:
            try:
                self.manager.add_person(name, pays_for_two)
                self.update_person_listbox()
                self.update_month_dropdown()
                self.manager.save_data(self.data_filepath)
                self.add_person_window.destroy()
                messagebox.showinfo("Success", f"Person {name} added successfully!")
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showerror("Error", "Name cannot be empty.")

    def on_person_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            person_name = event.widget.get(index)
            if person_name != "No users available.":
                self.show_person_options_window(person_name)

    def show_person_options_window(self, person_name):
        self.person_options_window = tk.Toplevel(self.root)
        self.person_options_window.title(f"Options for {person_name}")

        options_frame = ttk.Frame(self.person_options_window, padding="10 10 10 10")
        options_frame.grid(row=0, column=0, sticky="nsew")

        self.add_expense_button = ttk.Button(options_frame, text="Add Expense", command=lambda: self.show_add_expense_window(person_name))
        self.add_expense_button.grid(row=0, column=0, padx=5, pady=5)

        self.view_expenses_button = ttk.Button(options_frame, text="View Expenses", command=lambda: self.show_view_expenses_window(person_name))
        self.view_expenses_button.grid(row=0, column=1, padx=5, pady=5)

        self.edit_person_button = ttk.Button(options_frame, text="Edit User Name", command=lambda: self.show_edit_person_window(person_name))
        self.edit_person_button.grid(row=1, column=0, padx=5, pady=5)

        self.delete_person_button = ttk.Button(options_frame, text="Delete User", command=lambda: self.delete_person(person_name))
        self.delete_person_button.grid(row=1, column=1, padx=5, pady=5)

    def show_edit_person_window(self, person_name):
        self.edit_person_window = tk.Toplevel(self.root)
        self.edit_person_window.title(f"Edit Person: {person_name}")

        edit_person_frame = ttk.Frame(self.edit_person_window, padding="10 10 10 10")
        edit_person_frame.grid(row=0, column=0, sticky="nsew")

        self.edit_name_label = ttk.Label(edit_person_frame, text="Name:")
        self.edit_name_label.grid(row=0, column=0, padx=5, pady=5)
        self.edit_name_entry = ttk.Entry(edit_person_frame)
        self.edit_name_entry.grid(row=0, column=1, padx=5, pady=5)
        self.edit_name_entry.insert(0, person_name)

        self.edit_pays_for_two_var = tk.BooleanVar()
        person = next((p for p in self.manager.persons if p.name == person_name), None)
        self.edit_pays_for_two_check = ttk.Checkbutton(edit_person_frame, text="Pays for Two", variable=self.edit_pays_for_two_var)
        self.edit_pays_for_two_check.grid(row=0, column=2, padx=5, pady=5)
        self.edit_pays_for_two_var.set(person.pays_for_two)

        self.save_person_button = ttk.Button(edit_person_frame, text="Save", command=lambda: self.save_person(person_name))
        self.save_person_button.grid(row=1, column=0, columnspan=3, padx=5, pady=5)

    def save_person(self, old_name):
        new_name = self.edit_name_entry.get()
        pays_for_two = self.edit_pays_for_two_var.get()
        if new_name:
            try:
                person = next((p for p in self.manager.persons if p.name == old_name), None)
                person.name = new_name
                person.pays_for_two = pays_for_two
                self.update_person_listbox()
                self.update_month_dropdown()
                self.manager.save_data(self.data_filepath)
                self.edit_person_window.destroy()
                self.person_options_window.destroy()
                messagebox.showinfo("Success", f"Person {new_name} updated successfully!")
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showerror("Error", "Name cannot be empty.")

    def delete_person(self, person_name):
        self.manager.delete_person(person_name)
        self.update_person_listbox()
        self.update_month_dropdown()
        self.manager.save_data(self.data_filepath)
        self.person_options_window.destroy()
        messagebox.showinfo("Success", f"Person {person_name} deleted successfully!")

    def erase_all_data(self):
        self.manager.erase_all_data()
        self.update_person_listbox()
        self.update_month_dropdown()
        self.manager.save_data(self.data_filepath)
        messagebox.showinfo("Success", "All data erased successfully!")

    def show_add_expense_window(self, person_name):
        self.add_expense_window = tk.Toplevel(self.root)
        self.add_expense_window.title(f"Add Expense for {person_name}")

        add_expense_frame = ttk.Frame(self.add_expense_window, padding="10 10 10 10")
        add_expense_frame.grid(row=0, column=0, sticky="nsew")

        self.invoice_id_label = ttk.Label(add_expense_frame, text="Invoice ID:")
        self.invoice_id_label.grid(row=0, column=0, padx=5, pady=5)
        self.invoice_id_entry = ttk.Entry(add_expense_frame)
        self.invoice_id_entry.grid(row=0, column=1, padx=5, pady=5)

        self.description_label = ttk.Label(add_expense_frame, text="Description:")
        self.description_label.grid(row=1, column=0, padx=5, pady=5)
        self.description_entry = ttk.Entry(add_expense_frame)
        self.description_entry.grid(row=1, column=1, padx=5, pady=5)

        self.value_label = ttk.Label(add_expense_frame, text="Value (€):")
        self.value_label.grid(row=2, column=0, padx=5, pady=5)
        self.value_entry = ttk.Entry(add_expense_frame)
        self.value_entry.grid(row=2, column=1, padx=5, pady=5)

        self.date_label = ttk.Label(add_expense_frame, text="Date:")
        self.date_label.grid(row=3, column=0, padx=5, pady=5)
        self.date_entry = ttk.Entry(add_expense_frame)
        self.date_entry.grid(row=3, column=1, padx=5, pady=5)
        self.date_button = ttk.Button(add_expense_frame, text="Select Date", command=self.show_date_picker)
        self.date_button.grid(row=3, column=2, padx=5, pady=5)

        self.add_expense_button = ttk.Button(add_expense_frame, text="Add Expense", command=lambda: self.add_expense(person_name))
        self.add_expense_button.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

    def show_date_picker(self):
        self.date_picker_window = tk.Toplevel(self.root)
        self.date_picker_window.title("Select Date")

        self.calendar = Calendar(self.date_picker_window, selectmode='day', date_pattern='yyyy-mm-dd')
        self.calendar.pack(padx=10, pady=10)

        select_button = ttk.Button(self.date_picker_window, text="Select", command=self.select_date)
        select_button.pack(pady=5)

    def select_date(self):
        selected_date = self.calendar.get_date()
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, selected_date)
        self.date_picker_window.destroy()

    def add_expense(self, person_name):
        invoice_id = self.invoice_id_entry.get()
        description = self.description_entry.get()
        value = self.value_entry.get()
        expense_date = self.date_entry.get()

        try:
            value = float(value)
            expense_date = datetime.strptime(expense_date, '%Y-%m-%d').date()
            self.manager.add_expense(person_name, invoice_id, description, value, expense_date)
            self.update_month_dropdown()
            self.manager.save_data(self.data_filepath)
            self.add_expense_window.destroy()
            self.person_options_window.destroy()
            messagebox.showinfo("Success", f"Expense added successfully for {person_name}!")
        except ValueError:
            messagebox.showerror("Error", "Invalid value or date format.")

    def show_view_expenses_window(self, person_name):
        self.view_expenses_window = tk.Toplevel(self.root)
        self.view_expenses_window.title(f"View Expenses for {person_name}")

        view_expenses_frame = ttk.Frame(self.view_expenses_window, padding="10 10 10 10")
        view_expenses_frame.grid(row=0, column=0, sticky="nsew")

        self.expense_month_var = tk.StringVar()
        self.expense_month_dropdown = ttk.Combobox(view_expenses_frame, textvariable=self.expense_month_var)
        self.expense_month_dropdown.grid(row=0, column=0, padx=5, pady=5)
        self.expense_month_dropdown.bind("<<ComboboxSelected>>", lambda event: self.update_expense_list(person_name))

        expenses_by_month = self.manager.get_expenses_by_month()
        months = sorted(expenses_by_month.keys(), key=lambda x: datetime.strptime(x, "%b %Y"))
        self.expense_month_dropdown['values'] = months
        if months:
            self.expense_month_var.set(months[0])

        self.expense_listbox = tk.Listbox(view_expenses_frame, height=10)
        self.expense_listbox.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.expense_listbox.bind('<<ListboxSelect>>', lambda event: self.show_edit_expense_window(person_name))

        self.update_expense_list(person_name)

    def update_expense_list(self, person_name):
        selected_month = self.expense_month_var.get()
        person = next((p for p in self.manager.persons if p.name == person_name), None)
        if person:
            self.expense_listbox.delete(0, tk.END)
            expenses = [expense for expense in person.expenses if expense.expense_date.strftime("%b %Y").upper() == selected_month]
            for expense in expenses:
                self.expense_listbox.insert(tk.END, f"{expense.expense_date}: {expense.description} - {expense.value}€")

    def show_edit_expense_window(self, person_name):
        selection = self.expense_listbox.curselection()
        if selection:
            index = selection[0]
            selected_month = self.expense_month_var.get()
            person = next((p for p in self.manager.persons if p.name == person_name), None)
            if person:
                expenses = [expense for expense in person.expenses if expense.expense_date.strftime("%b %Y").upper() == selected_month]
                expense = expenses[index]

                self.edit_expense_window = tk.Toplevel(self.root)
                self.edit_expense_window.title(f"Edit Expense for {person_name}")

                edit_expense_frame = ttk.Frame(self.edit_expense_window, padding="10 10 10 10")
                edit_expense_frame.grid(row=0, column=0, sticky="nsew")

                self.edit_invoice_id_label = ttk.Label(edit_expense_frame, text="Invoice ID:")
                self.edit_invoice_id_label.grid(row=0, column=0, padx=5, pady=5)
                self.edit_invoice_id_entry = ttk.Entry(edit_expense_frame)
                self.edit_invoice_id_entry.grid(row=0, column=1, padx=5, pady=5)
                self.edit_invoice_id_entry.insert(0, expense.invoice_id)

                self.edit_description_label = ttk.Label(edit_expense_frame, text="Description:")
                self.edit_description_label.grid(row=1, column=0, padx=5, pady=5)
                self.edit_description_entry = ttk.Entry(edit_expense_frame)
                self.edit_description_entry.grid(row=1, column=1, padx=5, pady=5)
                self.edit_description_entry.insert(0, expense.description)

                self.edit_value_label = ttk.Label(edit_expense_frame, text="Value (€):")
                self.edit_value_label.grid(row=2, column=0, padx=5, pady=5)
                self.edit_value_entry = ttk.Entry(edit_expense_frame)
                self.edit_value_entry.grid(row=2, column=1, padx=5, pady=5)
                self.edit_value_entry.insert(0, expense.value)

                self.edit_date_label = ttk.Label(edit_expense_frame, text="Date:")
                self.edit_date_label.grid(row=3, column=0, padx=5, pady=5)
                self.edit_date_entry = ttk.Entry(edit_expense_frame)
                self.edit_date_entry.grid(row=3, column=1, padx=5, pady=5)
                self.edit_date_button = ttk.Button(edit_expense_frame, text="Select Date", command=self.show_edit_date_picker)
                self.edit_date_button.grid(row=3, column=2, padx=5, pady=5)

                self.save_expense_button = ttk.Button(edit_expense_frame, text="Save", command=lambda: self.save_expense(person_name, expense))
                self.save_expense_button.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

    def show_edit_date_picker(self):
        self.edit_date_picker_window = tk.Toplevel(self.root)
        self.edit_date_picker_window.title("Select Date")

        self.edit_calendar = Calendar(self.edit_date_picker_window, selectmode='day', date_pattern='yyyy-mm-dd')
        self.edit_calendar.pack(padx=10, pady=10)

        select_button = ttk.Button(self.edit_date_picker_window, text="Select", command=self.select_edit_date)
        select_button.pack(pady=5)

    def select_edit_date(self):
        selected_date = self.edit_calendar.get_date()
        self.edit_date_entry.delete(0, tk.END)
        self.edit_date_entry.insert(0, selected_date)
        self.edit_date_picker_window.destroy()

    def save_expense(self, person_name, expense):
        invoice_id = self.edit_invoice_id_entry.get()
        description = self.edit_description_entry.get()
        value = self.edit_value_entry.get()
        expense_date = self.edit_date_entry.get()

        try:
            expense.invoice_id = invoice_id
            expense.description = description
            expense.value = float(value)
            expense.expense_date = datetime.strptime(expense_date, '%Y-%m-%d').date()
            self.edit_expense_window.destroy()
            self.update_expense_list(person_name)
            self.manager.save_data(self.data_filepath)
            messagebox.showinfo("Success", "Expense updated successfully!")
        except ValueError:
            messagebox.showerror("Error", "Invalid value or date format.")

    def update_month_selection(self, event):
        selected_month = self.month_var.get()
        self.show_totals_for_month(selected_month)

    def show_totals_for_month(self, month):
        try:
            totals_by_month, balances_by_month = self.manager.calculate_totals()
            settlements_by_month = self.manager.calculate_settlements(balances_by_month)
            totals = totals_by_month.get(month, [])
            settlements = settlements_by_month.get(month, [])

            self.totals_window = tk.Toplevel(self.root)
            self.totals_window.title(f"Totals for {month}")

            totals_frame = ttk.Frame(self.totals_window, padding="10 10 10 10")
            totals_frame.grid(row=0, column=0, sticky="nsew")

            style = ttk.Style()
            style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))

            tree = ttk.Treeview(totals_frame, columns=("Name", "Total Paid", "Total to be Received/Paid"), show="headings")
            tree.heading("Name", text="Name")
            tree.heading("Total Paid", text="Total Paid")
            tree.heading("Total to be Received/Paid", text="Total to be Received/Paid")

            for total in totals:
                name, total_paid, should_pay, difference = total
                color = "green" if difference > 0 else "red"
                tree.insert("", tk.END, values=(name, total_paid, difference), tags=(color,))

            tree.tag_configure("green", foreground="green")
            tree.tag_configure("red", foreground="red")

            tree.pack(fill=tk.BOTH, expand=True)

            total_expenses = sum(total[1] for total in totals)
            total_label = ttk.Label(totals_frame, text=f"Total Expenses: {total_expenses}€")
            total_label.pack(pady=5)

            settlements_label = ttk.Label(totals_frame, text="Settlements:")
            settlements_label.pack(pady=5)

            settlements_str = "\n".join([f"{debtor} should pay {creditor} {amount}€" for debtor, creditor, amount in settlements])
            settlements_text = tk.Text(totals_frame, height=10, wrap=tk.WORD)
            settlements_text.insert(tk.END, settlements_str)
            settlements_text.config(state=tk.DISABLED)
            settlements_text.pack(fill=tk.BOTH, expand=True)
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def show_totals_window(self):
        selected_month = self.month_var.get()
        self.show_totals_for_month(selected_month)

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseApp(root)
    root.mainloop()
