import React, { useState, useEffect } from 'react';
import api from '../../api/axiosConfig';
import { useAuth } from '../../hooks/useAuth';
import './Expense.css'; // Styling for expense forms/lists

function AddExpenseForm({ groupId, groupMembers, onExpenseAdded }) {
  const { appUser } = useAuth();
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [payerId, setPayerId] = useState(appUser?.id || ''); // Default payer to current user
  const [participants, setParticipants] = useState([]); // Array of { id: memberId, checked: bool, share: amount }
  const [splitMethod, setSplitMethod] = useState('equal'); // 'equal' or 'unequal'
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Initialize participants when groupMembers change or form is reset
    if (groupMembers) {
      const initialParticipants = groupMembers.map(member => ({
        id: member.id,
        username: member.username || member.email,
        checked: false, // Default to not included
        share: '' // For unequal split
      }));
      setParticipants(initialParticipants);
    }
    setPayerId(appUser?.id || ''); // Reset payer to current user
  }, [groupMembers, appUser]);

  const handleParticipantCheck = (id) => {
    setParticipants(prev => 
      prev.map(p => p.id === id ? { ...p, checked: !p.checked } : p)
    );
  };

  const handleShareChange = (id, value) => {
    setParticipants(prev => 
      prev.map(p => p.id === id ? { ...p, share: value } : p)
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    const includedParticipants = participants.filter(p => p.checked);

    if (includedParticipants.length === 0) {
      setError('Please select at least one participant.');
      setIsLoading(false);
      return;
    }

    let finalParticipantsData = [];
    if (splitMethod === 'equal') {
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
          setError("Share amounts cannot be negative.");
          setIsLoading(false);
          return;
        }
        finalParticipantsData.push({ user_id: p.id, share_amount: shareAmount });
        totalAssignedShare += shareAmount;
      }

      if (hasUnassignedShare) {
        setError("All selected participants must have a valid share amount for unequal split.");
        setIsLoading(false);
        return;
      }

      if (Math.abs(totalAssignedShare - parseFloat(amount)) > 0.01) { // Allow for small float inaccuracies
        setError(`Total shares ($${totalAssignedShare.toFixed(2)}) do not match total amount ($${parseFloat(amount).toFixed(2)}).`);
        setIsLoading(false);
        return;
      }
    }

    try {
      const response = await api.post('/expenses', {
        group_id: groupId,
        description,
        amount: parseFloat(amount),
        payer_id: payerId,
        participants: finalParticipantsData,
      });
      onExpenseAdded(response.data);
      // Reset form
      setDescription('');
      setAmount('');
      setSplitMethod('equal');
      setParticipants(groupMembers.map(member => ({
        id: member.id,
        username: member.username || member.email,
        checked: false,
        share: ''
      })));
      setPayerId(appUser?.id || '');
    } catch (err) {
      console.error('Error adding expense:', err);
      setError(err.response?.data?.message || 'Failed to add expense.');
    } finally {
      setIsLoading(false);
    }
  };

  const availableMembers = groupMembers || [];

  return (
    <div className="add-expense-form-container">
      <h4>Add New Expense</h4>
      <form onSubmit={handleSubmit} className="add-expense-form">
        {error && <p className="error-message">{error}</p>}
        <div className="form-group">
          <label htmlFor="description">Description:</label>
          <input
            type="text"
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="amount">Amount:</label>
          <input
            type="number"
            id="amount"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            min="0.01"
            step="0.01"
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="payer">Who Paid?</label>
          <select
            id="payer"
            value={payerId}
            onChange={(e) => setPayerId(e.target.value)}
            required
          >
            {availableMembers.map(member => (
              <option key={member.id} value={member.id}>
                {member.username || member.email} {appUser?.id === member.id && "(You)"}
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
                checked={splitMethod === 'equal'} 
                onChange={() => setSplitMethod('equal')} 
              /> Equal
            </label>
            <label>
              <input 
                type="radio" 
                value="unequal" 
                checked={splitMethod === 'unequal'} 
                onChange={() => setSplitMethod('unequal')} 
              /> Unequal
            </label>
          </div>
          <ul className="participant-list">
            {participants.map(p => (
              <li key={p.id}>
                <label>
                  <input
                    type="checkbox"
                    checked={p.checked}
                    onChange={() => handleParticipantCheck(p.id)}
                  />
                  {p.username}
                </label>
                {splitMethod === 'unequal' && p.checked && (
                  <input
                    type="number"
                    value={p.share}
                    onChange={(e) => handleShareChange(p.id, e.target.value)}
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
        <button type="submit" className="button primary" disabled={isLoading}>
          {isLoading ? 'Adding...' : 'Add Expense'}
        </button>
      </form>
    </div>
  );
}

export default AddExpenseForm;