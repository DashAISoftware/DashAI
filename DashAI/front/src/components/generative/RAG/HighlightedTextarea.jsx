import { forwardRef, useRef, useCallback, useImperativeHandle } from "react";
import { Box, Typography, useTheme } from "@mui/material";
import { renderTemplateWithHighlights } from "../../../pages/generative/RAGSession/components/sectionUtils";

/**
 * A multiline text field that highlights placeholders ({chunks}, {input}, etc.)
 * inside the editable area using an overlay technique.
 *
 * Both the highlighted backdrop and the native textarea share the same CSS Grid
 * cell and identical styling (padding, font, line-height, border), so the
 * highlights align perfectly with the text. The backdrop scrolls in sync.
 *
 * The ref forwards to the underlying <textarea> DOM element so parents can
 * access selectionStart / selectionEnd for cursor-based operations.
 */
const HighlightedTextarea = forwardRef(function HighlightedTextarea(
  { value, onChange, label, placeholder, minRows = 4, sx, ...textareaProps },
  ref,
) {
  const theme = useTheme();
  const backdropRef = useRef(null);
  const inputRef = useRef(null);

  useImperativeHandle(ref, () => inputRef.current, []);

  const bgColor = theme.palette.placeholder?.bg || theme.palette.warning.light;
  const textColor =
    theme.palette.placeholder?.text || theme.palette.warning.dark;

  const handleScroll = useCallback(() => {
    const input = inputRef.current;
    const backdrop = backdropRef.current;
    if (input && backdrop) {
      backdrop.scrollTop = input.scrollTop;
      backdrop.scrollLeft = input.scrollLeft;
    }
  }, []);

  /** Shared styles applied to both backdrop and textarea for perfect alignment */
  const sharedInputSx = {
    fontFamily: theme.typography.code.fontFamily,
    fontSize: theme.typography.body2.fontSize,
    lineHeight: 1.6,
    p: "16.5px 14px",
    border: 1,
    borderColor: "divider",
    borderRadius: 1,
    // Stack both elements in the same grid cell so they overlap exactly
    gridArea: "1 / 1",
  };

  return (
    <Box sx={{ mt: 2, width: "100%", ...sx }}>
      {label && (
        <Typography variant="body2" sx={{ mb: 0.5, color: "text.secondary" }}>
          {label}
        </Typography>
      )}

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "1fr",
          gridTemplateRows: "auto",
          width: "100%",
        }}
      >
        <Box
          ref={backdropRef}
          aria-hidden="true"
          sx={{
            ...sharedInputSx,
            pointerEvents: "none",
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            overflow: "hidden",
            zIndex: 0,
            borderColor: "transparent",
            color: "text.primary",
          }}
        >
          {value
            ? renderTemplateWithHighlights(
                value,
                {
                  bg: bgColor,
                  text: textColor,
                },
                theme.typography.code.fontFamily,
              )
            : placeholder || ""}
        </Box>

        <Box
          component="textarea"
          ref={inputRef}
          value={value}
          onChange={onChange}
          onScroll={handleScroll}
          placeholder={placeholder}
          rows={minRows}
          sx={{
            ...sharedInputSx,
            position: "relative",
            zIndex: 1,
            display: "block",
            width: "100%",
            color: "transparent",
            caretColor: (t) => t.palette.text.primary,
            backgroundColor: "transparent",
            resize: "vertical",
            outline: "none",
            "&::placeholder": {
              color: (t) => t.palette.text.secondary,
              opacity: 1,
            },
            "&::selection": {
              backgroundColor: "primary.light",
            },
            "&:focus": {
              borderColor: "primary.main",
              borderWidth: 2,
              p: "15.5px 13px",
            },
            "&:hover": {
              borderColor: (t) => t.palette.text.primary,
            },
          }}
          {...textareaProps}
        />
      </Box>
    </Box>
  );
});

export default HighlightedTextarea;
