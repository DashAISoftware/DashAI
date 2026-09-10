import { Box, IconButton } from "@mui/material";
import { ChevronLeft, ChevronRight } from "@mui/icons-material";
import { useThreePanelLayoutContext } from "./ThreePanelLayoutContext";

export default function LeftPanel({ children, "data-tour": dataTour }) {
  const {
    leftBarVisible,
    leftBarWidth,
    isTogglingLeft,
    bindLeftResize,
    handleToggleLeft,
  } = useThreePanelLayoutContext();
  return (
    <>
      <IconButton
        onClick={handleToggleLeft}
        size="small"
        sx={{
          position: "absolute",
          left: leftBarVisible ? `calc(${leftBarWidth}% - 9px)` : 8,
          top: "50%",
          transform: "translateY(-50%)",
          bgcolor: "primary.main",
          color: "primary.contrastText",
          // border: "1px solid",
          boxShadow: 2,
          width: 18,
          height: 32,
          borderRadius: 1,
          zIndex: 11,
          transition: isTogglingLeft
            ? "left 0.3s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.2s ease, transform 0.2s ease"
            : "background-color 0.2s ease, transform 0.2s ease",
          "&:hover": {
            bgcolor: "secondary.main",
            transform: "translateY(-50%) scale(1.1)",
          },
        }}
      >
        {leftBarVisible ? (
          <ChevronLeft fontSize="small" />
        ) : (
          <ChevronRight fontSize="small" />
        )}
      </IconButton>
      <Box
        width={leftBarVisible ? `${leftBarWidth}%` : "0%"}
        position="relative"
        className="datasets-list"
        sx={{
          transition: isTogglingLeft
            ? "width 0.3s cubic-bezier(0.4, 0, 0.2, 1), margin 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease"
            : "none",
          opacity: leftBarVisible ? 1 : 0,
          overflow: "hidden",
        }}
        data-tour={dataTour}
      >
        {leftBarVisible && (
          <>
            {children}
            <Box
              {...bindLeftResize}
              sx={{
                position: "absolute",
                right: -2,
                top: 0,
                bottom: 0,
                width: "5px",
                cursor: "col-resize",
                bgcolor: "transparent",
                transition: "background-color 0.2s ease",
                "&:hover": {
                  bgcolor: "primary.main",
                },
                zIndex: 10,
              }}
            />
          </>
        )}
      </Box>
    </>
  );
}
