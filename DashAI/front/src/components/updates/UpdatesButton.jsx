import React, { useEffect, useState } from "react";
import Badge from "@mui/material/Badge";
import IconButton from "@mui/material/IconButton";
import Tooltip from "@mui/material/Tooltip";
import SystemUpdateAltOutlinedIcon from "@mui/icons-material/SystemUpdateAltOutlined";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import { getUpdateCheck } from "../../api/system";
import UpdatesDialog from "./UpdatesDialog";

export default function UpdatesButton() {
  const theme = useTheme();
  const { t } = useTranslation("updates");
  const [open, setOpen] = useState(false);
  const [info, setInfo] = useState(null);

  // The backend caches the GitHub answer, so one request per app load is
  // enough. A failed request leaves info empty and the dialog says so.
  useEffect(() => {
    getUpdateCheck()
      .then(setInfo)
      .catch(() => setInfo(null));
  }, []);

  const updateAvailable = Boolean(info?.update_available);

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
      <Tooltip
        title={
          updateAvailable
            ? t("updateAvailableTooltip", { version: info.latest_version })
            : t("title")
        }
      >
        <IconButton
          onClick={() => setOpen(true)}
          aria-label="updates"
          sx={iconBtnSx}
        >
          <Badge
            color="primary"
            variant="dot"
            invisible={!updateAvailable}
            overlap="circular"
          >
            <SystemUpdateAltOutlinedIcon sx={{ fontSize: 18 }} />
          </Badge>
        </IconButton>
      </Tooltip>
      <UpdatesDialog open={open} onClose={() => setOpen(false)} info={info} />
    </>
  );
}
