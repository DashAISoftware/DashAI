import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import PropTypes from "prop-types";

import * as authService from "./authService";
import { getRolePermissions } from "./mockInstance";

const SessionContext = createContext(null);

/**
 * Keeps the logged-in user and the list of accounts, and exposes the session
 * actions to the whole app through `useSession()`.
 */
export function SessionProvider({ children }) {
  const [user, setUser] = useState(null);
  const [users, setUsers] = useState([]);
  // True until the stored session has been read; guards wait for it
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([authService.getCurrentUser(), authService.getUsers()]).then(
      ([currentUser, allUsers]) => {
        setUser(currentUser);
        setUsers(allUsers);
        setLoading(false);
      },
    );
  }, []);

  const login = useCallback(async (email, password) => {
    const loggedUser = await authService.login(email, password);
    setUser(loggedUser);
    return loggedUser;
  }, []);

  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
  }, []);

  const register = useCallback(async (data) => {
    const newUser = await authService.register(data);
    setUsers(await authService.getUsers());
    return newUser;
  }, []);

  const updateUser = useCallback(async (userId, changes) => {
    const allUsers = await authService.updateUser(userId, changes);
    setUsers(allUsers);
    setUser((previous) =>
      previous?.id === userId
        ? allUsers.find((candidate) => candidate.id === userId)
        : previous,
    );
  }, []);

  const changePassword = useCallback(
    (currentPassword, newPassword) =>
      authService.changePassword(user.id, currentPassword, newPassword),
    [user],
  );

  // Permissions come from the global role; project roles are not checked yet
  const can = useCallback(
    (permission) =>
      Boolean(user) && getRolePermissions(user.globalRole).includes(permission),
    [user],
  );

  const value = useMemo(
    () => ({
      user,
      users,
      loading,
      isAuthenticated: Boolean(user),
      login,
      logout,
      register,
      updateUser,
      changePassword,
      can,
    }),
    [
      user,
      users,
      loading,
      login,
      logout,
      register,
      updateUser,
      changePassword,
      can,
    ],
  );

  return (
    <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
  );
}

SessionProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSession must be used within a SessionProvider");
  }
  return context;
}
