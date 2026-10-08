import PropTypes from "prop-types";
import {
  Box,
  FormControlLabel,
  IconButton,
  Switch,
  Tab,
  Tooltip,
  Typography,
} from "@mui/material";
import {
  ChevronLeft as PreviousIcon,
  ChevronRight as NextIcon,
} from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import PillTabs from "../shared/PillTabs";

const SCROLL_CONTAINER_PADDING = 16;

function PageNavigator({
  page,
  totalPages,
  hasPrevious,
  hasNext,
  onPrevious,
  onNext,
}) {
  const { t } = useTranslation(["datasets"]);
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
      <Tooltip title={t("datasets:document.previousPage")}>
        <span>
          <IconButton
            size="small"
            aria-label={t("datasets:document.previousPage")}
            onClick={onPrevious}
            disabled={!hasPrevious}
          >
            <PreviousIcon fontSize="small" />
          </IconButton>
        </span>
      </Tooltip>
      <Typography
        variant="body2"
        aria-live="polite"
        sx={{
          minWidth: 96,
          textAlign: "center",
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {t("datasets:document.pageOf", { page, total: totalPages })}
      </Typography>
      <Tooltip title={t("datasets:document.nextPage")}>
        <span>
          <IconButton
            size="small"
            aria-label={t("datasets:document.nextPage")}
            onClick={onNext}
            disabled={!hasNext}
          >
            <NextIcon fontSize="small" />
          </IconButton>
        </span>
      </Tooltip>
    </Box>
  );
}

PageNavigator.propTypes = {
  page: PropTypes.number.isRequired,
  totalPages: PropTypes.number.isRequired,
  hasPrevious: PropTypes.bool.isRequired,
  hasNext: PropTypes.bool.isRequired,
  onPrevious: PropTypes.func.isRequired,
  onNext: PropTypes.func.isRequired,
};

export default function DocumentToolbar({
  tab,
  onTabChange,
  imageCount,
  showKinds,
  onShowKindsChange,
  page,
  totalPages,
  pages,
  onPageChange,
}) {
  const { t } = useTranslation(["datasets"]);
  const isImages = tab === 2;
  const index = pages.indexOf(page);
  return (
    <Box
      sx={{
        position: "sticky",
        top: -SCROLL_CONTAINER_PADDING,
        zIndex: 2,
        mx: -4,
        px: 4,
        py: 1.5,
        bgcolor: "background.default",
        borderBottom: 1,
        borderColor: "divider",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 2,
        flexWrap: "wrap",
      }}
    >
      <PillTabs
        minHeight="40px"
        value={tab}
        onChange={(_, value) => onTabChange(value)}
      >
        <Tab label={t("datasets:document.viewDocument")} />
        <Tab label={t("datasets:document.viewStructure")} />
        <Tab
          label={t("datasets:document.tabImage", { total: imageCount })}
          disabled={!imageCount}
        />
      </PillTabs>

      <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
        {tab === 0 && (
          <Tooltip title={t("datasets:document.showKindsHint")}>
            <FormControlLabel
              sx={{ mr: 0 }}
              control={
                <Switch
                  size="small"
                  checked={showKinds}
                  onChange={(event) => onShowKindsChange(event.target.checked)}
                />
              }
              label={
                <Typography variant="body2">
                  {t("datasets:document.showKinds")}
                </Typography>
              }
            />
          </Tooltip>
        )}
        {!isImages && pages.length > 1 && index !== -1 && (
          <PageNavigator
            page={page}
            totalPages={totalPages}
            hasPrevious={index > 0}
            hasNext={index < pages.length - 1}
            onPrevious={() => onPageChange(pages[index - 1])}
            onNext={() => onPageChange(pages[index + 1])}
          />
        )}
      </Box>
    </Box>
  );
}

DocumentToolbar.propTypes = {
  tab: PropTypes.number.isRequired,
  onTabChange: PropTypes.func.isRequired,
  imageCount: PropTypes.number,
  showKinds: PropTypes.bool.isRequired,
  onShowKindsChange: PropTypes.func.isRequired,
  page: PropTypes.number,
  totalPages: PropTypes.number,
  pages: PropTypes.arrayOf(PropTypes.number).isRequired,
  onPageChange: PropTypes.func.isRequired,
};
