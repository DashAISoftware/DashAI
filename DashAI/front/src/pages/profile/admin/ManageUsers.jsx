import React, { useState } from "react";
import Button from "@mui/material/Button";
import MenuItem from "@mui/material/MenuItem";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";

import ProfileLayout from "../mem-utils/ProfileLayout";
import DetailPanel, {
  DetailField,
  DetailSection,
} from "../mem-utils/DetailPanel";
import StatusChip from "../mem-utils/StatusChip";
import {
  CURRENT_USER_ID,
  GLOBAL_ROLES,
  MOCK_PROJECTS,
  MOCK_USERS,
} from "../mem-utils/mockInstance";
import ManageUsersContent from "../utils/ManageUsersContent";

function UserDetails({ user, onChange, onClose }) {
  const theme = useTheme();

  // An admin cannot demote or deactivate their own account
  const isSelf = user?.id === CURRENT_USER_ID;

  const memberships = user
    ? MOCK_PROJECTS.flatMap((project) =>
        project.members
          .filter((member) => member.userId === user.id)
          .map((member) => ({ project, role: member.role })),
      )
    : [];

  return (
    <DetailPanel
      title={user?.name}
      subtitle={user?.email}
      onClose={onClose}
      emptyMessage="Selecciona un usuario para gestionar su cuenta."
    >
      {user && (
        <>
          <DetailSection label="Información">
            <DetailField label="Nickname">@{user.nickname}</DetailField>
            <DetailField label="Estado">
              <StatusChip status={user.active ? "Activo" : "Inactivo"} />
            </DetailField>
          </DetailSection>

          <DetailSection label="Rol global">
            <TextField
              select
              size="small"
              fullWidth
              value={user.globalRole}
              onChange={(event) => onChange({ globalRole: event.target.value })}
              disabled={isSelf}
              helperText={
                isSelf
                  ? "No puedes cambiar tu propio rol."
                  : "Define el acceso del usuario a toda la instancia."
              }
            >
              {GLOBAL_ROLES.map((role) => (
                <MenuItem key={role} value={role}>
                  {role}
                </MenuItem>
              ))}
            </TextField>
          </DetailSection>

          <DetailSection label="Proyectos">
            {memberships.length === 0 ? (
              <Typography
                variant="body2"
                sx={{ color: theme.palette.text.disabled }}
              >
                No pertenece a ningún proyecto.
              </Typography>
            ) : (
              memberships.map(({ project, role }) => (
                <DetailField key={project.id} label={project.name}>
                  {role}
                </DetailField>
              ))
            )}
          </DetailSection>

          <DetailSection label="Acceso">
            <Button
              variant="outlined"
              size="small"
              color={user.active ? "error" : "primary"}
              disabled={isSelf}
              onClick={() => onChange({ active: !user.active })}
              sx={{ textTransform: "none" }}
            >
              {user.active ? "Desactivar cuenta" : "Reactivar cuenta"}
            </Button>
            <Typography
              variant="caption"
              sx={{
                display: "block",
                mt: 1,
                color: theme.palette.text.disabled,
              }}
            >
              Una cuenta desactivada no puede iniciar sesión, pero conserva sus
              datos y proyectos.
            </Typography>
          </DetailSection>
        </>
      )}
    </DetailPanel>
  );
}

export default function ManageUsers() {
  const [users, setUsers] = useState(MOCK_USERS);
  const [selectedId, setSelectedId] = useState(null);

  const selectedUser = users.find((user) => user.id === selectedId) ?? null;

  const updateSelectedUser = (changes) =>
    setUsers((previous) =>
      previous.map((user) =>
        user.id === selectedId ? { ...user, ...changes } : user,
      ),
    );

  return (
    <ProfileLayout
      title="Gestionar usuarios"
      subtitle="Administra las cuentas de la instancia, su rol global y su acceso."
      rightPanel={
        <UserDetails
          user={selectedUser}
          onChange={updateSelectedUser}
          onClose={() => setSelectedId(null)}
        />
      }
    >
      <ManageUsersContent
        users={users}
        selectedUserId={selectedId}
        onSelectUser={setSelectedId}
      />
    </ProfileLayout>
  );
}
