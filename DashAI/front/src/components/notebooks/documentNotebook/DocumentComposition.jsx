import PropTypes from "prop-types";
import { Box, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import {
  KIND_ORDER,
  kindColor,
  kindLabel,
} from "../../documents/documentKinds";
import { CONTENT_TYPE_ICONS, contentTypeLabel } from "./documentItems";

function orderedKinds(kinds) {
  const rank = (kind) => {
    const index = KIND_ORDER.indexOf(kind);
    return index === -1 ? KIND_ORDER.length : index;
  };
  return Object.entries(kinds || {}).sort(([a], [b]) => rank(a) - rank(b));
}

export default function DocumentComposition({ columnTypes }) {
  const { t } = useTranslation(["datasets"]);
  const theme = useTheme();
  const types = Object.entries(columnTypes || {});

  if (types.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        {t("datasets:documentNotebook.noItems")}
      </Typography>
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      {types.map(([typeName, info]) => {
        const Icon = CONTENT_TYPE_ICONS[typeName];
        return (
          <Box key={typeName}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
              {Icon && <Icon sx={{ fontSize: 18, color: "text.secondary" }} />}
              <Typography sx={{ fontWeight: 600, flex: 1, fontSize: "14px" }}>
                {contentTypeLabel(t, typeName)}
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ fontVariantNumeric: "tabular-nums" }}
              >
                {info.count}
              </Typography>
            </Box>
            {orderedKinds(info.kinds).map(([kind, count]) => (
              <Box
                key={kind}
                sx={{
                  display: "grid",
                  gridTemplateColumns: "112px 1fr 40px",
                  alignItems: "center",
                  gap: 1.5,
                  py: 0.5,
                }}
              >
                <Typography variant="body2" noWrap>
                  {kindLabel(t, kind)}
                </Typography>
                <Box
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    bgcolor: theme.palette.ui.border,
                    overflow: "hidden",
                  }}
                >
                  <Box
                    sx={{
                      height: "100%",
                      width: `${(count / Math.max(info.count, 1)) * 100}%`,
                      bgcolor: kindColor(theme, kind),
                    }}
                  />
                </Box>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{
                    textAlign: "right",
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  {count}
                </Typography>
              </Box>
            ))}
          </Box>
        );
      })}
    </Box>
  );
}

DocumentComposition.propTypes = {
  columnTypes: PropTypes.objectOf(
    PropTypes.shape({
      count: PropTypes.number,
      kinds: PropTypes.objectOf(PropTypes.number),
    }),
  ),
};
