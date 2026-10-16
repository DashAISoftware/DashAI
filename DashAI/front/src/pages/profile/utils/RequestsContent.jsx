import React from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";
import AddIcon from "@mui/icons-material/Add";

import ContentHeader from "../mem-utils/ContentHeader";
import ActionButton from "../mem-utils/ActionButton";
import DataTable from "../mem-utils/DataTable";
import { getUserRequests } from "../mem-utils/mockInstance";
import { useSession } from "../mem-utils/SessionContext";

export default function RequestsContent({ selectedRequest, onSelectRequest }) {
  const theme = useTheme();
  const { user } = useSession();
  const requests = getUserRequests(user.id);

  const columns = [
    {
      key: "subject",
      label: "Solicitud",
      width: "2fr",
      render: (request, selected) => (
        <Box sx={{ minWidth: 0 }}>
          <Typography
            variant="body2"
            sx={{
              color: theme.palette.text.primary,
              fontWeight: selected ? 500 : 400,
            }}
          >
            {request.subject}
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: theme.palette.text.disabled,
              fontFamily: '"Geist Mono", monospace',
            }}
          >
            {request.id}
          </Typography>
        </Box>
      ),
    },
    {
      key: "project",
      label: "Proyecto",
      render: (request) => (
        <Typography
          variant="body2"
          sx={{
            color: theme.palette.text.secondary,
            fontFamily: '"Geist Mono", monospace',
            fontSize: "0.8rem",
          }}
        >
          {request.project}
        </Typography>
      ),
    },
    { key: "status", label: "Estado" },
  ];

  return (
    <>
      <ContentHeader
        title="Solicitudes"
        subtitle={`${requests.length} solicitudes asociadas a tu cuenta`}
        action={<ActionButton icon={AddIcon}>Solicitar acceso</ActionButton>}
      />

      <DataTable
        columns={columns}
        rows={requests}
        selectedId={selectedRequest?.id}
        onRowClick={onSelectRequest}
        actionLabel="Ver detalles"
      />
    </>
  );
}
