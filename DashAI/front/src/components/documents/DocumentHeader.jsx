import PropTypes from "prop-types";
import { Box } from "@mui/material";
import MenuBookIcon from "@mui/icons-material/MenuBook";
import NotesIcon from "@mui/icons-material/Notes";
import ImageIcon from "@mui/icons-material/Image";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";
import { HeaderBox } from "../notebooks/dataset/header/HeaderBox";
import { useTranslation } from "react-i18next";

export default function DocumentHeader({
  totalPages,
  textCount,
  imageCount,
  fileType,
}) {
  const { t } = useTranslation(["common", "datasets"]);

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: 2,
        flexGrow: 1,
        minHeight: 0,
      }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "row",
          gap: 2,
          justifyContent: "flex-start",
          alignItems: "stretch",
          width: "100%",
          flexWrap: "wrap",
          flexGrow: 0,
        }}
      >
        <HeaderBox
          title={t("datasets:document.pages")}
          value={totalPages ?? t("common:na")}
          IconComponent={MenuBookIcon}
          iconColor="rgb(100, 150, 255)"
          bgColor="rgba(100, 150, 255, 0.15)"
        />
        <HeaderBox
          title={t("datasets:document.textCount")}
          value={textCount ?? 0}
          IconComponent={NotesIcon}
          iconColor="rgb(100, 200, 150)"
          bgColor="rgba(100, 200, 150, 0.15)"
        />
        <HeaderBox
          title={t("datasets:document.imageCount")}
          value={imageCount ?? 0}
          IconComponent={ImageIcon}
          iconColor="rgb(180, 120, 200)"
          bgColor="rgba(180, 120, 200, 0.15)"
        />
        <HeaderBox
          title={t("datasets:document.fileType")}
          value={fileType ? fileType.toUpperCase() : t("common:na")}
          IconComponent={InsertDriveFileIcon}
          iconColor="rgb(230, 160, 90)"
          bgColor="rgba(230, 160, 90, 0.15)"
        />
      </Box>
    </Box>
  );
}

DocumentHeader.propTypes = {
  totalPages: PropTypes.number,
  textCount: PropTypes.number,
  imageCount: PropTypes.number,
  fileType: PropTypes.string,
};
