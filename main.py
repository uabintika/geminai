import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import date

app = FastAPI()

# Models

class Account(BaseModel):
    id: int
    person_name: str
    address: str

class Payment(BaseModel):
    id: int
    from_account_id: int
    to_account_id: int
    amount_in_euros: int
    payment_date: date

class ReportEntry(BaseModel):
    from_person_name: str
    to_person_name: str
    amount_in_euros: int
    payment: str

# File setup

if not os.path.exists("accounts.txt"):
    open("accounts.txt", "w").close()

if not os.path.exists("payments.txt"):
    open("payments.txt", "w").close()

# Accounts

def write_account_to_file(account: Account):
    with open("accounts.txt", "a") as file:
        file.write(f"{account.id},{account.person_name},{account.address}\n")

def read_accounts_from_file() -> List[Account]:
    accounts = []
    with open("accounts.txt", "r") as file:
        for line in file:
            if line.strip():
                id, person_name, address = line.strip().split(",", 3)
                accounts.append(Account(id=int(id), person_name=person_name, address=address))
    return accounts

def delete_account_from_file(account_id: int):
    accounts = read_accounts_from_file()
    updated_accounts = [acc for acc in accounts if acc.id != account_id]
    with open("accounts.txt", "w") as file:
        for acc in updated_accounts:
            file.write(f"{acc.id},{acc.person_name},{acc.address}\n")

@app.post("/accounts/")
def create_account(account: Account):
    accounts = read_accounts_from_file()
    if any(a.id == account.id for a in accounts):
        raise HTTPException(status_code=400, detail="Account with this ID already exists.")
    write_account_to_file(account)
    return {"message": "Account created"}

@app.get("/accounts/")
def get_accounts():
    return read_accounts_from_file()

@app.get("/accounts/{account_id}")
def get_account(account_id: int):
    for acc in read_accounts_from_file():
        if acc.id == account_id:
            return acc
    raise HTTPException(status_code=404, detail="Account not found")

@app.delete("/accounts/{account_id}")
def delete_account(account_id: int):
    delete_account_from_file(account_id)
    return {"message": "Account deleted"}

# Payments

def write_payment_to_file(payment: Payment):
    with open("payments.txt", "a") as file:
        file.write(f"{payment.id},{payment.from_account_id},{payment.to_account_id},{payment.amount_in_euros},{payment.payment_date}\n")

def read_payments_from_file() -> List[Payment]:
    payments = []
    with open("payments.txt", "r") as file:
        for line in file:
            if line.strip():
                id, from_id, to_id, amount, pay_date = line.strip().split(",")
                payments.append(Payment(
                    id=int(id),
                    from_account_id=int(from_id),
                    to_account_id=int(to_id),
                    amount_in_euros=int(amount),
                    payment_date=date.fromisoformat(pay_date)
                ))
    return payments

@app.post("/payments/")
def create_payment(payment: Payment):
    accounts = read_accounts_from_file()
    if not any(acc.id == payment.from_account_id for acc in accounts):
        raise HTTPException(status_code=400, detail="From account not found")
    if not any(acc.id == payment.to_account_id for acc in accounts):
        raise HTTPException(status_code=400, detail="To account not found")
    if payment.amount_in_euros <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")

    write_payment_to_file(payment)
    return {"message": "Payment created"}

@app.get("/payments/")
def get_payments():
    return read_payments_from_file()

@app.get("/payments/{payment_id}")
def get_payment(payment_id: int):
    for payment in read_payments_from_file():
        if payment.id == payment_id:
            return payment
    raise HTTPException(status_code=404, detail="Payment not found")

# Report 

@app.get("/report", response_model=List[ReportEntry])
def report():
    accounts = read_accounts_from_file()
    accounts_dict = {acc.id: acc.person_name for acc in accounts}
    report_entries = []

    for payment in read_payments_from_file():
        from_name = accounts_dict.get(payment.from_account_id, "Unknown")
        to_name = accounts_dict.get(payment.to_account_id, "Unknown")
        report_entries.append(ReportEntry(
            from_person_name=from_name,
            to_person_name=to_name,
            amount_in_euros=payment.amount_in_euros,
            payment=payment.payment_date.isoformat()
        ))

    return report_entries
