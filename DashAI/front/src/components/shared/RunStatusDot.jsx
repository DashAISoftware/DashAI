import Box from "@mui/material/Box";
import { useTheme } from "@mui/material/styles";
import PropTypes from "prop-types";
import { getRunStatusColor } from "../../utils/runStatus";

export default function RunStatusDot({ status, size, sx, colorKey }) {
  const theme = useTheme();
  // An explicit colorKey overrides the status-derived one, letting a caller
  // signal "in progress" (e.g. a queued job still at NOT_STARTED) with a color
  // its raw status would not map to.
  const statusColorKey = colorKey ?? getRunStatusColor(status);
  const statusMain =
    statusColorKey === "default"
      ? theme.palette.text.disabled
      : theme.palette[statusColorKey].main;

  return (
    <Box
      component="span"
      sx={{
        display: "inline-block",
        verticalAlign: "middle",
        width: size,
        height: size,
        borderRadius: "50%",
        bgcolor: statusMain,
        flexShrink: 0,
        ...sx,
      }}
    />
  );
}

RunStatusDot.propTypes = {
  status: PropTypes.number.isRequired,
  size: PropTypes.number,
  sx: PropTypes.object,
  colorKey: PropTypes.oneOf(["default", "info", "success", "error", "warning"]),
};

RunStatusDot.defaultProps = {
  size: 8,
  sx: {},
  colorKey: undefined,
};
