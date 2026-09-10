import { Box, Link, Paper, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import ReactMarkdown from "react-markdown";
import { FormCardProvider } from "../../contexts/FormCardContext";

const CHAR_LIMIT = 120;

// Markdown component overrides — render with caption sizing and theme colours
const mdComponents = (color) => ({
  p: ({ children }) => (
    <Typography
      component="span"
      variant="caption"
      color={color}
      sx={{ display: "block", lineHeight: 1.5, "& + span": { mt: 1 } }}
    >
      {children}
    </Typography>
  ),
  a: ({ href, children }) => (
    <Link
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      variant="caption"
      color="primary"
    >
      {children}
    </Link>
  ),
  code: ({ inline, children }) =>
    inline ? (
      <Box
        component="code"
        sx={{
          fontFamily: "monospace",
          fontSize: "0.7rem",
          bgcolor: "action.hover",
          borderRadius: 0.5,
          px: 2,
          py: 1,
        }}
      >
        {children}
      </Box>
    ) : (
      <Box
        component="pre"
        sx={{
          fontFamily: "monospace",
          fontSize: "0.7rem",
          bgcolor: "action.hover",
          borderRadius: 1,
          p: 3,
          mt: 2,
          overflowX: "auto",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}
      >
        <code>{children}</code>
      </Box>
    ),
  strong: ({ children }) => (
    <Box component="strong" sx={{ fontWeight: 700 }}>
      {children}
    </Box>
  ),
  em: ({ children }) => (
    <Box component="em" sx={{ fontStyle: "italic" }}>
      {children}
    </Box>
  ),
  ul: ({ children }) => (
    <Box component="ul" sx={{ pl: 8, my: 1, "& li": { fontSize: "0.75rem" } }}>
      {children}
    </Box>
  ),
  ol: ({ children }) => (
    <Box component="ol" sx={{ pl: 8, my: 1, "& li": { fontSize: "0.75rem" } }}>
      {children}
    </Box>
  ),
});

export function DescriptionBlock({ text, isError }) {
  const [expanded, setExpanded] = useState(false);
  const { t } = useTranslation(["common"]);

  if (!text) return null;

  const needsTruncation = text.length > CHAR_LIMIT;
  const displayed =
    expanded || !needsTruncation ? text : `${text.slice(0, CHAR_LIMIT)}\u2026`;
  const color = isError ? "error.main" : "text.disabled";

  return (
    <Box sx={{ mt: 2, pb: 2 }}>
      <ReactMarkdown components={mdComponents(color)}>
        {displayed}
      </ReactMarkdown>
      {needsTruncation && (
        <Link
          component="button"
          type="button"
          variant="caption"
          color={isError ? "error" : "primary"}
          underline="hover"
          onClick={() => setExpanded((prev) => !prev)}
          sx={{
            mt: 1,
            display: "inline-block",
            background: "none",
            border: "none",
            cursor: "pointer",
          }}
        >
          {expanded ? t("common:viewLess") : t("common:viewMore")}
        </Link>
      )}
    </Box>
  );
}

DescriptionBlock.propTypes = {
  text: PropTypes.string,
  isError: PropTypes.bool,
};

/**
 * Card shell used by all FormSchema field variants.
 * Renders a header row (avatar + label + param key + optional right slot)
 * and a body with the input(s) followed by an inline truncated description.
 *
 * @param {string} label        - Display label shown bold in the header
 * @param {string} paramKey     - Technical key shown in monospace below the label
 * @param {string} description  - Parameter description shown inline below the input
 * @param {string} errorMessage - When set, replaces description and renders in red
 * @param {node}   headerRight  - Optional right-side header slot (optimize toggle, expand button…)
 * @param {node}   children     - The actual input(s)
 */
function FormSchemaFieldCard({
  label,
  paramKey,
  description,
  errorMessage,
  headerRight,
  children,
}) {
  return (
    <Paper variant="outlined" sx={{ borderRadius: 2, overflow: "hidden" }}>
      {/* ── Header ── */}
      <Box
        sx={{
          px: 6,
          py: 3,
          display: "flex",
          alignItems: "center",
          gap: 4,
          borderBottom: "1px solid",
          borderColor: "divider",
        }}
      >
        <Box flex={1} minWidth={0}>
          <Typography
            variant="body2"
            fontWeight={600}
            color={errorMessage ? "error.main" : "text.primary"}
          >
            {label ?? paramKey}
          </Typography>
        </Box>

        {headerRight}
      </Box>

      {/* ── Body ── */}
      <FormCardProvider>
        <Box
          sx={{
            px: 6,
            pt: 2,
            pb: description || errorMessage ? 2 : 4,
            // Hide the floating label — the card header already shows it
            "& .MuiInputLabel-root": { display: "none" },
            // Remove the label notch indent from outlined inputs
            "& .MuiOutlinedInput-notchedOutline legend > span": {
              display: "none",
            },
          }}
        >
          {children}
        </Box>

        {(description || errorMessage) && (
          <Box sx={{ px: 6 }}>
            <DescriptionBlock
              text={errorMessage ?? description}
              isError={Boolean(errorMessage)}
            />
          </Box>
        )}
      </FormCardProvider>
    </Paper>
  );
}

FormSchemaFieldCard.propTypes = {
  label: PropTypes.string,
  paramKey: PropTypes.string,
  description: PropTypes.string,
  errorMessage: PropTypes.string,
  headerRight: PropTypes.node,
  children: PropTypes.node.isRequired,
};

export default FormSchemaFieldCard;
