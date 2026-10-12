import React, { useState } from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";

import ProfileLayout from "../mem-utils/ProfileLayout";
import DetailPanel, {
  DetailField,
  DetailSection,
} from "../mem-utils/DetailPanel";
import StatusChip from "../mem-utils/StatusChip";
import {
  MOCK_REQUESTS,
  getProjectName,
  getUserName,
} from "../mem-utils/mockInstance";
import ManageRequestsContent from "../utils/ManageRequestsContent";

function RequestReview({ request, onDecide, onClose }) {
  const theme = useTheme();

  return (
    <DetailPanel
      title={request?.subject}
      subtitle={request?.id}
      onClose={onClose}
      emptyMessage="Selecciona una solicitud para revisarla."
    >
      {request && (
        <>
          <DetailSection label="Información">
            <DetailField label="Solicitante">
              {getUserName(request.requesterId)}
            </DetailField>
            <DetailField label="Proyecto">
              {getProjectName(request.projectId)}
            </DetailField>
            <DetailField label="Estado">
              <StatusChip status={request.status} />
            </DetailField>
          </DetailSection>

          <DetailSection label="Permisos solicitados">
            {request.permissions.map((permission) => (
              <Typography
                key={permission}
                variant="body2"
                sx={{
                  py: 0.5,
                  color: theme.palette.text.secondary,
                  fontFamily: '"Geist Mono", monospace',
                  fontSize: "0.8rem",
                }}
              >
                {permission}
              </Typography>
            ))}
          </DetailSection>

          <DetailSection label="Motivo">
            <Typography
              variant="body2"
              sx={{ color: theme.palette.text.secondary, lineHeight: 1.6 }}
            >
              {request.reason}
            </Typography>
          </DetailSection>

          {request.status === "Pendiente" && (
            <DetailSection label="Decisión">
              <Box sx={{ display: "flex", gap: 1 }}>
                <Button
                  variant="contained"
                  size="small"
                  color="success"
                  disableElevation
                  onClick={() => onDecide("Aprobada")}
                  sx={{ textTransform: "none" }}
                >
                  Aprobar
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  color="error"
                  onClick={() => onDecide("Rechazada")}
                  sx={{ textTransform: "none" }}
                >
                  Rechazar
                </Button>
              </Box>
              <Typography
                variant="caption"
                sx={{
                  display: "block",
                  mt: 1,
                  color: theme.palette.text.disabled,
                }}
              >
                Al aprobar, el usuario recibe los permisos solicitados en el
                proyecto.
              </Typography>
            </DetailSection>
          )}
        </>
      )}
    </DetailPanel>
  );
}

export default function ManageRequests() {
  const [requests, setRequests] = useState(MOCK_REQUESTS);
  const [selectedId, setSelectedId] = useState(null);

  const selectedRequest =
    requests.find((request) => request.id === selectedId) ?? null;

  const decide = (status) =>
    setRequests((previous) =>
      previous.map((request) =>
        request.id === selectedId ? { ...request, status } : request,
      ),
    );

  return (
    <ProfileLayout
      title="Gestionar solicitudes"
      subtitle="Revisa las solicitudes de acceso y permisos de los usuarios de la instancia."
      rightPanel={
        <RequestReview
          request={selectedRequest}
          onDecide={decide}
          onClose={() => setSelectedId(null)}
        />
      }
    >
      <ManageRequestsContent
        requests={requests}
        selectedRequestId={selectedId}
        onSelectRequest={setSelectedId}
      />
    </ProfileLayout>
  );
}
