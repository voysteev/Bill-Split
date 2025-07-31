// frontend/src/components/Groups/GroupDetail.js (Minimalist/Placeholder)
import React from 'react';
import './Group.css'; // For styling

function GroupDetail({ group, members, expenses, settlementResult, currentUserId, groupOwnerId }) {
  if (!group) {
    return <p>Loading group details...</p>;
  }

  return (
    <div className="group-detail-card">
      <h2>{group.name}</h2>
      {group.description && <p className="group-description">{group.description}</p>}

      {/* This component would typically contain sub-components or render sections */}
      {/* For instance: */}
      {/* <GroupMembersList members={members} ownerId={group.owner_id} currentUserId={currentUserId} /> */}
      {/* <GroupExpensesList expenses={expenses} members={members} /> */}
      {/* <GroupSettlementView settlementResult={settlementResult} members={members} /> */}

      {/* You can expand this or integrate logic from pages/GroupPage.js into here */}
      <p>Group ID: {group.id}</p>
      <p>Owner: {members.find(m => m.id === group.owner_id)?.username || group.owner_id}</p>
      
      <h3>Members ({members.length})</h3>
      <ul className="member-list">
        {members.map(member => (
          <li key={member.id}>
            {member.username} {member.id === currentUserId && "(You)"}
            {member.id === group.owner_id && " (Owner)"}
          </li>
        ))}
      </ul>
      {/* ... more details from GroupPage.js can be moved here */}
    </div>
  );
}

export default GroupDetail;