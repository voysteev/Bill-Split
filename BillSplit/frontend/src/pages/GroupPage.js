import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../api/axiosConfig';
import { useAuth } from '../hooks/useAuth';
import AddExpenseForm from '../components/Expenses/AddExpenseForm';
import ExpenseList from '../components/Expenses/ExpenseList';

function GroupPage() {
  const { groupId } = useParams();
  const { appUser } = useAuth();
  const [group, setGroup] = useState(null);
  const [members, setMembers] = useState([]); // Full member objects
  const [expenses, setExpenses] = useState([]);
  const [settlementResult, setSettlementResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isAddExpenseFormVisible, setIsAddExpenseFormVisible] = useState(false);

  const fetchGroupDetails = async () => {
    setLoading(true);
    setError('');
    try {
      const groupResponse = await api.get(`/groups/${groupId}`);
      setGroup(groupResponse.data);

      // Fetch member details
      const memberIds = groupResponse.data.members;
      if (memberIds && memberIds.length > 0) {
        // As Firestore doesn't allow direct 'IN' queries for collection IDs across top-level collections
        // and we are using Flask as a proxy, we'd need a backend endpoint for this.
        // For now, we'll fetch them one by one or create a specific backend endpoint later.
        // For simplicity, let's assume we fetch all users and filter, or make individual calls.
        // A better approach would be to have a /api/users endpoint that accepts a list of IDs.
        // For now, let's just use the IDs or fetch all and filter.

        // Simulating fetching member names - ideally from a new Flask API /users?ids=x,y,z
        const fetchedMembers = [];
        for (const memberId of memberIds) {
          try {
            const userRes = await api.get(`/auth/me?user_id=${memberId}`); // Assuming a /me?user_id= endpoint or similar
            if (userRes.data.id === memberId) {
                fetchedMembers.push(userRes.data);
            }
          } catch (fetchErr) {
            console.warn(`Could not fetch details for member ${memberId}:`, fetchErr);
            fetchedMembers.push({ id: memberId, username: `Unknown User (${memberId})` }); // Fallback
          }
        }
        setMembers(fetchedMembers);
      } else {
        setMembers([]);
      }

      const expensesResponse = await api.get(`/expenses/group/${groupId}`);
      setExpenses(expensesResponse.data);

      const settlementResponse = await api.get(`/settlements/${groupId}`);
      setSettlementResult(settlementResponse.data);

    } catch (err) {
      console.error('Error fetching group details:', err);
      setError('Failed to load group details. ' + (err.response?.data?.message || err.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (appUser && groupId) {
      fetchGroupDetails();
    }
  }, [appUser, groupId]);

  const handleExpenseAdded = (newExpense) => {
    setExpenses((prev) => [...prev, newExpense]);
    setIsAddExpenseFormVisible(false);
    // Re-fetch settlements after adding an expense to update balances
    fetchGroupDetails(); 
  };

  const handleExpenseUpdated = (updatedExpense) => {
    setExpenses((prev) => prev.map(exp => exp.id === updatedExpense.id ? updatedExpense : exp));
    fetchGroupDetails(); 
  };

  const handleExpenseDeleted = (deletedExpenseId) => {
    setExpenses((prev) => prev.filter(exp => exp.id !== deletedExpenseId));
    fetchGroupDetails(); 
  };


  if (loading) {
    return <div className="container">Loading group details...</div>;
  }

  if (error) {
    return <div className="container error-message">{error}</div>;
  }

  if (!group) {
    return <div className="container">Group not found.</div>;
  }

  return (
    <div className="container group-detail-page">
      <h2>{group.name}</h2>
      {group.description && <p className="group-description">{group.description}</p>}

      <section className="group-members">
        <h3>Members</h3>
        <ul className="member-list">
          {members.length > 0 ? (
            members.map((member) => (
              <li key={member.id}>
                {member.username || member.email} {appUser?.id === member.id && "(You)"}
                {group.owner_id === member.id && " (Owner)"}
              </li>
            ))
          ) : (
            <li>No members found.</li>
          )}
        </ul>
        {/* Add member functionality (e.g., modal) */}
        {group.owner_id === appUser?.id && (
            <button className="button secondary">Manage Members</button>
        )}
      </section>

      <section className="group-expenses">
        <h3>Expenses</h3>
        <button 
          onClick={() => setIsAddExpenseFormVisible(!isAddExpenseFormVisible)} 
          className="button primary"
        >
          {isAddExpenseFormVisible ? "Cancel Add Expense" : "+ Add New Expense"}
        </button>
        {isAddExpenseFormVisible && (
          <AddExpenseForm 
            groupId={group.id} 
            groupMembers={members} 
            onExpenseAdded={handleExpenseAdded} 
          />
        )}
        <ExpenseList 
            expenses={expenses} 
            groupMembers={members} 
            onExpenseUpdated={handleExpenseUpdated}
            onExpenseDeleted={handleExpenseDeleted}
            currentUserId={appUser?.id}
            groupOwnerId={group.owner_id}
        />
      </section>

      <section className="group-settlement">
        <h3>Settlements</h3>
        {settlementResult && (
          <div>
            <h4>Current Balances:</h4>
            <ul className="balances-list">
              {Object.entries(settlementResult.balances).map(([userId, balance]) => {
                const user = members.find(m => m.id === userId);
                return (
                  <li key={userId}>
                    {user ? user.username : `User ${userId}`}: {balance >= 0 ? 'Owed' : 'Owes'} ${Math.abs(balance).toFixed(2)}
                  </li>
                );
              })}
            </ul>

            <h4>Transactions to Settle:</h4>
            {settlementResult.transactions.length > 0 ? (
              <ul className="transactions-list">
                {settlementResult.transactions.map((t, index) => (
                  <li key={index}>
                    {t.payer_name || `User ${t.payer_id}`} owes {t.receiver_name || `User ${t.receiver_id}`} ${t.amount.toFixed(2)}
                  </li>
                ))}
              </ul>
            ) : (
              <p>Everyone is settled!</p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}

export default GroupPage;