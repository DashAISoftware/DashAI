import React from "react";
import PropTypes from "prop-types";
import Chip from "@mui/material/Chip";

const STATUS_COLORS = {
  Activo: "success",
  Inactivo: "default",
  Archivado: "default",
  Pendiente: "warning",
  Aprobada: "success",
  Rechazada: "error",
};

/**
 * Small colored label for the status of users, projects and requests.
 */
export default function StatusChip({ status }) {
  return (
    <Chip
      label={status}
      size="small"
      variant="outlined"
      color={STATUS_COLORS[status] ?? "default"}
    />
  );
}

StatusChip.propTypes = {
  status: PropTypes.string.isRequired,
};
