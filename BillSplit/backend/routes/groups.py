from flask import Blueprint, request, jsonify, current_app
from backend.services import group_service, auth_service
from backend.routes.auth import jwt_required
from backend.models import GroupCreate, GroupUpdate
from pydantic import ValidationError # Ensure this is imported

groups_bp = Blueprint('groups', __name__)

@groups_bp.route('', methods=['POST'])
@jwt_required
def create_group():
    user_id = request.user_id
    data = request.get_json()
    if not data:
        current_app.logger.warning("No input data provided for group creation.")
        return jsonify({"message": "No input data provided."}), 400

    try:
        # Pydantic will validate 'data' against GroupCreate schema
        group_create_data = GroupCreate(**data)
        current_app.logger.info(f"Received valid group data from frontend: {group_create_data.model_dump()}")

        new_group = group_service.create_group(group_create_data, user_id)
        return jsonify(new_group.model_dump(by_alias=True)), 201
    except ValidationError as e:
        # THIS IS THE KEY PART FOR DEBUGGING 400s
        current_app.logger.error(f"Validation error during group creation: {e.errors()}", exc_info=True)
        return jsonify({"message": "Validation error", "errors": e.errors()}), 400
    except ValueError as e:
        current_app.logger.error(f"Value error during group creation: {e}", exc_info=True)
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred during group creation: {e}", exc_info=True)
        return jsonify({"message": f"An error occurred: {e}"}), 500

@groups_bp.route('', methods=['GET'])
@jwt_required
def get_user_groups():
    user_id = request.user_id
    try:
        current_app.logger.info(f"Attempting to fetch groups for user_id: {user_id}")
        groups = group_service.get_user_groups(user_id)
        current_app.logger.info(f"Fetched {len(groups)} groups for user {user_id}.")

        # Add a debug print for what's actually being returned
        # You can remove this for clean output later
        for group in groups:
             current_app.logger.debug(f"Group: {group.model_dump_json(indent=2)}")

        return jsonify([group.model_dump(by_alias=True) for group in groups]), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching user groups for user {user_id}: {e}", exc_info=True)
        return jsonify({"message": f"An error occurred: {e}"}), 500

@groups_bp.route('/<string:group_id>', methods=['GET'])
@jwt_required
def get_group_details(group_id):
    user_id = request.user_id
    try:
        group = group_service.get_group(group_id)
        if not group:
            return jsonify({"message": "Group not found."}), 404
        
        # Check if user is a member of the group
        if user_id not in group.members and user_id != group.owner_id:
            return jsonify({"message": "Access denied. Not a member of this group."}), 403

        return jsonify(group.model_dump(by_alias=True)), 200
    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500

@groups_bp.route('/<string:group_id>', methods=['PUT'])
@jwt_required
def update_group(group_id):
    user_id = request.user_id
    data = request.get_json()
    if not data:
        return jsonify({"message": "No input data provided."}), 400

    try:
        # Before updating, check if user is the owner
        existing_group = group_service.get_group(group_id)
        if not existing_group:
            return jsonify({"message": "Group not found."}), 404
        if existing_group.owner_id != user_id:
            return jsonify({"message": "Access denied. Only the owner can update this group."}), 403

        group_update_data = GroupUpdate(**data)
        updated_group = group_service.update_group(group_id, group_update_data)
        if updated_group:
            return jsonify(updated_group.model_dump(by_alias=True)), 200
        return jsonify({"message": "Group not found or no changes applied."}), 404
    except ValidationError as e:
        return jsonify({"message": "Validation error", "errors": e.errors()}), 400
    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500

@groups_bp.route('/<string:group_id>', methods=['DELETE'])
@jwt_required
def delete_group(group_id):
    user_id = request.user_id
    try:
        # Before deleting, check if user is the owner
        existing_group = group_service.get_group(group_id)
        if not existing_group:
            return jsonify({"message": "Group not found."}), 404
        if existing_group.owner_id != user_id:
            return jsonify({"message": "Access denied. Only the owner can delete this group."}), 403

        success = group_service.delete_group(group_id)
        if success:
            return jsonify({"message": "Group deleted successfully."}), 204 # No Content
        return jsonify({"message": "Group not found or could not be deleted."}), 404
    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500

@groups_bp.route('/<string:group_id>/members', methods=['POST'])
@jwt_required
def add_group_member(group_id):
    user_id = request.user_id # User making the request
    data = request.get_json()
    member_user_firebase_uid = data.get('firebase_uid')
    if not member_user_firebase_uid:
        return jsonify({"message": "Member's Firebase UID is required."}), 400

    try:
        # Check if requesting user is the owner of the group
        existing_group = group_service.get_group(group_id)
        if not existing_group:
            return jsonify({"message": "Group not found."}), 404
        if existing_group.owner_id != user_id:
            return jsonify({"message": "Access denied. Only the owner can add members."}), 403
        
        # Find the internal user_id from the firebase_uid
        member_user = auth_service.db.collection('users').where('firebase_uid', '==', member_user_firebase_uid).limit(1).get()
        if not member_user:
            return jsonify({"message": "Member user not found with provided Firebase UID."}), 404
        
        member_internal_id = member_user[0].id

        added = group_service.add_member_to_group(group_id, member_internal_id)
        if added:
            return jsonify({"message": "Member added successfully."}), 200
        return jsonify({"message": "User is already a member of this group."}), 409 # Conflict
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500

@groups_bp.route('/<string:group_id>/members/<string:member_id>', methods=['DELETE'])
@jwt_required
def remove_group_member(group_id, member_id):
    user_id = request.user_id # User making the request
    try:
        # Check if requesting user is the owner of the group
        existing_group = group_service.get_group(group_id)
        if not existing_group:
            return jsonify({"message": "Group not found."}), 404
        if existing_group.owner_id != user_id:
            return jsonify({"message": "Access denied. Only the owner can remove members."}), 403

        success = group_service.remove_member_from_group(group_id, member_id)
        if success:
            return jsonify({"message": "Member removed successfully."}), 204
        return jsonify({"message": "Member not found in this group."}), 404
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500