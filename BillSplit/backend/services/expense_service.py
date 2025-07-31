from backend.firebase_db import get_firestore_db
from backend.models import ExpenseInDB, ExpenseCreate, ExpenseUpdate, ExpenseParticipantData
from firebase_admin.firestore import CollectionReference, DocumentReference
from datetime import datetime
from typing import List, Optional

expenses_ref: CollectionReference = lambda: get_firestore_db().collection('expenses')
groups_ref: CollectionReference = lambda: get_firestore_db().collection('groups')
users_ref: CollectionReference = lambda: get_firestore_db().collection('users')


def _validate_expense_data(expense_data: ExpenseCreate):
    """Helper to validate existence of group, payer, and participants."""
    if not get_firestore_db(): raise ConnectionError("Firestore not initialized.")

    # Validate group exists
    group_doc = groups_ref.document(expense_data.group_id).get()
    if not group_doc.exists:
        raise ValueError(f"Group with ID {expense_data.group_id} not found.")

    # Validate payer exists and is a member of the group
    payer_doc = users_ref.document(expense_data.payer_id).get()
    if not payer_doc.exists:
        raise ValueError(f"Payer user with ID {expense_data.payer_id} not found.")
    
    group_member_doc = groups_ref.document(expense_data.group_id).collection('members').document(expense_data.payer_id).get()
    if not group_member_doc.exists:
        raise ValueError(f"Payer user with ID {expense_data.payer_id} is not a member of group {expense_data.group_id}.")

    # Validate all participants exist and are members of the group
    for participant in expense_data.participants:
        user_doc = users_ref.document(participant.user_id).get()
        if not user_doc.exists:
            raise ValueError(f"Participant user with ID {participant.user_id} not found.")
        
        group_member_doc = groups_ref.document(expense_data.group_id).collection('members').document(participant.user_id).get()
        if not group_member_doc.exists:
            raise ValueError(f"Participant user with ID {participant.user_id} is not a member of group {expense_data.group_id}.")

def add_expense(expense_data: ExpenseCreate):
    """Adds a new expense to Firestore."""
    if not get_firestore_db(): raise ConnectionError("Firestore not initialized.")

    _validate_expense_data(expense_data)

    expense_dict = expense_data.model_dump()
    expense_dict['created_at'] = datetime.utcnow()

    # Store participants directly within the expense document for simplicity
    # For very large number of participants or complex participant data, a subcollection might be considered.
    update_time, doc_ref = expenses_ref.add(expense_dict)
    expense_id = doc_ref.id

    created_expense_doc = expenses_ref.document(expense_id).get()
    if created_expense_doc.exists:
        return ExpenseInDB(doc_id=created_expense_doc.id, **created_expense_doc.to_dict())
    return None

def get_expense(expense_id: str):
    """Retrieves a single expense by ID."""
    if not get_firestore_db(): raise ConnectionError("Firestore not initialized.")

    expense_doc = expenses_ref.document(expense_id).get()
    if expense_doc.exists:
        return ExpenseInDB(doc_id=expense_doc.id, **expense_doc.to_dict())
    return None

def get_expenses_for_group(group_id: str):
    """Retrieves all expenses for a specific group."""
    if not get_firestore_db(): raise ConnectionError("Firestore not initialized.")

    expenses_snapshot = expenses_ref.where('group_id', '==', group_id).stream()
    expenses = []
    for doc in expenses_snapshot:
        expenses.append(ExpenseInDB(doc_id=doc.id, **doc.to_dict()))
    return expenses

def get_expenses_for_user(user_id: str):
    """Retrieves all expenses where a user is either the payer or a participant."""
    if not get_firestore_db(): raise ConnectionError("Firestore not initialized.")

    user_expenses = []

    # Get expenses where user is the payer
    payer_expenses_snapshot = expenses_ref.where('payer_id', '==', user_id).stream()
    for doc in payer_expenses_snapshot:
        user_expenses.append(ExpenseInDB(doc_id=doc.id, **doc.to_dict()))

    # Get expenses where user is a participant (requires iterating or a specific query)
    # Firestore doesn't directly support querying array elements for specific values efficiently in all cases.
    # For 'participants' array, you'd typically need to fetch all and filter client-side,
    # or use array-contains if you're looking for exact matches of complete participant objects.
    # A better approach for this query might be to have a separate 'user_expense_involvements'
    # collection or a more complex query setup.
    # For now, let's assume we iterate and filter for demonstration.
    all_expenses_snapshot = expenses_ref.stream() # Can be inefficient for many expenses
    for doc in all_expenses_snapshot:
        expense = ExpenseInDB(doc_id=doc.id, **doc.to_dict())
        for participant in expense.participants:
            if participant.user_id == user_id and expense.id not in [e.id for e in user_expenses]:
                user_expenses.append(expense)
                break
    
    return user_expenses

def update_expense(expense_id: str, expense_data: ExpenseUpdate):
    """Updates an existing expense."""
    if not get_firestore_db(): raise ConnectionError("Firestore not initialized.")

    expense_ref: DocumentReference = expenses_ref.document(expense_id)
    expense_doc = expense_ref.get()
    if not expense_doc.exists:
        return None

    update_dict = expense_data.model_dump(exclude_unset=True)
    
    # If participants are updated, ensure they are validated
    if 'participants' in update_dict and update_dict['participants'] is not None:
        # Re-fetch the current group_id to validate participants
        current_expense_data = expense_doc.to_dict()
        current_group_id = current_expense_data.get('group_id')
        
        # Create a temporary ExpenseCreate object for validation
        temp_expense_data = ExpenseCreate(
            description="temp", amount=1.0, payer_id="temp", group_id=current_group_id,
            participants=update_dict['participants']
        )
        _validate_expense_data(temp_expense_data) # Validate participants against group membership

    if update_dict:
        expense_ref.update(update_dict)

    return get_expense(expense_id)

def delete_expense(expense_id: str):
    """Deletes an expense."""
    if not get_firestore_db(): raise ConnectionError("Firestore not initialized.")

    expense_ref: DocumentReference = expenses_ref.document(expense_id)
    if not expense_ref.get().exists:
        return False
    
    expense_ref.delete()
    return True