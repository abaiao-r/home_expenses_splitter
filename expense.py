import uuid
from datetime import date

class Expense:
    def __init__(self, invoice_id: str, description: str, value: float, expense_date: date):
        self.id = uuid.uuid4()
        self.invoice_id = invoice_id
        self.description = description
        self.value = value
        self.expense_date = expense_date

    def to_dict(self):
        return {
            "id": str(self.id),
            "invoice_id": self.invoice_id,
            "description": self.description,
            "value": self.value,
            "expense_date": self.expense_date.isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        expense = cls(
            invoice_id=data["invoice_id"],
            description=data["description"],
            value=data["value"],
            expense_date=date.fromisoformat(data["expense_date"])
        )
        expense.id = uuid.UUID(data["id"])
        return expense