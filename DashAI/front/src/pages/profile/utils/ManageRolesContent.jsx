import React from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";

import ContentHeader from "../mem-utils/ContentHeader";
import DataTable from "../mem-utils/DataTable";

export default function ManageRolesContent({
  roles,
  selectedRoleId,
  onSelectRole,
}) {
  const theme = useTheme();

  const columns = [
    {
      key: "name",
      label: "Rol",
      width: "2fr",
      render: (role, selected) => (
        <Box sx={{ minWidth: 0 }}>
          <Typography
            variant="body2"
            sx={{
              color: theme.palette.text.primary,
              fontWeight: selected ? 500 : 400,
            }}
          >
            {role.name}
          </Typography>
          <Typography
            variant="caption"
            sx={{ color: theme.palette.text.disabled }}
          >
            {role.description}
          </Typography>
        </Box>
      ),
    },
    { key: "scope", label: "Alcance" },
    {
      key: "permissions",
      label: "Permisos",
      render: (role) => (
        <Typography
          variant="body2"
          sx={{ color: theme.palette.text.secondary }}
        >
          {role.permissions.length}
        </Typography>
      ),
    },
  ];

  return (
    <>
      <ContentHeader
        title="Roles"
        subtitle="Los roles globales aplican a toda la instancia; los de proyecto, a cada proyecto por separado."
      />

      <DataTable
        columns={columns}
        rows={roles}
        selectedId={selectedRoleId}
        onRowClick={(role) => onSelectRole(role.id)}
        actionLabel="Ver permisos"
      />
    </>
  );
}
