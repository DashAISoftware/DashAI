import React from "react";
import { Box, Button, IconButton, Typography } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { useTheme, alpha } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import StepperNavigationFooter from "../shared/StepperNavigationFooter";

const ARROW = 8;

function getArrowSx(placement, bg, borderColor) {
  if (!placement || placement === "center" || placement === "auto") return null;
  const border = `1px solid ${borderColor}`;
  const base = {
    position: "absolute",
    width: ARROW * 2,
    height: ARROW * 2,
    backgroundColor: bg,
    transform: "rotate(45deg)",
    zIndex: 0,
  };
  if (placement.startsWith("top"))
    return {
      ...base,
      bottom: -ARROW,
      left: `calc(50% - ${ARROW}px)`,
      borderBottom: border,
      borderRight: border,
    };
  if (placement.startsWith("bottom"))
    return {
      ...base,
      top: -ARROW,
      left: `calc(50% - ${ARROW}px)`,
      borderTop: border,
      borderLeft: border,
    };
  if (placement.startsWith("left"))
    return {
      ...base,
      right: -ARROW,
      top: `calc(50% - ${ARROW}px)`,
      borderTop: border,
      borderRight: border,
    };
  if (placement.startsWith("right"))
    return {
      ...base,
      left: -ARROW,
      top: `calc(50% - ${ARROW}px)`,
      borderBottom: border,
      borderLeft: border,
    };
  return null;
}

export const CustomTooltip = ({
  index,
  step,
  backProps,
  closeProps,
  primaryProps,
  skipProps,
  tooltipProps,
  size,
  isLastStep,
}) => {
  const { t } = useTranslation(["common"]);
  const theme = useTheme();
  const isInteractive = step.isInteractive;

  const bg = theme.palette.background.paper;
  const borderColor = alpha(theme.palette.primary.main, 0.5);
  const arrowSx = getArrowSx(step.placement, bg, borderColor);

  const getMarginSx = () => {
    if (!step.placement) return {};
    if (step.placement.startsWith("top")) return { marginBottom: "7px" };
    if (step.placement.startsWith("bottom")) return { marginTop: "7px" };
    if (step.placement.startsWith("left")) return { marginRight: "7px" };
    if (step.placement.startsWith("right")) return { marginLeft: "7px" };
    return {};
  };

  return (
    <Box
      {...tooltipProps}
      sx={{
        backgroundColor: bg,
        borderRadius: "8px",
        border: `1px solid ${borderColor}`,
        filter: "drop-shadow(0 4px 20px rgba(0,0,0,0.8))",
        maxWidth: "35ch",
        padding: "20px",
        position: "relative",
        overflow: "visible",
        zIndex: 1,
        ...getMarginSx(),
      }}
    >
      {arrowSx && <Box sx={arrowSx} />}

      <IconButton
        {...closeProps}
        size="small"
        sx={{
          position: "absolute",
          top: 8,
          right: 8,
          color: theme.palette.text.secondary,
          // Above the step counter and content (zIndex 2), which come later
          // in the DOM and would otherwise swallow clicks on the button.
          zIndex: 3,
          "&:hover": { color: theme.palette.text.primary },
        }}
      >
        <CloseIcon fontSize="small" />
      </IconButton>

      <Typography
        variant="overline"
        sx={{
          color: theme.palette.primary.main,
          fontWeight: 700,
          letterSpacing: 1.5,
          lineHeight: 1,
          display: "block",
          mb: 1,
          pr: 4,
          zIndex: 2,
          position: "relative",
        }}
      >
        {t("common:step")} {index + 1} / {size}
      </Typography>

      <Box
        sx={{
          fontSize: "16px",
          lineHeight: "1.6",
          color: theme.palette.text.primary,
          pr: 2,
          position: "relative",
          zIndex: 2,
          "& h3": {
            fontSize: "16px",
            fontWeight: 600,
            marginBottom: "8px",
            marginTop: 0,
            color: theme.palette.text.primary,
          },
          "& p": { marginBottom: "8px", marginTop: 0 },
          "& ul": { marginBottom: "8px", marginTop: "8px" },
          "& li": { marginBottom: "4px" },
          "& strong": {
            fontWeight: 600,
            color: theme.palette.text.primary,
          },
        }}
      >
        {step.content}
      </Box>

      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mt: 1,
          position: "relative",
          zIndex: 2,
        }}
      >
        <Box>
          {!isLastStep && (
            <Button
              {...skipProps}
              variant="text"
              size="small"
              sx={{
                color: theme.palette.text.secondary,
                textTransform: "none",
              }}
            >
              {t("common:skipTour")}
            </Button>
          )}
        </Box>

        <StepperNavigationFooter
          onBack={
            index > 0 && !step.disableBackButton
              ? backProps?.onClick
              : undefined
          }
          onNext={!isInteractive ? primaryProps?.onClick : undefined}
          showBack={index > 0 && !step.disableBackButton}
          showNext={!isInteractive}
          nextLabel={isLastStep ? t("common:finish") : t("common:next")}
          sx={{ mt: 0, pt: 0, borderTop: 0 }}
        />
      </Box>
    </Box>
  );
};
