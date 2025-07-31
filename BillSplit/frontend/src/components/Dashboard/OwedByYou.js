import React, { useEffect, useState } from 'react';
import api from '../../api/axiosConfig';

function OwedByYou({ userId }) {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchExpenses = async () => {
      if (!userId) {
        setLoading(false);
        return;
      }
      setLoading(true);
      setError('');
      try {
        // Fetch all expenses where the current user is a participant
        const response = await api.get(`/expenses/user/${userId}`);
        const userExpenses = response.data;

        // Filter for expenses where the user is a participant and owes money
        // This is a simplified client-side calculation. A more robust solution
        // would involve the backend returning personal balances or detailed "owed" lists.
        let owedExpenses = [];
        const personalBalances = {}; // Track user's balance per group

        for (const exp of userExpenses) {
          if (exp.payer_id !== userId) { // If someone else paid
            const participantEntry = exp.participants.find(p => p.user_id === userId);
            if (participantEntry) {
              const numParticipants = exp.participants.length;
              let userShare = 0;

              // Check if any participant has an explicit share_amount
              const hasExplicitShares = exp.participants.some(p => p.share_amount !== null && p.share_amount !== undefined);

              if (hasExplicitShares) {
                userShare = participantEntry.share_amount;
                // If user's share_amount is null, it means they are part of the 'remaining' for equal split
                if (userShare === null || userShare === undefined) {
                    const totalExplicitShare = exp.participants.reduce((sum, p) => sum + (p.share_amount || 0), 0);
                    const numImplicitParticipants = exp.participants.filter(p => p.share_amount === null || p.share_amount === undefined).length;
                    if (numImplicitParticipants > 0) {
                        userShare = (exp.amount - totalExplicitShare) / numImplicitParticipants;
                    } else {
                        userShare = 0; // Should not happen if this path is taken
                    }
                }
              } else {
                // Pure equal split among all participants
                userShare = exp.amount / numParticipants;
              }

              if (userShare > 0) {
                owedExpenses.push({
                  id: exp.id,
                  description: exp.description,
                  amount: userShare,
                  group_id: exp.group_id,
                  payer_id: exp.payer_id,
                  payer_name: 'Loading...', // Placeholder, ideally fetch names
                });
              }
            }
          }
        }
        setExpenses(owedExpenses);

        // Fetch payer names for display
        const payerIds = [...new Set(owedExpenses.map(e => e.payer_id))];
        if (payerIds.length > 0) {
            const usersResponse = await api.get('/auth/users', { params: { ids: payerIds.join(',') } }); // Assuming such an endpoint
            const usersMap = new Map(usersResponse.data.map(u => [u.id, u.username || u.email]));
            setExpenses(prev => prev.map(exp => ({
                ...exp,
                payer_name: usersMap.get(exp.payer_id) || `User ${exp.payer_id}`
            })));
        }

      } catch (err) {
        console.error('Error fetching expenses for "Owed By You":', err);
        setError('Failed to load what you owe.');
      } finally {
        setLoading(false);
      }
    };

    fetchExpenses();
  }, [userId]);

  if (loading) {
    return <div className="balance-section">Loading your debts...</div>;
  }

  if (error) {
    return <div className="balance-section error-message">{error}</div>;
  }

  const totalOwed = expenses.reduce((sum, exp) => sum + exp.amount, 0);

  return (
    <div className="balance-section">
      <h4>Owed By You: ${totalOwed.toFixed(2)}</h4>
      {expenses.length === 0 ? (
        <p>You currently don't owe anyone for shared expenses.</p>
      ) : (
        <ul className="owed-list">
          {expenses.map((expense) => (
            <li key={expense.id}>
              You owe {expense.payer_name} ${expense.amount.toFixed(2)} for "{expense.description}"
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default OwedByYou;