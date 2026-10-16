import React from "react";
import PropTypes from "prop-types";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import { useTheme } from "@mui/material/styles";
import { useLocation } from "react-router-dom";

import ProfileSidebar from "./ProfileSidebar";
import PageHeader from "./PageHeader";

/**
 * Shared three-column layout for the profile area:
 * left navigation sidebar, main content and an optional right panel.
 *
 * @param {node} title page title; when omitted no header is rendered
 * @param {node} subtitle text shown below the title
 * @param {node} rightPanel content of the right sidebar (hidden below `lg`)
 * @param {object} contentSx overrides for the main content container
 *
 * A `notice` in the navigation state (e.g. sent by RequirePermission) is shown
 * as a warning above the content.
 */
export default function ProfileLayout({
  title,
  subtitle,
  rightPanel,
  contentSx,
  children,
}) {
  const theme = useTheme();
  const notice = useLocation().state?.notice;

  return (
    <Box
      sx={{
        display: "flex",
        height: "calc(100dvh - 53px)",
        minHeight: 0,
        overflow: "hidden",
      }}
    >
      <ProfileSidebar />

      <Box
        component="main"
        sx={{
          flex: 1,
          minWidth: 0,
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {title && <PageHeader title={title} subtitle={subtitle} />}

        <Box
          sx={{
            flex: 1,
            minHeight: 0,
            overflow: "auto",
            p: 6,
            ...contentSx,
          }}
        >
          {notice && (
            <Alert severity="warning" sx={{ mb: 4 }}>
              {notice}
            </Alert>
          )}
          {children}
        </Box>
      </Box>

      {rightPanel && (
        <Box
          component="aside"
          sx={{
            width: 340,
            flexShrink: 0,
            borderLeft: `1px solid ${theme.palette.divider}`,
            background: theme.palette.background.box,
            display: { xs: "none", lg: "flex" },
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          {rightPanel}
        </Box>
      )}
    </Box>
  );
}

ProfileLayout.propTypes = {
  title: PropTypes.node,
  subtitle: PropTypes.node,
  rightPanel: PropTypes.node,
  contentSx: PropTypes.object,
  children: PropTypes.node,
};
