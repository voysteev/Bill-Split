import React, { useState } from 'react';
import api from '../../api/axiosConfig';
import { useAuth } from '../../hooks/useAuth';
import './Modal.css'; // Generic modal styling

function CreateGroupModal({ isOpen, onClose, onGroupCreated }) {
  const { appUser } = useAuth();
  const [groupName, setGroupName] = useState('');
  const [description, setDescription] = useState('');
  const [memberEmails, setMemberEmails] = useState(''); // Comma-separated emails
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    if (!appUser) {
      setError("User not logged in.");
      setIsLoading(false);
      return;
    }

    const memberUids = memberEmails.split(',').map(email => email.trim()).filter(email => email);

    try {
      const response = await api.post('/groups', {
        name: groupName,
        description: description,
        owner_id: appUser.id, // The Flask backend will actually use the JWT's user_id
        member_uids: memberUids // Send Firebase UIDs, backend will resolve to internal IDs
      });
      onGroupCreated(response.data);
      setGroupName('');
      setDescription('');
      setMemberEmails('');
    } catch (err) {
      console.error('Error creating group:', err);
      setError(err.response?.data?.message || 'Failed to create group.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h3>Create New Group</h3>
        <form onSubmit={handleSubmit}>
          {error && <p className="error-message">{error}</p>}
          <div className="form-group">
            <label htmlFor="groupName">Group Name:</label>
            <input
              type="text"
              id="groupName"
              value={groupName}
              onChange={(e) => setGroupName(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="description">Description (Optional):</label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            ></textarea>
          </div>
          <div className="form-group">
            <label htmlFor="memberEmails">Add Members (Firebase User Emails, comma-separated):</label>
            <input
              type="text"
              id="memberEmails"
              value={memberEmails}
              onChange={(e) => setMemberEmails(e.target.value)}
              placeholder="e.g., user1@example.com, user2@example.com"
            />
            <small>New members must already be registered Firebase users.</small>
          </div>
          <div className="modal-actions">
            <button type="submit" className="button primary" disabled={isLoading}>
              {isLoading ? 'Creating...' : 'Create Group'}
            </button>
            <button type="button" className="button secondary" onClick={onClose} disabled={isLoading}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CreateGroupModal;