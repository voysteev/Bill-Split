import React, { createContext, useContext, useEffect, useState } from 'react';
import { onAuthStateChanged, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut } from 'firebase/auth';
import { auth } from '../firebase';
import api from '../api/axiosConfig';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [appUser, setAppUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        // Firebase user exists, now get/verify ID token with your backend
        try {
          const idToken = await firebaseUser.getIdToken();
          const response = await api.post('/auth/login', { idToken });
          const { token, user: backendUser } = response.data;
          
          localStorage.setItem('jwt_token', token);
          setUser(firebaseUser);
          setAppUser(backendUser);
          setIsAuthenticated(true);
        } catch (error) {
          console.error("Error verifying Firebase ID token with backend:", error);
          // If backend verification fails, log out Firebase user
          await signOut(auth);
          localStorage.removeItem('jwt_token');
          setUser(null);
          setAppUser(null);
          setIsAuthenticated(false);
        }
      } else {
        localStorage.removeItem('jwt_token');
        setUser(null);
        setAppUser(null);
        setIsAuthenticated(false);
      }
      setIsLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const signup = async (email, password, username) => {
    setIsLoading(true);
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const firebaseUser = userCredential.user;
      
      // Update Firebase user profile with username (optional)
      // await updateProfile(firebaseUser, { displayName: username }); // This is for Firebase profile, not Flask

      const idToken = await firebaseUser.getIdToken();
      const response = await api.post('/auth/register', { idToken, username }); // Send idToken and username to Flask
      const { token, user: backendUser } = response.data;

      localStorage.setItem('jwt_token', token);
      setUser(firebaseUser);
      setAppUser(backendUser);
      setIsAuthenticated(true);
      setIsLoading(false);
      return { success: true };
    } catch (error) {
      console.error("Signup error:", error);
      setIsLoading(false);
      return { success: false, error: error.message };
    }
  };

  const login = async (email, password) => {
    setIsLoading(true);
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      const firebaseUser = userCredential.user;
      const idToken = await firebaseUser.getIdToken();

      const response = await api.post('/auth/login', { idToken });
      const { token, user: backendUser } = response.data;
      
      localStorage.setItem('jwt_token', token);
      setUser(firebaseUser);
      setAppUser(backendUser);
      setIsAuthenticated(true);
      setIsLoading(false);
      return { success: true };
    } catch (error) {
      console.error("Login error:", error);
      setIsLoading(false);
      return { success: false, error: error.message };
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await signOut(auth);
      localStorage.removeItem('jwt_token');
      setUser(null);
      setAppUser(null);
      setIsAuthenticated(false);
      setIsLoading(false);
      return { success: true };
    } catch (error) {
      console.error("Logout error:", error);
      setIsLoading(false);
      return { success: false, error: error.message };
    }
  };

  return (
    <AuthContext.Provider value={{ user, appUser, isAuthenticated, isLoading, signup, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);