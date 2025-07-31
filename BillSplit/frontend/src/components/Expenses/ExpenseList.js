import React, { useState } from 'react';
import api from '../../api/axiosConfig';
import { FaEdit, FaTrash } from 'react-icons/fa'; // For icons

function ExpenseList({ expenses, groupMembers, onExpenseUpdated, onExpenseDeleted, currentUserId, groupOwnerId }) {
  const [editingExpenseId, setEditingExpenseId] = useState(null);
  const [editDescription, setEditDescription] = useState('');
  const [editAmount, setEditAmount] = useState('');
  const [editPayerId, setEditPayerId] = useState('');
  const [editParticipants, setEditParticipants] = useState([]); // {id, checked, share}
  const [editSplitMethod, setEditSplitMethod] = useState('equal');
  const [editError, setEditError] = useState('');
  const [editLoading, setEditLoading] = useState(false);

  const getMemberName = (id) => {
    const member = groupMembers.find(m => m.id === id);
    return member ? member.username : `Unknown User (${id})`;
  };

  const startEditing = (expense) => {
    setEditingExpenseId(expense.id);
    setEditDescription(expense.description);
    setEditAmount(expense.amount);
    setEditPayerId(expense.payer_id);

    // Initialize participants for editing
    const initialEditParticipants = groupMembers.map(member => {
      const participantData = expense.participants.find(p => p.user_id === member.id);
      return {
        id: member.id,
        username: member.username || member.email,
        checked: !!participantData, // Check if this member was a participant
        share: participantData?.share_amount || '' // Pre-fill share if unequal
      };
    });
    setEditParticipants(initialEditParticipants);

    // Determine initial split method based on existing expense
    const hasUnequalShares = expense.participants.some(p => p.share_amount !== null && p.share_amount !== undefined);
    setEditSplitMethod(hasUnequalShares ? 'unequal' : 'equal');
  };

  const cancelEditing = () => {
    setEditingExpenseId(null);
    setEditError('');
  };

  const handleEditParticipantCheck = (id) => {
    setEditParticipants(prev => 
      prev.map(p => p.id === id ? { ...p, checked: !p.checked } : p)
    );
  };

  const handleEditShareChange = (id, value) => {
    setEditParticipants(prev => 
      prev.map(p => p.id === id ? { ...p, share: value } : p)
    );
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setEditError('');
    setEditLoading(true);

    const includedParticipants = editParticipants.filter(p => p.checked);

    if (includedParticipants.length === 0) {
      setEditError('Please select at least one participant.');
      setEditLoading(false);
      return;
    }

    let finalParticipantsData = [];
    if (editSplitMethod === 'equal') {
      finalParticipantsData = includedParticipants.map(p => ({ user_id: p.id }));
    } else { // unequal split
      let totalAssignedShare = 0;
      let hasUnassignedShare = false;

      for (const p of includedParticipants) {
        if (p.share === '' || isNaN(parseFloat(p.share))) {
          hasUnassignedShare = true;
          break;
        }
        const shareAmount = parseFloat(p.share);
        if (shareAmount < 0) {
            setEditError("Share amounts cannot be negative.");
            setEditLoading(false);
            return;
        }
        finalParticipantsData.push({ user_id: p.id, share_amount: shareAmount });
        totalAssignedShare += shareAmount;
      }

      if (hasUnassignedShare) {
        setEditError("All selected participants must have a valid share amount for unequal split.");
        setEditLoading(false);
        return;
      }

      if (Math.abs(totalAssignedShare - parseFloat(editAmount)) > 0.01) {
        setEditError(`Total shares ($${totalAssignedShare.toFixed(2)}) do not match total amount ($${parseFloat(editAmount).toFixed(2)}).`);
        setEditLoading(false);
        return;
      }
    }

    try {
      const response = await api.put(`/expenses/${editingExpenseId}`, {
        description: editDescription,
        amount: parseFloat(editAmount),
        payer_id: editPayerId,
        participants: finalParticipantsData,
      });
      onExpenseUpdated(response.data);
      setEditingExpenseId(null); // Exit edit mode
    } catch (err) {
      console.error('Error updating expense:', err);
      setEditError(err.response?.data?.message || 'Failed to update expense.');
    } finally {
      setEditLoading(false);
    }
  };

  const handleDelete = async (expenseId) => {
    if (window.confirm('Are you sure you want to delete this expense?')) {
      try {
        await api.delete(`/expenses/${expenseId}`);
        onExpenseDeleted(expenseId);
      } catch (err) {
        console.error('Error deleting expense:', err);
        alert(err.response?.data?.message || 'Failed to delete expense.');
      }
    }
  };

  return (
    <div className="expense-list-container">
      {expenses.length === 0 ? (
        <p>No expenses added yet for this group.</p>
      ) : (
        <ul className="expense-list">
          {expenses.map((expense) => (
            <li key={expense.id} className="expense-item">
              {editingExpenseId === expense.id ? (
                <form onSubmit={handleUpdate} className="edit-expense-form">
                  {editError && <p className="error-message">{editError}</p>}
                  <div className="form-group">
                    <label>Description:</label>
                    <input
                      type="text"
                      value={editDescription}
                      onChange={(e) => setEditDescription(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Amount:</label>
                    <input
                      type="number"
                      value={editAmount}
                      onChange={(e) => setEditAmount(e.target.value)}
                      min="0.01"
                      step="0.01"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Payer:</label>
                    <select
                      value={editPayerId}
                      onChange={(e) => setEditPayerId(e.target.value)}
                      required
                    >
                      {groupMembers.map(member => (
                        <option key={member.id} value={member.id}>
                          {member.username || member.email}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>For Whom?</label>
                    <div className="split-method-radios">
                        <label>
                            <input
                                type="radio"
                                value="equal"
                                checked={editSplitMethod === 'equal'}
                                onChange={() => setEditSplitMethod('equal')}
                            /> Equal
                        </label>
                        <label>
                            <input
                                type="radio"
                                value="unequal"
                                checked={editSplitMethod === 'unequal'}
                                onChange={() => setEditSplitMethod('unequal')}
                            /> Unequal
                        </label>
                    </div>
                    <ul className="participant-list">
                      {editParticipants.map(p => (
                        <li key={p.id}>
                          <label>
                            <input
                              type="checkbox"
                              checked={p.checked}
                              onChange={() => handleEditParticipantCheck(p.id)}
                            />
                            {p.username}
                          </label>
                          {editSplitMethod === 'unequal' && p.checked && (
                            <input
                              type="number"
                              value={p.share}
                              onChange={(e) => handleEditShareChange(p.id, e.target.value)}
                              placeholder="Share"
                              min="0"
                              step="0.01"
                              className="participant-share-input"
                            />
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="edit-actions">
                    <button type="submit" className="button primary" disabled={editLoading}>
                      {editLoading ? 'Updating...' : 'Update'}
                    </button>
                    <button type="button" className="button secondary" onClick={cancelEditing} disabled={editLoading}>
                      Cancel
                    </button>
                  </div>
                </form>
              ) : (
                <>
                  <div className="expense-details">
                    <p><strong>{expense.description}</strong> - ${expense.amount.toFixed(2)}</p>
                    <p>Paid by: {getMemberName(expense.payer_id)}</p>
                    <p>For: {
                      expense.participants.map(p => getMemberName(p.user_id))
                                       .join(', ')
                    }</p>
                    <p className="expense-date">
                        {new Date(expense.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="expense-actions">
                    {(expense.payer_id === currentUserId || groupOwnerId === currentUserId) && (
                      <>
                        <button onClick={() => startEditing(expense)} className="button icon-button edit-button">
                          <FaEdit />
                        </button>
                        <button onClick={() => handleDelete(expense.id)} className="button icon-button delete-button">
                          <FaTrash />
                        </button>
                      </>
                    )}
                  </div>
                </>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default ExpenseList;