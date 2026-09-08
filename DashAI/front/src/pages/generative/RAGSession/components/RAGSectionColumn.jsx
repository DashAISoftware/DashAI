import { Box } from "@mui/material";
import PropTypes from "prop-types";

/**
 * A flex-column layout wrapper used inside RAG sections for consistent spacing.
 *
 * @param {object}          props
 * @param {React.ReactNode} [props.children] - Content to render.
 * @param {number|string}   [props.gap]      - Gap between children (default 4).
 * @param {object|Array}    [props.sx]       - Additional MUI sx overrides.
 * @param {object}          [props]          - Additional props spread to the Box.
 * @returns {JSX.Element} The column wrapper.
 */
export default function RAGSectionColumn({ children, gap = 4, sx, ...props }) {
  return (
    <Box
      sx={[
        {
          display: "flex",
          flexDirection: "column",
          width: "100%",
          gap,
        },
        sx,
      ]}
      {...props}
    >
      {children}
    </Box>
  );
}

RAGSectionColumn.propTypes = {
  children: PropTypes.node,
  gap: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  sx: PropTypes.oneOfType([PropTypes.array, PropTypes.object, PropTypes.func]),
};
