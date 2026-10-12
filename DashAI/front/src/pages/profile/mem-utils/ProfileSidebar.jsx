import React from "react";
import Box from "@mui/material/Box";
import { useTheme } from "@mui/material/styles";
import { Link as RouterLink, useLocation } from "react-router-dom";

import SectionLabel from "./SectionLabel";
import { MOCK_USER } from "./mockUser";
import { PROFILE_SIDEBAR } from "./profileNavigation";

function SidebarLink({ href, Icon, label, active }) {
  const theme = useTheme();

  return (
    <Box
      component={RouterLink}
      to={href}
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 2,
        px: 4,
        py: 2,
        borderLeft: "2px solid",
        borderLeftColor: active ? theme.palette.primary.main : "transparent",
        textDecoration: "none",
        color: active
          ? theme.palette.text.primary
          : theme.palette.text.secondary,
        background: active ? theme.palette.ui.hover : "transparent",
        ...theme.typography.navItem,
        transition: "background 0.15s, color 0.15s, border-color 0.15s",

        "&:hover": {
          background: theme.palette.ui.hover,
          color: theme.palette.text.primary,
          borderLeftColor: active
            ? theme.palette.primary.main
            : `${theme.palette.primary.main}38`,
        },
      }}
    >
      <Icon
        sx={{
          fontSize: 13,
          opacity: active ? 1 : 0.6,
          flexShrink: 0,
        }}
      />

      <Box component="span" sx={{ flexGrow: 1 }}>
        {label}
      </Box>
    </Box>
  );
}

/**
 * Left navigation of the profile area. Highlights the link matching the
 * current route.
 */
export default function ProfileSidebar() {
  const theme = useTheme();
  const { pathname } = useLocation();

  return (
    <Box
      component="aside"
      sx={{
        width: 230,
        flexShrink: 0,
        borderRight: `1px solid ${theme.palette.divider}`,
        background: theme.palette.background.box,
        display: { xs: "none", sm: "flex" },
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {PROFILE_SIDEBAR.filter(
        (section) => !section.adminOnly || MOCK_USER.isAdmin,
      ).map((section) => (
        <Box
          key={section.key}
          sx={{
            pb: 4,
            borderBottom: `1px solid ${theme.palette.ui.borderLight}`,
          }}
        >
          <SectionLabel sx={{ px: 4, pt: 2, pb: 1 }}>
            {section.label}
          </SectionLabel>

          {section.links.map(({ key, label, href, Icon }) => (
            <SidebarLink
              key={key}
              href={href}
              Icon={Icon}
              label={label}
              active={pathname === href}
            />
          ))}
        </Box>
      ))}
    </Box>
  );
}
