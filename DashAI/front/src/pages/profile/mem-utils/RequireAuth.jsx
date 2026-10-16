import React from "react";
import PropTypes from "prop-types";
import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useSession } from "./SessionContext";

/**
 * Route guard: without a session, redirects to the login view and remembers
 * the requested path to come back after logging in. Works both wrapping an
 * element and as a layout route (renders the nested routes).
 *
 * Only hides the UI; the backend must also check the session on every
 * endpoint.
 */
export default function RequireAuth({ children }) {
  const { isAuthenticated, loading } = useSession();
  const location = useLocation();

  if (loading) return null;

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/app/login"
        replace
        state={{
          from: `${location.pathname}${location.search}`,
          reason: "auth",
        }}
      />
    );
  }

  return children ?? <Outlet />;
}

RequireAuth.propTypes = {
  children: PropTypes.node,
};
