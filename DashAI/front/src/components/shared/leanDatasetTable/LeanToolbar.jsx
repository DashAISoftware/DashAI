import { memo } from "react";
import PropTypes from "prop-types";
import {
  Box,
  Button,
  CircularProgress,
  IconButton,
  Tooltip,
  Typography,
} from "@mui/material";
import ViewColumnIcon from "@mui/icons-material/ViewColumn";
import FilterListIcon from "@mui/icons-material/FilterList";
import FilterListOffIcon from "@mui/icons-material/FilterListOff";
import SearchIcon from "@mui/icons-material/Search";
import ClearIcon from "@mui/icons-material/Clear";
import FileDownloadIcon from "@mui/icons-material/FileDownload";
import { useTranslation } from "react-i18next";

const LeanToolbar = memo(function LeanToolbar({
  hiddenColumnsCount,
  loading,
  showFilters,
  searchValue,
  enableFilters,
  enableSearch,
  enableColumnVisibility,
  showExportButton,
  isExporting,
  hasActiveFilters,
  onOpenColumnsMenu,
  onToggleFilters,
  onSearchChange,
  onClearSearch,
  onExport,
  extraActions,
}) {
  const { t } = useTranslation(["datasets"]);

  if (
    !enableFilters &&
    !enableSearch &&
    !enableColumnVisibility &&
    !showExportButton
  ) {
    return null;
  }

  return (
    <Box className="lean-toolbar">
      {/* Left: filters, search, hidden-count badge, column-visibility */}
      {enableFilters && (
        <Tooltip
          title={
            showFilters
              ? t("datasets:table.hideFilters")
              : t("datasets:table.showFilters")
          }
        >
          <IconButton
            size="small"
            onClick={onToggleFilters}
            color={showFilters ? "primary" : "default"}
          >
            {showFilters ? (
              <FilterListOffIcon fontSize="small" />
            ) : (
              <FilterListIcon fontSize="small" />
            )}
          </IconButton>
        </Tooltip>
      )}
      {enableSearch && (
        <Box className="lean-search">
          <SearchIcon fontSize="small" className="lean-search-icon" />
          <input
            className="lean-search-input"
            type="text"
            placeholder={t("datasets:table.search")}
            value={searchValue}
            onChange={onSearchChange}
          />
          {searchValue && (
            <IconButton size="small" onClick={onClearSearch} sx={{ p: 0.25 }}>
              <ClearIcon fontSize="small" />
            </IconButton>
          )}
        </Box>
      )}
      {hiddenColumnsCount > 0 && (
        <Typography variant="caption" color="text.secondary" sx={{ mr: 1 }}>
          {t("datasets:table.hiddenCount", { count: hiddenColumnsCount })}
        </Typography>
      )}
      {enableColumnVisibility && (
        <Tooltip title={t("datasets:table.showHideColumns")}>
          <IconButton size="small" onClick={onOpenColumnsMenu}>
            <ViewColumnIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      )}

      <Box sx={{ flex: 1 }} />

      {/* Right: export, then any per-table custom actions */}
      {showExportButton && (
        <Tooltip
          title={
            hasActiveFilters
              ? t("datasets:table.exportTooltipFiltered")
              : t("datasets:table.exportTooltipAll")
          }
          arrow
        >
          <span>
            <Button
              size="small"
              variant="text"
              onClick={onExport}
              disabled={isExporting}
              startIcon={
                isExporting ? (
                  <CircularProgress size={14} color="inherit" />
                ) : (
                  <FileDownloadIcon fontSize="small" />
                )
              }
            >
              {hasActiveFilters
                ? t("datasets:table.exportFiltered")
                : t("datasets:table.export")}
            </Button>
          </span>
        </Tooltip>
      )}
      {extraActions && (
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, ml: 1 }}>
          {extraActions}
        </Box>
      )}
    </Box>
  );
});

LeanToolbar.propTypes = {
  hiddenColumnsCount: PropTypes.number.isRequired,
  loading: PropTypes.bool.isRequired,
  showFilters: PropTypes.bool.isRequired,
  searchValue: PropTypes.string.isRequired,
  enableFilters: PropTypes.bool.isRequired,
  enableSearch: PropTypes.bool.isRequired,
  enableColumnVisibility: PropTypes.bool.isRequired,
  showExportButton: PropTypes.bool.isRequired,
  isExporting: PropTypes.bool.isRequired,
  hasActiveFilters: PropTypes.bool.isRequired,
  onOpenColumnsMenu: PropTypes.func.isRequired,
  onToggleFilters: PropTypes.func.isRequired,
  onSearchChange: PropTypes.func.isRequired,
  onClearSearch: PropTypes.func.isRequired,
  onExport: PropTypes.func.isRequired,
  extraActions: PropTypes.node,
};

export default LeanToolbar;
