import React, { useEffect, useState } from 'react';
import api from '../../api/axiosConfig';

function Stats({ userId }) {
  const [totalSpent, setTotalSpent] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchStats = async () => {
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

        // Calculate total amount paid by the user
        const total = userExpenses.reduce((sum, exp) => {
            if (exp.payer_id === userId) {
                return sum + exp.amount;
            }
            return sum;
        }, 0);
        setTotalSpent(total);

      } catch (err) {
        console.error('Error fetching stats:', err);
        setError('Failed to load spending statistics.');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [userId]);

  if (loading) {
    return <div className="balance-section">Loading your spending stats...</div>;
  }

  if (error) {
    return <div className="balance-section error-message">{error}</div>;
  }

  return (
    <div className="balance-section">
      <h4>Your Total Spending: ${totalSpent.toFixed(2)}</h4>
      <p>This includes all expenses you've paid for across all your groups.</p>
      {/* You can add more complex stats here later, like spending by group, category, etc. */}
    </div>
  );
}

export default Stats;