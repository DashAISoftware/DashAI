import React from "react";
import PropTypes from "prop-types";
import { Navigate } from "react-router-dom";

import { MOCK_USER } from "./mockUser";

/**
 * Route guard for the administration views: users without admin access are
 * sent back to their profile. Only hides the UI; the backend must also
 * enforce permissions on every endpoint.
 */
export default function RequireAdmin({ children }) {
  if (!MOCK_USER.isAdmin) return <Navigate to="/app/profile" replace />;
  return children;
}

RequireAdmin.propTypes = {
  children: PropTypes.node.isRequired,
};
