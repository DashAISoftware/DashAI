import React, { useState } from "react";
import IconButton from "@mui/material/IconButton";
import Tooltip from "@mui/material/Tooltip";
import VpnKeyOutlinedIcon from "@mui/icons-material/VpnKeyOutlined";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import CredentialsDialog from "./CredentialsDialog";

export default function CredentialsButton() {
  const theme = useTheme();
  const { t } = useTranslation("credentials");
  const [open, setOpen] = useState(false);

  const iconBtnSx = {
    width: 32,
    height: 32,
    borderRadius: "4px",
    border: `1px solid ${theme.palette.divider}`,
    color: theme.palette.text.secondary,
    "&:hover": {
      background: theme.palette.ui.hover,
      color: theme.palette.text.primary,
    },
  };

  return (
    <>
      <Tooltip title={t("title")}>
        <IconButton
          onClick={() => setOpen(true)}
          aria-label="credentials"
          sx={iconBtnSx}
        >
          <VpnKeyOutlinedIcon sx={{ fontSize: 18 }} />
        </IconButton>
      </Tooltip>
      <CredentialsDialog open={open} onClose={() => setOpen(false)} />
    </>
  );
}
