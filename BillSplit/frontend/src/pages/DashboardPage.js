import React, { useEffect, useState, useCallback } from 'react'; // <--- ADD useCallback here
import { useAuth } from '../hooks/useAuth';
import api from '../api/axiosConfig';
import { Link } from 'react-router-dom'; // Keep Link here for general use, even if GroupList abstracts it
import CreateGroupModal from '../components/Groups/CreateGroupModal';
import OwedByYou from '../components/Dashboard/OwedByYou';
import OwedToYou from '../components/Dashboard/OwedToYou';
import Stats from '../components/Dashboard/Stats';
import GroupList from '../components/Groups/GroupList'; // Ensure GroupList is imported

function DashboardPage() {
  const { appUser, isLoading: authLoading } = useAuth();
  const [groups, setGroups] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loadingGroups, setLoadingGroups] = useState(true);
  const [error, setError] = useState('');

  // 1. Wrap fetchGroups in useCallback
  const fetchGroups = useCallback(async () => {
    if (!appUser) {
      setLoadingGroups(false);
      return;
    }
    setLoadingGroups(true);
    setError('');
    try {
      const response = await api.get('/groups');
      console.log("Dashboard - Fetched groups from backend:", response.data); // Keep this log temporarily for debugging
      setGroups(response.data);
    } catch (err) {
      console.error('Dashboard - Error fetching groups:', err.response?.data?.message || err.message);
      setError('Failed to load groups.');
    } finally {
      setLoadingGroups(false);
    }
  }, [appUser]); // appUser is a dependency for fetchGroups

  // 2. Add fetchGroups to useEffect dependencies
  useEffect(() => {
    fetchGroups();
  }, [fetchGroups]); // <--- Changed: now depends on fetchGroups

  const handleGroupCreated = (newGroup) => {
    console.log("Dashboard - New group object received:", newGroup); // Keep this log temporarily for debugging
    setIsModalOpen(false);
    // 3. Trigger a full re-fetch of groups after a new one is created
    fetchGroups(); // <--- CRUCIAL CHANGE HERE
  };

  if (authLoading) {
    return <div className="container">Loading user data...</div>;
  }

  if (!appUser) {
    return <div className="container">Please log in to view your dashboard.</div>;
  }

  // Temporary logging to inspect `groups` array before passing to GroupList
  console.log("Dashboard - `groups` state before rendering GroupList:", groups);


  return (
    <div className="container dashboard-page">
      <h2>Welcome, {appUser.username}!</h2>

      <section className="my-groups-section">
        <h3>My Groups</h3>
        <button onClick={() => setIsModalOpen(true)} className="button primary">
          + Create New Group
        </button>
        {loadingGroups ? (
          <p>Loading groups...</p>
        ) : error ? (
          <p className="error-message">{error}</p>
        ) : groups.length === 0 ? (
          <p>You haven't joined or created any groups yet.</p>
        ) : (
          // GroupList will receive the `groups` array with proper `id`s from fetchGroups
          <GroupList groups={groups} currentUserId={appUser.id}/>
        )}
      </section>

      <CreateGroupModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onGroupCreated={handleGroupCreated}
      />

      {/* Dashboard Sections */}
      <section className="balances-section">
        <h3>Your Balances</h3>
        <OwedByYou userId={appUser.id} />
        <OwedToYou userId={appUser.id} />
      </section>

      <section className="stats-section">
        <h3>Spending Statistics</h3>
        <Stats userId={appUser.id} />
      </section>
    </div>
  );
}

export default DashboardPage;