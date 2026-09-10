import { forwardRef, useRef, useLayoutEffect } from "react";
import { Box, Typography, ButtonBase, useTheme } from "@mui/material";

// Must match the top+bottom padding set below ("22px 24px").
const VERTICAL_PADDING = 44;
// Must match the footer's mt below.
const FOOTER_GAP = 16;

const OptionBox = forwardRef(function OptionBox(
  {
    optionName,
    description,
    onClick,
    Icon = null,
    chips = [],
    dataTour,
    minHeight,
    onMeasure,
    ...otherProps
  },
  ref,
) {
  const theme = useTheme();
  const accent = theme.palette.primary.main;
  const accentDim = `${theme.palette.primary.main}1F`;
  const accentBorder = `${theme.palette.primary.main}38`;
  const accentGlow = `${theme.palette.primary.main}0A`;

  const contentRef = useRef(null);
  const footerRef = useRef(null);
  // Kept in a ref so the observer effect below doesn't need to reconnect
  // every time the parent re-renders and hands us a new function identity.
  const onMeasureRef = useRef(onMeasure);
  onMeasureRef.current = onMeasure;

  // Reports this card's own natural (unconstrained) required height, so the
  // parent can size every card to whichever one needs the most space.
  // contentRef/footerRef never stretch (the spacer between them absorbs any
  // extra space from an applied minHeight), so this reading is always the
  // card's true minimum, regardless of what minHeight is currently applied.
  // The observer itself is only (re)created when the card's own content
  // changes, not on every parent re-render, to avoid amplifying updates
  // during a live resize into a runaway render cascade.
  useLayoutEffect(() => {
    if (!contentRef.current || !footerRef.current) return;
    const report = () => {
      onMeasureRef.current?.(
        contentRef.current.offsetHeight +
          footerRef.current.offsetHeight +
          FOOTER_GAP +
          VERTICAL_PADDING,
      );
    };
    report();
    const observer = new ResizeObserver(report);
    observer.observe(contentRef.current);
    observer.observe(footerRef.current);
    return () => observer.disconnect();
  }, [optionName, description]);

  return (
    <ButtonBase
      ref={ref}
      data-tour={dataTour}
      onClick={onClick}
      sx={{
        width: "100%",
        height: "auto",
        minHeight: minHeight ? `${minHeight}px` : "auto",
        textAlign: "left",
        display: "flex",
        flexDirection: "column",
        background: theme.palette.background.paper,
        border: `1px solid ${theme.palette.divider}`,
        borderRadius: "4px",
        padding: "22px 24px",
        cursor: "pointer",
        position: "relative",
        overflow: "hidden",
        transition: "border-color 0.2s, background 0.2s, transform 0.15s",
        "&::before": {
          content: '""',
          position: "absolute",
          top: 0,
          left: "10%",
          right: "10%",
          height: "1px",
          background: `linear-gradient(90deg, transparent, ${accent}, transparent)`,
          opacity: 0,
          transition: "opacity 0.25s",
        },
        "&:hover": {
          transform: "translateY(-1px)",
          borderColor: accentBorder,
          background: accentGlow,
        },
        "&:hover::before": {
          opacity: 1,
        },
        "&:hover .card-arrow": {
          transform: "translateX(3px)",
          color: accent,
        },
      }}
      {...otherProps}
    >
      <Box ref={contentRef} sx={{ width: "100%", flexShrink: 0 }}>
        {/* Header: icon */}
        {Icon && (
          <Box sx={{ display: "flex", mb: "14px", width: "100%" }}>
            <Box
              sx={{
                width: 38,
                height: 38,
                borderRadius: "6px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                background: accentDim,
                color: accent,
                flexShrink: 0,
              }}
            >
              <Icon sx={{ fontSize: 25 }} />
            </Box>
          </Box>
        )}

        {/* Title */}
        <Typography
          variant="h4"
          sx={{
            color: theme.palette.text.primary,
            mb: "5px",
            width: "100%",
          }}
        >
          {optionName}
        </Typography>

        {/* Description */}
        <Typography
          variant="body1"
          sx={{
            fontWeight: 300,
            color: theme.palette.text.secondary,
            lineHeight: 1.65,
            width: "100%",
          }}
        >
          {description}
        </Typography>
      </Box>

      {/* Spacer: absorbs extra height so the footer stays pinned to the bottom */}
      <Box sx={{ flexGrow: 1 }} />

      {/* Footer: chips + arrow */}
      <Box
        ref={footerRef}
        sx={{
          mt: "16px",
          pt: "14px",
          borderTop: `1px solid ${theme.palette.ui.borderLight}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          width: "100%",
        }}
      >
        <Box sx={{ display: "flex", gap: "5px", flexWrap: "wrap" }}>
          {chips.map((chip) => (
            <Box
              key={chip}
              sx={{
                ...theme.typography.statusBadge,
                border: `1px solid ${theme.palette.divider}`,
                color: theme.palette.text.disabled,
                px: "7px",
                py: "2px",
                borderRadius: "2px",
                background: theme.palette.background.default,
              }}
            >
              {chip}
            </Box>
          ))}
        </Box>
        <Typography
          component="span"
          variant="h2"
          className="card-arrow"
          sx={{
            color: theme.palette.text.disabled,
            transition: "color 0.15s, transform 0.15s",
            flexShrink: 0,
            ml: 2,
          }}
        >
          →
        </Typography>
      </Box>
    </ButtonBase>
  );
});

export default OptionBox;
