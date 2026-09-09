import PropTypes from "prop-types";
import { Box, Typography } from "@mui/material";
import ViewModuleIcon from "@mui/icons-material/ViewModule";
import { useTranslation } from "react-i18next";
import NewItemButton from "../threeSectionLayout/NewItemButton";

/**
 * The 64px header at the top of the generative module's left panel.
 *
 * Every view in the module starts with this row, so the way back to the hub
 * sits in the same place on all of them. It is extracted from `SessionBar`
 * because the RAG session view splits its left panel between documents and
 * sessions, and the header has to stay above that split rather than travel
 * with the session list.
 *
 * The row holds nothing but the way back: a second control beside it read as
 * an action on the hub button rather than on the view below.
 *
 * @param {object}   props
 * @param {boolean}  [props.showHubButton=false] - Whether to offer the way
 *   back to the hub. The hub itself has nowhere to go, so it shows its name.
 * @param {Function} [props.onHubClick] - Navigates to the hub.
 * @returns {JSX.Element} The header row.
 */
export default function GenerativeHubHeader({
  showHubButton = false,
  onHubClick,
}) {
  const { t } = useTranslation(["generative"]);

  return (
    <Box
      p={4}
      sx={{ height: "64px", display: "flex", alignItems: "center", gap: 1 }}
    >
      {showHubButton ? (
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <NewItemButton
            onClick={onHubClick}
            title={t("generative:button.generativeHub")}
            EndIcon={ViewModuleIcon}
          />
        </Box>
      ) : (
        <Typography variant="body1" color="textSecondary">
          {t("generative:label.generativeModule")}
        </Typography>
      )}
    </Box>
  );
}

GenerativeHubHeader.propTypes = {
  showHubButton: PropTypes.bool,
  onHubClick: PropTypes.func,
};
