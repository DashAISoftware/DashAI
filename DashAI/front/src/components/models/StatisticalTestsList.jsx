import React, { useState, useEffect, useMemo } from "react";
import PropTypes from "prop-types";
import { Box, Typography, TextField, CircularProgress } from "@mui/material";
import { Search as SearchIcon } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { getComponents } from "../../api/component";
import ModelListItem from "./model/ModelListItem";

export default function StatisticalTestsList({ onTestSelect }) {
  const { t } = useTranslation(["models"]);
  const { enqueueSnackbar } = useSnackbar();

  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  // Traer tests estadísticos del backend
  useEffect(() => {
    const fetchTests = async () => {
      try {
        setLoading(true);
        const response = await getComponents({
          selectTypes: ["StatisticalTest"],
        });
        setTests(
          response.filter((comp) => comp.metadata?.is_posthoc === false),
        );
      } catch (error) {
        console.error("Error fetching statistical tests:", error);
        enqueueSnackbar(t("models:error.fetchingStatisticalTests"), {
          variant: "error",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchTests();
  }, [enqueueSnackbar, t]);

  // Clasificar tests por tipo (paramétricos, no-paramétricos y helpers)
  const { parametricTests, nonParametricTests, helperTests } = useMemo(() => {
    const parametric = [];
    const nonParametric = [];
    const helper = [];

    tests.forEach((test) => {
      if (test.metadata?.is_parametric === true) {
        parametric.push(test);
      } else if (test.metadata?.is_parametric === false) {
        nonParametric.push(test);
      } else {
        helper.push(test);
      }
    });

    return {
      parametricTests: parametric,
      nonParametricTests: nonParametric,
      helperTests: helper,
    };
  }, [tests]);

  // Filtrar tests por búsqueda
  const filterByQuery = (list) => {
    if (!searchQuery.trim()) return list;
    const query = searchQuery.toLowerCase();
    return list.filter((test) =>
      (test.display_name || test.metadata?.name || test.name || "")
        .toLowerCase()
        .includes(query),
    );
  };

  const filteredHelperTests = useMemo(
    () => filterByQuery(helperTests),
    [searchQuery, helperTests],
  );
  const filteredParametricTests = useMemo(
    () => filterByQuery(parametricTests),
    [searchQuery, parametricTests],
  );
  const filteredNonParametricTests = useMemo(
    () => filterByQuery(nonParametricTests),
    [searchQuery, nonParametricTests],
  );

  const renderSection = (titleKey, colorKey, list) =>
    list.length > 0 && (
      <Box sx={{ mb: 3 }}>
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{
            textTransform: "uppercase",
            letterSpacing: 0.5,
            fontWeight: 600,
            display: "block",
            mb: 2,
          }}
        >
          {t(titleKey)}
        </Typography>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
          {list.map((test) => (
            <ModelListItem
              key={test.name}
              model={test}
              draggable
              dragType="application/x-dashai-statistical-test"
              dragPayload={test}
              onClick={() => onTestSelect(test)}
            />
          ))}
        </Box>
      </Box>
    );

  const noResults =
    filteredHelperTests.length === 0 &&
    filteredParametricTests.length === 0 &&
    filteredNonParametricTests.length === 0;

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        height: "100%",
        width: "100%",
      }}
    >
      {/* Search Box */}
      <Box sx={{ p: 4, flexShrink: 0 }}>
        <TextField
          fullWidth
          size="small"
          placeholder={t("models:label.searchTests")}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          slotProps={{
            input: {
              startAdornment: (
                <SearchIcon sx={{ mr: 2, color: "text.secondary" }} />
              ),
            },
          }}
        />
      </Box>

      {/* Content */}
      <Box
        sx={{
          flex: 1,
          overflow: "auto",
          display: "flex",
          flexDirection: "column",
          p: 4,
          pt: 0,
        }}
      >
        {loading ? (
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              flex: 1,
            }}
          >
            <CircularProgress size={32} />
          </Box>
        ) : (
          <>
            {renderSection(
              "models:label.helperTests",
              "info.main",
              filteredHelperTests,
            )}
            {renderSection(
              "models:label.parametricTests",
              "primary.main",
              filteredParametricTests,
            )}
            {renderSection(
              "models:label.nonParametricTests",
              "secondary.main",
              filteredNonParametricTests,
            )}

            {noResults && (
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  flex: 1,
                }}
              >
                <Typography
                  variant="body2"
                  sx={{ color: "text.secondary", textAlign: "center" }}
                >
                  {t("models:label.noTestsMatch")}
                </Typography>
              </Box>
            )}
          </>
        )}
      </Box>
    </Box>
  );
}

StatisticalTestsList.propTypes = {
  onTestSelect: PropTypes.func.isRequired,
  loading: PropTypes.bool,
};
