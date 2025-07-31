// frontend/src/components/Groups/GroupList.js
import React from 'react';
import { Link } from 'react-router-dom';
import './Group.css'; // You can create this for specific group list styling

function GroupList({ groups, currentUserId }) {
  if (!groups || groups.length === 0) {
    return <p>No groups found. Create one to get started!</p>;
  }

  return (
    <ul className="group-list">
      {groups.map((group) => (
        <li key={group.id} className="group-item">
          <Link to={`/groups/${group.id}`}>
            <div className="group-info">
              <h3>{group.name}</h3>
              {group.description && <p>{group.description}</p>}
              <span className="group-owner">
                {group.owner_id === currentUserId ? 'You are the owner' : `Owner: ${group.owner_id}`}
              </span>
            </div>
          </Link>
          {/* Add actions like edit/delete if current user is owner */}
        </li>
      ))}
    </ul>
  );
}

export default GroupList;