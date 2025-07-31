from backend.firebase_db import get_firestore_db
from backend.models import SettlementResult, SettlementTransaction, UserInDB, ExpenseInDB
from firebase_admin.firestore import CollectionReference
from typing import Dict, List, Tuple
import math

expenses_ref: CollectionReference = lambda: get_firestore_db().collection('expenses')
groups_ref: CollectionReference = lambda: get_firestore_db().collection('groups')
users_ref: CollectionReference = lambda: get_firestore_db().collection('users')

def calculate_settlements(group_id: str) -> SettlementResult:
    """
    Calculates the minimum number of transactions to settle debts within a group.
    """
    if not get_firestore_db(): raise ConnectionError("Firestore not initialized.")

    group_doc = groups_ref.document(group_id).get()
    if not group_doc.exists:
        raise ValueError(f"Group with ID {group_id} not found.")

    # 1. Get all members of the group
    members_snapshot = groups_ref.document(group_id).collection('members').stream()
    member_ids = [doc.id for doc in members_snapshot]
    if not member_ids:
        return SettlementResult(balances={}, transactions=[])

    # Fetch user details for names later
    user_docs = users_ref.where('__name__', 'in', member_ids).get()
    users_map: Dict[str, UserInDB] = {doc.id: UserInDB(doc_id=doc.id, **doc.to_dict()) for doc in user_docs}

    # Initialize balances for all members to 0
    balances: Dict[str, float] = {member_id: 0.0 for member_id in member_ids}

    # 2. Get all expenses for the group
    expenses_snapshot = expenses_ref.where('group_id', '==', group_id).stream()

    for exp_doc in expenses_snapshot:
        expense = ExpenseInDB(doc_id=exp_doc.id, **exp_doc.to_dict())

        # Ensure payer is a valid member
        if expense.payer_id not in balances:
            print(f"Warning: Payer {expense.payer_id} for expense {expense.id} is not a valid group member. Skipping.")
            continue

        # Add the amount paid by the payer
        balances[expense.payer_id] += expense.amount

        # Calculate share for each participant
        num_participants = len(expense.participants)
        if num_participants == 0:
            continue # No one to split with, payer gets full amount back from no one

        # If any participant has a specific share_amount, use that.
        # Otherwise, divide evenly among participants.
        total_explicit_share_amount = sum(p.share_amount for p in expense.participants if p.share_amount is not None)
        num_implicit_participants = sum(1 for p in expense.participants if p.share_amount is None)

        if total_explicit_share_amount > expense.amount:
             # This means explicit shares exceed total amount. Handle as an error or adjust.
             # For simplicity, we'll just log and continue, or raise an error in a real app.
             print(f"Warning: Explicit participant shares for expense {expense.id} exceed total amount. Adjusting.")
             # Optionally, proportionally scale down explicit shares, or redistribute remaining.
             pass # For now, let's assume valid data for this simple calc.

        remaining_amount_for_implicit = expense.amount - total_explicit_share_amount
        implicit_share_per_person = 0.0
        if num_implicit_participants > 0:
            implicit_share_per_person = remaining_amount_for_implicit / num_implicit_participants

        for participant in expense.participants:
            # Ensure participant is a valid member
            if participant.user_id not in balances:
                print(f"Warning: Participant {participant.user_id} for expense {expense.id} is not a valid group member. Skipping.")
                continue

            share = participant.share_amount if participant.share_amount is not None else implicit_share_per_person
            balances[participant.user_id] -= share # Each participant owes their share

    # Round balances to avoid floating point inaccuracies
    for user_id in balances:
        balances[user_id] = round(balances[user_id], 2)

    # 3. Simplify transactions (Min-cash-flow algorithm)
    transactions: List[SettlementTransaction] = []

    # Filter out users with zero balance and separate debtors/creditors
    net_balances: Dict[str, float] = {k: v for k, v in balances.items() if abs(v) > 0.01} # Use a small epsilon

    # Create lists of (user_id, balance) tuples
    debtors = sorted([(user_id, balance) for user_id, balance in net_balances.items() if balance < 0], key=lambda x: x[1]) # Most negative first
    creditors = sorted([(user_id, balance) for user_id, balance in net_balances.items() if balance > 0], key=lambda x: x[1], reverse=True) # Most positive first

    while debtors and creditors:
        debtor_id, debtor_balance = debtors[0]
        creditor_id, creditor_balance = creditors[0]

        # Amount to settle in this transaction
        settle_amount = min(abs(debtor_balance), creditor_balance)

        transactions.append(SettlementTransaction(
            payer_id=debtor_id,
            receiver_id=creditor_id,
            amount=round(settle_amount, 2),
            payer_name=users_map.get(debtor_id, UserInDB(id=debtor_id, username=f"User {debtor_id}", email="")).username, # Fallback name
            receiver_name=users_map.get(creditor_id, UserInDB(id=creditor_id, username=f"User {creditor_id}", email="")).username
        ))

        # Update balances
        debtors[0] = (debtor_id, debtor_balance + settle_amount)
        creditors[0] = (creditor_id, creditor_balance - settle_amount)

        # Remove if balance is settled
        if round(debtors[0][1], 2) >= 0:
            debtors.pop(0)
        if round(creditors[0][1], 2) <= 0:
            creditors.pop(0)

    return SettlementResult(balances=balances, transactions=transactions)