import React, { useState } from "react";
import Avatar from "@mui/material/Avatar";
import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import IconButton from "@mui/material/IconButton";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";
import PersonOutlineIcon from "@mui/icons-material/PersonOutline";
import { Link as RouterLink, useLocation, useNavigate } from "react-router-dom";

import { useSession } from "./SessionContext";

/**
 * Menu groups separated by dividers. Items with a `permission` are shown only
 * to users who have it; a group without visible items is hidden.
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
  [
    {
      label: "Gestionar usuarios",
      to: "/app/admin/users",
      permission: "users.manage",
    },
    {
      label: "Gestionar proyectos",
      to: "/app/admin/projects",
      permission: "projects.oversee",
    },
    {
      label: "Gestionar solicitudes",
      to: "/app/admin/requests",
      permission: "requests.review",
    },
    {
      label: "Roles y permisos",
      to: "/app/admin/roles",
      permission: "roles.manage",
    },
  ],
];

/**
 * Options shown when nobody is logged in.
 */
const GUEST_ITEMS = [
  { label: "Iniciar sesión", to: "/app/login" },
  { label: "Crear cuenta", to: "/app/register" },
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
 * Avatar button shown at the right end of the app bar. With a session it opens
 * the user's shortcuts; without one it only offers to log in or register.
 */
export default function UserMenu() {
  const theme = useTheme();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { user, can, logout } = useSession();
  const [anchorEl, setAnchorEl] = useState(null);

  const open = Boolean(anchorEl);
  const handleClose = () => setAnchorEl(null);

  const handleLogout = async () => {
    handleClose();
    await logout();
    navigate("/app");
  };

  const menuGroups = MENU_GROUPS.map((group) =>
    group.filter((item) => !item.permission || can(item.permission)),
  ).filter((group) => group.length > 0);

  const dividerSx = { mx: 1.5, my: 1, borderColor: theme.palette.divider };
  const itemSx = { ...theme.typography.body2, px: 2, py: 1 };
  const avatarBorder = open
    ? theme.palette.primary.main
    : theme.palette.divider;

  const renderItem = (item) => (
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
  );

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
          alt={user?.socialName ?? "Invitado"}
          sx={{
            width: 32,
            height: 32,
            fontSize: 13,
            fontWeight: 500,
            bgcolor: user
              ? `${theme.palette.primary.main}1F`
              : theme.palette.ui.hover,
            color: user
              ? theme.palette.primary.main
              : theme.palette.text.secondary,
            border: `1px solid ${avatarBorder}`,
            transition: "border-color 0.15s",
          }}
        >
          {user ? (
            getInitials(user.socialName)
          ) : (
            <PersonOutlineIcon sx={{ fontSize: 18 }} />
          )}
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
        {user
          ? [
              // Identity
              <Box
                key="identity"
                component="li"
                role="none"
                sx={{ px: 2, py: 1 }}
              >
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
              </Box>,

              ...menuGroups.flatMap((group, index) => [
                <Divider key={`divider-${index}`} sx={dividerSx} />,
                ...group.map(renderItem),
              ]),

              <Divider key="divider-logout" sx={dividerSx} />,
              <MenuItem key="logout" onClick={handleLogout} sx={itemSx}>
                Cerrar sesión
              </MenuItem>,
            ]
          : GUEST_ITEMS.map(renderItem)}
      </Menu>
    </>
  );
}
