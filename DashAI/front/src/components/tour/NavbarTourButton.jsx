import React, { useState, useEffect } from "react";
import { IconButton, Tooltip } from "@mui/material";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import { useTourRegistry } from "../../contexts/TourRegistryContext";

const NOOP_REGISTRY = {
  getActive: () => null,
  subscribe: () => () => {},
};

export default function NavbarTourButton() {
  const theme = useTheme();
  const { t } = useTranslation(["common"]);
  const registry = useTourRegistry() ?? NOOP_REGISTRY;
  const [active, setActive] = useState(() => registry.getActive());

  useEffect(() => {
    setActive(registry.getActive());
    return registry.subscribe(() => {
      setActive(registry.getActive());
    });
  }, [registry]);

  const noTour = !active;
  const isDisabled = noTour || active.disabled;

  const title = noTour
    ? t("common:noTourAvailable")
    : active.disabled
      ? active.disabledMessage
      : t("common:startTour");

  const handleClick = () => {
    if (active && !active.disabled) {
      active.resetTour();
      active.startTour();
    }
  };

  return (
    <Tooltip title={title} placement="bottom">
      <IconButton
        onClick={isDisabled ? undefined : handleClick}
        aria-label="start tour"
        sx={{
          width: 32,
          height: 32,
          borderRadius: "4px",
          border: `1px solid ${theme.palette.divider}`,
          color: isDisabled
            ? theme.palette.text.disabled
            : theme.palette.text.secondary,
          opacity: isDisabled ? 0.5 : 1,
          cursor: isDisabled ? "default" : "pointer",
          "&:hover": isDisabled
            ? { background: "transparent", color: theme.palette.text.disabled }
            : {
                background: theme.palette.ui.hover,
                color: theme.palette.text.primary,
              },
        }}
      >
        <HelpOutlineIcon sx={{ fontSize: 18 }} />
      </IconButton>
    </Tooltip>
  );
}
