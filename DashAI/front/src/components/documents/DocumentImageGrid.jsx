import { memo } from "react";
import PropTypes from "prop-types";
import { Box, ButtonBase, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { normalizeUrl } from "../../utils/urlUtils";

function DocumentImageGrid({ images, onOpen }) {
  const { t } = useTranslation(["datasets"]);
  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
        gap: 2,
      }}
    >
      {images.map((image) => (
        <ButtonBase
          key={image.position}
          onClick={() => onOpen(image.position)}
          focusRipple
          sx={{
            display: "flex",
            flexDirection: "column",
            alignItems: "stretch",
            textAlign: "left",
            border: 1,
            borderColor: "divider",
            borderRadius: 1,
            overflow: "hidden",
            bgcolor: "background.paper",
            "&:hover": { borderColor: "primary.main" },
            "&.Mui-focusVisible": {
              outline: 2,
              outlineColor: "primary.main",
              outlineOffset: 2,
            },
          }}
        >
          <Box
            sx={{
              height: 150,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              bgcolor: "background.box",
            }}
          >
            <Box
              component="img"
              src={normalizeUrl(image.url)}
              alt={
                image.attrs?.alt ||
                t("datasets:document.imageAlt", {
                  position: image.position + 1,
                })
              }
              loading="lazy"
              sx={{ maxWidth: "100%", maxHeight: "100%", objectFit: "contain" }}
            />
          </Box>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ px: 1.5, py: 1 }}
          >
            {image.page !== null && image.page !== undefined
              ? t("datasets:document.imagePlace", {
                  position: image.position + 1,
                  page: image.page,
                })
              : t("datasets:document.itemPosition", {
                  position: image.position + 1,
                })}
          </Typography>
        </ButtonBase>
      ))}
    </Box>
  );
}

DocumentImageGrid.propTypes = {
  images: PropTypes.arrayOf(
    PropTypes.shape({
      position: PropTypes.number.isRequired,
      page: PropTypes.number,
      url: PropTypes.string,
      attrs: PropTypes.object,
    }),
  ).isRequired,
  onOpen: PropTypes.func.isRequired,
};

export default memo(DocumentImageGrid);
