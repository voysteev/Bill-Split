import React, { useEffect, useState } from 'react';
import api from '../../api/axiosConfig';

function OwedToYou({ userId }) {
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
        // Fetch all expenses where the current user is the payer
        const response = await api.get(`/expenses/user/${userId}`);
        const userExpenses = response.data;

        // Filter for expenses where the user is the payer and others owe them
        let owedToYouExpenses = [];
        for (const exp of userExpenses) {
          if (exp.payer_id === userId) { // If you paid
            const numParticipants = exp.participants.length;
            if (numParticipants === 0) continue; // No one to split with

            // If any participant has a specific share_amount, use that.
            // Otherwise, divide evenly among participants.
            let totalExplicitShareAmount = 0;
            let numImplicitParticipants = 0;

            exp.participants.forEach(p => {
                if (p.share_amount !== null && p.share_amount !== undefined) {
                    totalExplicitShareAmount += p.share_amount;
                } else {
                    numImplicitParticipants += 1;
                }
            });

            const remainingAmountForImplicit = exp.amount - totalExplicitShareAmount;
            const implicitSharePerPerson = numImplicitParticipants > 0 ? remainingAmountForImplicit / numImplicitParticipants : 0;

            for (const participant of exp.participants) {
              if (participant.user_id !== userId) { // If it's another person
                let share = participant.share_amount;
                if (share === null || share === undefined) {
                    share = implicitSharePerPerson;
                }
                
                if (share > 0) {
                    owedToYouExpenses.push({
                        id: `${exp.id}-${participant.user_id}`, // Unique key
                        description: exp.description,
                        amount: share,
                        group_id: exp.group_id,
                        owes_you_id: participant.user_id,
                        owes_you_name: 'Loading...' // Placeholder
                    });
                }
              }
            }
          }
        }
        setExpenses(owedToYouExpenses);

        // Fetch names of people who owe you
        const peopleOweYouIds = [...new Set(owedToYouExpenses.map(e => e.owes_you_id))];
        if (peopleOweYouIds.length > 0) {
            const usersResponse = await api.get('/auth/users', { params: { ids: peopleOweYouIds.join(',') } }); // Assuming such an endpoint
            const usersMap = new Map(usersResponse.data.map(u => [u.id, u.username || u.email]));
            setExpenses(prev => prev.map(exp => ({
                ...exp,
                owes_you_name: usersMap.get(exp.owes_you_id) || `User ${exp.owes_you_id}`
            })));
        }

      } catch (err) {
        console.error('Error fetching expenses for "Owed To You":', err);
        setError('Failed to load what is owed to you.');
      } finally {
        setLoading(false);
      }
    };

    fetchExpenses();
  }, [userId]);

  if (loading) {
    return <div className="balance-section">Loading amounts owed to you...</div>;
  }

  if (error) {
    return <div className="balance-section error-message">{error}</div>;
  }

  const totalOwedToYou = expenses.reduce((sum, exp) => sum + exp.amount, 0);

  return (
    <div className="balance-section">
      <h4>Owed To You: ${totalOwedToYou.toFixed(2)}</h4>
      {expenses.length === 0 ? (
        <p>No one currently owes you for shared expenses.</p>
      ) : (
        <ul className="owed-list">
          {expenses.map((expense) => (
            <li key={expense.id}>
              {expense.owes_you_name} owes you ${expense.amount.toFixed(2)} for "{expense.description}"
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default OwedToYou;