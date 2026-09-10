import PropTypes from "prop-types";
import { Box, Stack, Typography } from "@mui/material";
import CheckIcon from "@mui/icons-material/Check";
import Paper from "@mui/material/Paper";

/**
 * A vertical list of selectable preset cards.
 *
 * Wears the same card treatment as `ComponentSelector` -- flat `Paper`, a
 * border that turns primary when active, a tick in the corner -- so a preset
 * reads like the component choices elsewhere in the module. It does not reuse
 * that component: `ComponentSelector` also brings a search field, category
 * chips, download controls and a viewport-breakpoint grid, none of which apply
 * to a recipe, and a two-column grid is unreadable in a panel this narrow.
 *
 * @param {object}   props
 * @param {Array}    props.presets - Presets, each `{key, display_name,
 *   description, component, params}`.
 * @param {string}   [props.activeKey] - The preset the draft currently matches,
 *   or null when the configuration is custom.
 * @param {Function} props.onSelect - Called with the chosen preset.
 * @returns {JSX.Element} The card list.
 */
export default function PresetCardList({ presets, activeKey, onSelect }) {
  return (
    <Stack spacing={1}>
      {presets.map((preset) => {
        const isSelected = activeKey === preset.key;
        return (
          <Paper
            key={preset.key}
            elevation={0}
            onClick={() => onSelect(preset)}
            sx={{
              p: 2,
              cursor: "pointer",
              border: 1,
              borderColor: isSelected ? "primary.main" : "divider",
              bgcolor: isSelected ? "action.selected" : "background.paper",
              transition: "all 0.2s",
              "&:hover": { borderColor: "secondary.main" },
            }}
          >
            <Stack direction="row" alignItems="flex-start" spacing={1}>
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography variant="subtitle2">
                  {preset.display_name}
                </Typography>
                {preset.description && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{
                      display: "-webkit-box",
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: "vertical",
                      overflow: "hidden",
                    }}
                  >
                    {preset.description}
                  </Typography>
                )}
              </Box>
              {isSelected && (
                <CheckIcon fontSize="small" color="primary" sx={{ mt: 0.25 }} />
              )}
            </Stack>
          </Paper>
        );
      })}
    </Stack>
  );
}

PresetCardList.propTypes = {
  presets: PropTypes.array.isRequired,
  activeKey: PropTypes.string,
  onSelect: PropTypes.func.isRequired,
};
