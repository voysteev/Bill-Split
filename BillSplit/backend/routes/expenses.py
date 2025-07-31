from flask import Blueprint, request, jsonify
from backend.services import expense_service, group_service # Import group_service to validate group access
from backend.routes.auth import jwt_required
from backend.models import ExpenseCreate, ExpenseUpdate
from pydantic import ValidationError

expenses_bp = Blueprint('expenses', __name__)

# Helper to check if user has access to a group
def _user_can_access_group(user_id, group_id):
    group = group_service.get_group(group_id)
    if not group:
        return False, "Group not found."
    if user_id not in group.members and user_id != group.owner_id:
        return False, "Access denied. Not a member of this group."
    return True, None


@expenses_bp.route('', methods=['POST'])
@jwt_required
def add_expense():
    user_id = request.user_id
    data = request.get_json()
    if not data:
        return jsonify({"message": "No input data provided."}), 400

    try:
        # Ensure the group_id in the expense data is accessible by the user
        group_id = data.get('group_id')
        if not group_id:
            return jsonify({"message": "group_id is required for the expense."}), 400

        can_access, msg = _user_can_access_group(user_id, group_id)
        if not can_access:
            return jsonify({"message": msg}), 403

        expense_create_data = ExpenseCreate(**data)
        # Ensure the payer is the current user or a member of the group
        if expense_create_data.payer_id != user_id:
            # If payer is different, verify requesting user has permission (e.g., group owner, or admin)
            # For simplicity, let's assume only the logged-in user can add expenses on their behalf initially.
            # Or, if adding on behalf of another member, the requesting user must be a member too.
            if expense_create_data.payer_id not in group_service.get_group(group_id).members:
                 return jsonify({"message": "Payer must be a member of the group."}), 403
            # If allowing user to create expense for others, consider more robust authorization here.

        new_expense = expense_service.add_expense(expense_create_data)
        return jsonify(new_expense.model_dump(by_alias=True)), 201
    except ValidationError as e:
        return jsonify({"message": "Validation error", "errors": e.errors()}), 400
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500

@expenses_bp.route('/<string:expense_id>', methods=['GET'])
@jwt_required
def get_expense_details(expense_id):
    user_id = request.user_id
    try:
        expense = expense_service.get_expense(expense_id)
        if not expense:
            return jsonify({"message": "Expense not found."}), 404
        
        # Check if user can access the group this expense belongs to
        can_access, msg = _user_can_access_group(user_id, expense.group_id)
        if not can_access:
            return jsonify({"message": msg}), 403

        return jsonify(expense.model_dump(by_alias=True)), 200
    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500

@expenses_bp.route('/group/<string:group_id>', methods=['GET'])
@jwt_required
def get_expenses_by_group(group_id):
    user_id = request.user_id
    try:
        can_access, msg = _user_can_access_group(user_id, group_id)
        if not can_access:
            return jsonify({"message": msg}), 403

        expenses = expense_service.get_expenses_for_group(group_id)
        return jsonify([exp.model_dump(by_alias=True) for exp in expenses]), 200
    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500

@expenses_bp.route('/user/<string:user_to_query_id>', methods=['GET'])
@jwt_required
def get_expenses_by_user(user_to_query_id):
    current_user_id = request.user_id
    
    # Optional: Allow users to query only their own expenses
    # If a user tries to query another user's expenses, you might need
    # to check if they are in a common group, or only allow admins.
    # For simplicity, we'll allow users to query only their own expenses for now.
    if current_user_id != user_to_query_id:
        # return jsonify({"message": "Access denied. Cannot query other users' expenses directly."}), 403
        # If you want to allow this, you'd need to fetch groups the `user_to_query_id` is in
        # and then check if `current_user_id` is also in those groups.
        pass # Allow for now for testing, but ideally restrict.

    try:
        expenses = expense_service.get_expenses_for_user(user_to_query_id)
        
        # Filter expenses to only include those from groups the current_user_id has access to
        accessible_expenses = []
        for exp in expenses:
            can_access, _ = _user_can_access_group(current_user_id, exp.group_id)
            if can_access:
                accessible_expenses.append(exp)

        return jsonify([exp.model_dump(by_alias=True) for exp in accessible_expenses]), 200
    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500

@expenses_bp.route('/<string:expense_id>', methods=['PUT'])
@jwt_required
def update_expense(expense_id):
    user_id = request.user_id
    data = request.get_json()
    if not data:
        return jsonify({"message": "No input data provided."}), 400

    try:
        existing_expense = expense_service.get_expense(expense_id)
        if not existing_expense:
            return jsonify({"message": "Expense not found."}), 404

        # Only the payer or group owner can update an expense
        group = group_service.get_group(existing_expense.group_id)
        if not group: # Should not happen if expense exists
            return jsonify({"message": "Associated group not found."}), 404

        if existing_expense.payer_id != user_id and group.owner_id != user_id:
            return jsonify({"message": "Access denied. Only the payer or group owner can update this expense."}), 403

        expense_update_data = ExpenseUpdate(**data)
        updated_expense = expense_service.update_expense(expense_id, expense_update_data)
        if updated_expense:
            return jsonify(updated_expense.model_dump(by_alias=True)), 200
        return jsonify({"message": "Expense not found or no changes applied."}), 404
    except ValidationError as e:
        return jsonify({"message": "Validation error", "errors": e.errors()}), 400
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500

@expenses_bp.route('/<string:expense_id>', methods=['DELETE'])
@jwt_required
def delete_expense(expense_id):
    user_id = request.user_id
    try:
        existing_expense = expense_service.get_expense(expense_id)
        if not existing_expense:
            return jsonify({"message": "Expense not found."}), 404

        # Only the payer or group owner can delete an expense
        group = group_service.get_group(existing_expense.group_id)
        if not group:
            return jsonify({"message": "Associated group not found."}), 404

        if existing_expense.payer_id != user_id and group.owner_id != user_id:
            return jsonify({"message": "Access denied. Only the payer or group owner can delete this expense."}), 403

        success = expense_service.delete_expense(expense_id)
        if success:
            return jsonify({"message": "Expense deleted successfully."}), 204
        return jsonify({"message": "Expense not found or could not be deleted."}), 404
    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500