import { IconButton, Tooltip } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import { useTranslation } from "react-i18next";
import { useTourContext } from "./TourProvider";

export const TourButton = ({ tourKey, disabled = false, disabledMessage }) => {
  const { resetTour, startTour } = useTourContext();
  const theme = useTheme();
  const { t } = useTranslation(["common"]);
  return (
    <Tooltip
      title={
        disabled
          ? (disabledMessage ?? t("common:tourNotAvailable"))
          : t("common:startTour")
      }
      placement="left"
    >
      <IconButton
        onClick={() => {
          if (!disabled) {
            resetTour();
            startTour();
          }
        }}
        sx={{
          position: "fixed",
          top: 64,
          right: 16,
          backgroundColor: disabled
            ? theme.palette.action.disabled
            : theme.palette.primary.main,
          color: theme.palette.primary.contrastText,
          width: 36,
          height: 36,
          "&:hover": {
            backgroundColor: disabled
              ? theme.palette.action.disabled
              : theme.palette.primary.dark,
            transform: disabled ? "none" : "scale(1.05)",
          },
          transition: "all 0.2s ease-in-out",
          boxShadow: 2,
          zIndex: 1101,
          opacity: disabled ? 0.6 : 1,
          cursor: disabled ? "not-allowed" : "pointer",
          pointerEvents: "auto",
        }}
      >
        <HelpOutlineIcon />
      </IconButton>
    </Tooltip>
  );
};
