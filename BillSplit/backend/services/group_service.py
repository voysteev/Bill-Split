from backend.firebase_db import get_firestore_db
from backend.models import GroupInDB, GroupCreate, GroupUpdate, UserInDB
from firebase_admin.firestore import CollectionReference, DocumentReference
from datetime import datetime
from typing import List, Optional

# Firestore collection references
groups_ref: CollectionReference = lambda: get_firestore_db().collection('groups')
users_ref: CollectionReference = lambda: get_firestore_db().collection('users')

def create_group(group_data: GroupCreate, owner_id: str):
    """Creates a new group in Firestore."""
    if not get_firestore_db(): raise ConnectionError("Firestore not initialized.")

    # Validate owner_id exists
    owner_doc = users_ref().document(owner_id).get()
    if not owner_doc.exists:
        raise ValueError(f"Owner user with ID {owner_id} does not exist.")

    group_dict = group_data.model_dump(exclude={'member_uids'}) # Exclude member_uids from main doc
    group_dict['owner_id'] = owner_id
    group_dict['created_at'] = datetime.utcnow()

    # Add the group document
    update_time, doc_ref = groups_ref().add(group_dict)
    group_id = doc_ref.id

    # Add owner as the first member
    initial_members_firebase_uids = list(set(group_data.member_uids + [owner_doc.to_dict().get('firebase_uid')]))

    # Add members to a 'members' subcollection
    group_members_subcollection: CollectionReference = groups_ref().document(group_id).collection('members')
    added_member_ids = []
    for firebase_uid in initial_members_firebase_uids:
        user_query = users_ref().where('firebase_uid', '==', firebase_uid).limit(1).get()
        if user_query:
            member_doc_id = user_query[0].id
            group_members_subcollection.document(member_doc_id).set({'added_at': datetime.utcnow()})
            added_member_ids.append(member_doc_id)
        else:
            print(f"Warning: User with Firebase UID {firebase_uid} not found when adding to group {group_id}")

    # Fetch the created group to return consistent data
    created_group_doc = groups_ref().document(group_id).get()
    if created_group_doc.exists:
        # Construct GroupInDB with fetched member IDs
        group_data = created_group_doc.to_dict()
        group_data['members'] = added_member_ids # Add actual Firestore member IDs
        return GroupInDB(doc_id=created_group_doc.id, **group_data)
    return None

def get_group(group_id: str):
    """Retrieves a group and its members from Firestore."""
    if not get_firestore_db(): raise ConnectionError("Firestore not initialized.")

    group_doc = groups_ref().document(group_id).get()
    if not group_doc.exists:
        return None

    group_data = group_doc.to_dict()
    # Fetch members from the subcollection
    members_snapshot = groups_ref().document(group_id).collection('members').stream()
    member_ids = [doc.id for doc in members_snapshot]

    group_data['members'] = member_ids
    return GroupInDB(doc_id=group_doc.id, **group_data)

def get_user_groups(user_id: str):
    """Retrieves all groups a user is a member of."""
    if not get_firestore_db(): raise ConnectionError("Firestore not initialized.")

    # Find groups where the user is a member in the subcollection
    # Firestore doesn't directly support querying subcollections across documents.
    # The common pattern is to query all groups and then filter members.
    # For efficiency for large numbers of groups/users, a dedicated 'group_memberships'
    # collection might be better where each document represents a user's membership to a group.
    # For now, we iterate through groups and check membership.

    all_groups_snapshot = groups_ref().stream()
    user_groups = []
    for group_doc in all_groups_snapshot:
        group_id = group_doc.id
        # Check if user_id is present in the 'members' subcollection of this group
        member_doc = groups_ref().document(group_id).collection('members').document(user_id).get()
        if member_doc.exists:
            group_data = group_doc.to_dict()
            # Fetch all members for the complete GroupInDB object
            members_snapshot = groups_ref().document(group_id).collection('members').stream()
            group_data['members'] = [m_doc.id for m_doc in members_snapshot]
            user_groups.append(GroupInDB(doc_id=group_id, **group_data))
    return user_groups

def update_group(group_id: str, group_data: GroupUpdate):
    """Updates an existing group in Firestore."""
    if not get_firestore_db(): raise ConnectionError("Firestore not initialized.")

    group_ref: DocumentReference = groups_ref().document(group_id)
    group_doc = group_ref.get()
    if not group_doc.exists:
        return None

    update_dict = group_data.model_dump(exclude_unset=True) # Only update fields provided
    if update_dict:
        group_ref.update(update_dict)

    # Fetch updated group
    return get_group(group_id)

def delete_group(group_id: str):
    """Deletes a group and its subcollections (members, expenses)."""
    if not get_firestore_db(): raise ConnectionError("Firestore not initialized.")

    group_ref: DocumentReference = groups_ref().document(group_id)
    group_doc = group_ref.get()
    if not group_doc.exists:
        return False

    # Delete subcollections first (Firestore doesn't do this recursively)
    # Delete members subcollection
    members_snapshot = group_ref().collection('members').stream()
    for doc in members_snapshot:
        doc.reference.delete()

    # Delete expenses related to this group (assuming expenses are in a top-level collection
    # but also have a group_id field that can be queried).
    # If expenses were a subcollection, delete them similarly.
    expenses_in_group = get_firestore_db().collection('expenses').where('group_id', '==', group_id).stream()
    for exp_doc in expenses_in_group:
        # Delete expense participants subcollection if it exists for this expense
        exp_doc.reference.collection('participants').stream() # Assuming no participants subcollection, directly delete
        exp_doc.reference.delete()


    group_ref.delete()
    return True

def add_member_to_group(group_id: str, user_id: str):
    """Adds a user as a member to a group."""
    if not get_firestore_db(): raise ConnectionError("Firestore not initialized.")

    group_ref: DocumentReference = groups_ref().document(group_id)
    user_ref: DocumentReference = users_ref().document(user_id)

    if not group_ref.get().exists:
        raise ValueError(f"Group with ID {group_id} not found.")
    if not user_ref.get().exists:
        raise ValueError(f"User with ID {user_id} not found.")

    member_subcollection: CollectionReference = group_ref.collection('members')
    member_doc = member_subcollection.document(user_id).get()

    if member_doc.exists:
        return False # User is already a member

    member_subcollection.document(user_id).set({'added_at': datetime.utcnow()})
    return True

def remove_member_from_group(group_id: str, user_id: str):
    """Removes a user from a group's members."""
    if not get_firestore_db(): raise ConnectionError("Firestore not initialized.")

    group_ref: DocumentReference = groups_ref().document(group_id)
    member_subcollection: CollectionReference = group_ref.collection('members')
    member_doc = member_subcollection.document(user_id).get()

    if not group_ref.get().exists:
        raise ValueError(f"Group with ID {group_id} not found.")
    if not member_doc.exists:
        return False # User is not a member

    member_subcollection.document(user_id).delete()
    return True