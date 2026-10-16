import React from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";

import ContentHeader from "../mem-utils/ContentHeader";
import DataTable from "../mem-utils/DataTable";
import StatusChip from "../mem-utils/StatusChip";

export default function ManageUsersContent({
  users,
  selectedUserId,
  onSelectUser,
}) {
  const theme = useTheme();
  const activeCount = users.filter((user) => user.active).length;

  const columns = [
    {
      key: "socialName",
      label: "Usuario",
      width: "2fr",
      render: (user, selected) => (
        <Box sx={{ minWidth: 0 }}>
          <Typography
            variant="body2"
            sx={{
              color: theme.palette.text.primary,
              fontWeight: selected ? 500 : 400,
            }}
          >
            {user.socialName}
          </Typography>
          <Typography
            variant="caption"
            sx={{ color: theme.palette.text.disabled }}
          >
            @{user.nickname}
          </Typography>
        </Box>
      ),
    },
    { key: "email", label: "Correo", width: "2fr" },
    { key: "globalRole", label: "Rol global" },
    {
      key: "active",
      label: "Estado",
      render: (user) => (
        <StatusChip status={user.active ? "Activo" : "Inactivo"} />
      ),
    },
  ];

  return (
    <>
      <ContentHeader
        title="Usuarios"
        subtitle={`${users.length} usuarios · ${activeCount} activos`}
      />

      <DataTable
        columns={columns}
        rows={users}
        selectedId={selectedUserId}
        onRowClick={(user) => onSelectUser(user.id)}
        actionLabel="Ver detalles"
      />
    </>
  );
}
