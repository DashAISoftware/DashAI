import React from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";

import ContentHeader from "../mem-utils/ContentHeader";
import DataTable from "../mem-utils/DataTable";
import StatusChip from "../mem-utils/StatusChip";
import { getProjectName, getUserName } from "../mem-utils/mockInstance";

export default function ManageRequestsContent({
  requests,
  selectedRequestId,
  onSelectRequest,
}) {
  const theme = useTheme();
  const pendingCount = requests.filter(
    (request) => request.status === "Pendiente",
  ).length;

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
      key: "requesterId",
      label: "Solicitante",
      render: (request) => (
        <Typography
          variant="body2"
          sx={{ color: theme.palette.text.secondary }}
        >
          {getUserName(request.requesterId)}
        </Typography>
      ),
    },
    {
      key: "projectId",
      label: "Proyecto",
      render: (request) => (
        <Typography
          variant="body2"
          sx={{ color: theme.palette.text.secondary }}
        >
          {getProjectName(request.projectId)}
        </Typography>
      ),
    },
    {
      key: "status",
      label: "Estado",
      render: (request) => <StatusChip status={request.status} />,
    },
  ];

  return (
    <>
      <ContentHeader
        title="Solicitudes de acceso"
        subtitle={`${requests.length} solicitudes · ${pendingCount} pendientes`}
      />

      <DataTable
        columns={columns}
        rows={requests}
        selectedId={selectedRequestId}
        onRowClick={(request) => onSelectRequest(request.id)}
        actionLabel="Revisar"
      />
    </>
  );
}
