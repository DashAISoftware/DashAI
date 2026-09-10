import React, { useMemo, useState } from "react";
import PropTypes from "prop-types";
import {
  Box,
  Button,
  Checkbox,
  FormControlLabel,
  InputAdornment,
  Popover,
  TextField,
  Typography,
} from "@mui/material";
import { BarChart, ExpandLess, ExpandMore, Search } from "@mui/icons-material";
import { useTranslation } from "react-i18next";

function ResultsGraphsParameters({
  currentMetrics,
  selectedMetrics,
  handleToggleMetric,
  handleSelectAll,
  handleClearAll,
}) {
  const { t } = useTranslation(["models", "common"]);
  const [anchorEl, setAnchorEl] = useState(null);
  const [search, setSearch] = useState("");
  const open = Boolean(anchorEl);

  const filteredMetrics = useMemo(
    () =>
      currentMetrics.filter((metric) =>
        metric.toLowerCase().includes(search.toLowerCase()),
      ),
    [currentMetrics, search],
  );

  const handleClose = () => {
    setAnchorEl(null);
    setSearch("");
  };

  return (
    <>
      <Button
        onClick={(e) => setAnchorEl(e.currentTarget)}
        variant="outlined"
        size="small"
        disabled={currentMetrics.length === 0}
        startIcon={<BarChart fontSize="small" />}
        endIcon={
          open ? (
            <ExpandLess fontSize="small" />
          ) : (
            <ExpandMore fontSize="small" />
          )
        }
        sx={{
          textTransform: "none",
          color: "text.primary",
          borderColor: "divider",
        }}
      >
        {t("common:metrics")}
        <Box
          component="span"
          sx={{ ml: 1, color: "primary.main", fontWeight: 700 }}
        >
          {selectedMetrics.length}/{currentMetrics.length}
        </Box>
      </Button>

      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        transformOrigin={{ vertical: "top", horizontal: "right" }}
        slotProps={{
          paper: {
            sx: {
              mt: 1,
              width: 280,
              border: 1,
              borderColor: "divider",
              borderRadius: 1,
            },
          },
        }}
      >
        <Box sx={{ p: 1.5 }}>
          <TextField
            fullWidth
            size="small"
            autoFocus
            placeholder={t("models:label.searchMetric")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search fontSize="small" sx={{ color: "text.secondary" }} />
                </InputAdornment>
              ),
            }}
          />

          <Box sx={{ maxHeight: 260, overflowY: "auto", mt: 1 }}>
            {filteredMetrics.length === 0 ? (
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ p: 1, textAlign: "center" }}
              >
                {t("models:label.noMetricsAvailable")}
              </Typography>
            ) : (
              filteredMetrics.map((metric) => (
                <FormControlLabel
                  key={metric}
                  control={
                    <Checkbox
                      size="small"
                      checked={selectedMetrics.includes(metric)}
                      onChange={() => handleToggleMetric(metric)}
                    />
                  }
                  label={<Typography variant="body2">{metric}</Typography>}
                  sx={{ display: "flex", m: 0, width: "100%" }}
                />
              ))
            )}
          </Box>

          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              pt: 1.5,
              mt: 1,
              borderTop: "1px solid",
              borderColor: "divider",
            }}
          >
            <Typography
              variant="body2"
              color="primary"
              onClick={
                currentMetrics.length === 0 ? undefined : handleSelectAll
              }
              sx={{
                cursor: currentMetrics.length === 0 ? "default" : "pointer",
                opacity: currentMetrics.length === 0 ? 0.5 : 1,
                fontWeight: 600,
              }}
            >
              {t("common:selectAll")}
            </Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              onClick={
                selectedMetrics.length === 0 ? undefined : handleClearAll
              }
              sx={{
                cursor: selectedMetrics.length === 0 ? "default" : "pointer",
                opacity: selectedMetrics.length === 0 ? 0.5 : 1,
              }}
            >
              {t("common:clear")}
            </Typography>
          </Box>
        </Box>
      </Popover>
    </>
  );
}

ResultsGraphsParameters.propTypes = {
  currentMetrics: PropTypes.array.isRequired,
  selectedMetrics: PropTypes.array.isRequired,
  handleToggleMetric: PropTypes.func.isRequired,
  handleSelectAll: PropTypes.func.isRequired,
  handleClearAll: PropTypes.func.isRequired,
};

export default ResultsGraphsParameters;
