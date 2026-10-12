import React, { useState } from "react";
import Avatar from "@mui/material/Avatar";
import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import IconButton from "@mui/material/IconButton";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";
import { Link as RouterLink, useLocation } from "react-router-dom";

import { MOCK_USER } from "./mockUser";

/**
 * Menu groups separated by dividers.
 */
const MENU_GROUPS = [
  [
    { label: "Mi perfil", to: "/app/profile" },
    { label: "Mis proyectos", to: "/app/profile/projects" },
    { label: "Mis solicitudes", to: "/app/profile/requests" },
  ],
  [
    { label: "Gestionar perfil", to: "/app/profile/account" },
    { label: "Cambiar contraseña", to: "/app/profile/password" },
  ],
];

/**
 * Extra group shown only to administrators.
 */
const ADMIN_GROUP = [
  { label: "Gestionar usuarios", to: "/app/admin/users" },
  { label: "Gestionar proyectos", to: "/app/admin/projects" },
  { label: "Gestionar solicitudes", to: "/app/admin/requests" },
  { label: "Roles y permisos", to: "/app/admin/roles" },
];

function getInitials(name) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0].toUpperCase())
    .join("");
}

/**
 * Avatar button shown at the right end of the app bar. Opens a dropdown
 * with the user's name and shortcuts to the profile views.
 */
export default function UserMenu() {
  const theme = useTheme();
  const { pathname } = useLocation();
  const [anchorEl, setAnchorEl] = useState(null);

  const user = MOCK_USER;
  const menuGroups = user.isAdmin ? [...MENU_GROUPS, ADMIN_GROUP] : MENU_GROUPS;
  const open = Boolean(anchorEl);
  const handleClose = () => setAnchorEl(null);

  const dividerSx = { mx: 1.5, my: 1, borderColor: theme.palette.divider };
  const itemSx = { ...theme.typography.body2, px: 2, py: 1 };
  const avatarBorder = open
    ? theme.palette.primary.main
    : theme.palette.divider;

  return (
    <>
      <IconButton
        onClick={(event) => setAnchorEl(event.currentTarget)}
        aria-label="menú de usuario"
        aria-controls={open ? "user-menu" : undefined}
        aria-haspopup="true"
        aria-expanded={open ? "true" : undefined}
        sx={{ p: 0 }}
      >
        <Avatar
          alt={user.socialName}
          sx={{
            width: 32,
            height: 32,
            fontSize: 13,
            fontWeight: 500,
            bgcolor: `${theme.palette.primary.main}1F`,
            color: theme.palette.primary.main,
            border: `1px solid ${avatarBorder}`,
            transition: "border-color 0.15s",
          }}
        >
          {getInitials(user.socialName)}
        </Avatar>
      </IconButton>

      <Menu
        id="user-menu"
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        transformOrigin={{ vertical: "top", horizontal: "right" }}
        slotProps={{
          paper: {
            sx: {
              mt: 1,
              minWidth: 220,
              border: `1px solid ${theme.palette.divider}`,
              background: theme.palette.background.box,
            },
          },
        }}
      >
        {/* Identity */}
        <Box component="li" role="none" sx={{ px: 2, py: 1 }}>
          <Typography
            variant="body2"
            sx={{ color: theme.palette.text.primary, fontWeight: 500 }}
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

        {menuGroups.flatMap((group, index) => [
          <Divider key={`divider-${index}`} sx={dividerSx} />,
          ...group.map((item) => (
            <MenuItem
              key={item.label}
              component={RouterLink}
              to={item.to}
              onClick={handleClose}
              selected={pathname === item.to}
              sx={itemSx}
            >
              {item.label}
            </MenuItem>
          )),
        ])}

        <Divider sx={dividerSx} />

        {/* No authentication yet: only closes the menu */}
        <MenuItem onClick={handleClose} sx={itemSx}>
          Cerrar sesión
        </MenuItem>
      </Menu>
    </>
  );
}
