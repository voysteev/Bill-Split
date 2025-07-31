from flask import Blueprint, request, jsonify
from backend.services import settlement_service, group_service, auth_service
from backend.routes.auth import jwt_required # Import the decorator

settlements_bp = Blueprint('settlements', __name__)

@settlements_bp.route('/<string:group_id>', methods=['GET'])
@jwt_required
def get_group_settlements(group_id):
    user_id = request.user_id # User making the request
    try:
        # Check if the user is a member of the group
        group = group_service.get_group(group_id)
        if not group:
            return jsonify({"message": "Group not found."}), 404
        
        if user_id not in group.members and user_id != group.owner_id:
            return jsonify({"message": "Access denied. You are not a member of this group."}), 403

        settlement_result = settlement_service.calculate_settlements(group_id)

        # Enhance transaction list with user names for frontend display
        # Fetch user details for all involved users
        all_involved_user_ids = set()
        for transaction in settlement_result.transactions:
            all_involved_user_ids.add(transaction.payer_id)
            all_involved_user_ids.add(transaction.receiver_id)
        
        users_map = {}
        if all_involved_user_ids: # Avoid empty query
            user_docs = auth_service.users_ref().where('__name__', 'in', list(all_involved_user_ids)).get()
            users_map = {doc.id: auth_service.UserInDB(doc_id=doc.id, **doc.to_dict()) for doc in user_docs}

        # Update transaction objects with names
        for transaction in settlement_result.transactions:
            transaction.payer_name = users_map.get(transaction.payer_id).username if transaction.payer_id in users_map else f"User {transaction.payer_id}"
            transaction.receiver_name = users_map.get(transaction.receiver_id).username if transaction.receiver_id in users_map else f"User {transaction.receiver_id}"

        return jsonify(settlement_result.model_dump(by_alias=True)), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500