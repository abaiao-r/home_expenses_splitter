from typing import List
from expense import Expense

class Person:
    def __init__(self, name: str, pays_for_two: bool = False):
        self.name = name
        self.pays_for_two = pays_for_two
        self.expenses: List[Expense] = []

    def add_expense(self, expense: Expense):
        self.expenses.append(expense)

    def total_expenses(self) -> float:
        return sum(expense.value for expense in self.expenses)

    def to_dict(self):
        return {
            "name": self.name,
            "pays_for_two": self.pays_for_two,
            "expenses": [expense.to_dict() for expense in self.expenses]
        }

    @classmethod
    def from_dict(cls, data):
        person = cls(name=data["name"], pays_for_two=data["pays_for_two"])
        person.expenses = [Expense.from_dict(expense) for expense in data["expenses"]]
        return person
