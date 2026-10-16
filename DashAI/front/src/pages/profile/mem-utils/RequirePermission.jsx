import React from "react";
import PropTypes from "prop-types";
import { Navigate, Outlet } from "react-router-dom";

import RequireAuth from "./RequireAuth";
import { useSession } from "./SessionContext";

/**
 * Route guard for views that need a specific permission. Without a session
 * it behaves like RequireAuth; with a session but without the permission it
 * sends the user to their profile with a notice.
 *
 * Only hides the UI; the backend must also enforce permissions on every
 * endpoint.
 */
export default function RequirePermission({ permission, children }) {
  const { isAuthenticated, loading, can } = useSession();

  if (loading) return null;
  if (!isAuthenticated) return <RequireAuth />;

  if (!can(permission)) {
    return (
      <Navigate
        to="/app/profile"
        replace
        state={{ notice: "No tienes permisos para acceder a esa sección." }}
      />
    );
  }

  return children ?? <Outlet />;
}

RequirePermission.propTypes = {
  permission: PropTypes.string.isRequired,
  children: PropTypes.node,
};
