import { useState, useEffect, useCallback } from "react";
import PropTypes from "prop-types";
import {
  Box,
  Typography,
  IconButton,
  Chip,
  Tooltip,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from "@mui/material";
import { DeleteOutline, Refresh } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import {
  getSavedStatisticalTests,
  deleteSavedStatisticalTest,
} from "../../api/statisticalTests";
import SavedStatisticalTestResults from "./SavedStatisticalTestResults";

// Group rows that share a group_id (per-run batches, e.g. Shapiro) so each
// saved test is a single row. Single results become a group of one.
// Most recent first.
function groupSavedTests(tests) {
  const groups = new Map();
  tests.forEach((test) => {
    const key = test.group_id || `single:${test.id}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(test);
  });
  return Array.from(groups.values()).sort(
    (a, b) =>
      new Date(b[0].created ?? b[0].created_at).getTime() -
      new Date(a[0].created ?? a[0].created_at).getTime(),
  );
}

const formatDate = (row) => {
  const iso = row.created;
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
};

/**
 * Inline view listing the statistical tests saved for a session.
 * Each saved test is one summary row; clicking it opens a detail modal.
 */
export default function StatisticalTestTable({ session }) {
  const { t } = useTranslation(["models", "common"]);

  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [selectedGroup, setSelectedGroup] = useState(null);

  const modelSessionId = session?.id;

  const fetchTests = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getSavedStatisticalTests(modelSessionId);
      setTests(data);
    } catch (err) {
      setError(
        err.response?.data?.detail || t("models:error.failedToLoadTests"),
      );
    } finally {
      setLoading(false);
    }
  }, [modelSessionId, t]);

  useEffect(() => {
    fetchTests();
  }, [fetchTests]);

  const handleDelete = async (e, ids) => {
    e.stopPropagation();
    const list = Array.isArray(ids) ? ids : [ids];
    setDeletingId(list[0]);
    setError(null);
    try {
      await Promise.all(list.map((id) => deleteSavedStatisticalTest(id)));
      setTests((prev) => prev.filter((x) => !list.includes(x.id)));
    } catch (err) {
      setError(
        err.response?.data?.detail || t("models:error.failedToDeleteTest"),
      );
    } finally {
      setDeletingId(null);
    }
  };

  const groups = groupSavedTests(tests);
  const tableHeaders = [
    { label: t("models:label.name"), align: "left" },
    { label: t("models:label.test"), align: "left" },
    { label: t("models:label.metric"), align: "left" },
    { label: t("models:label.metricSplit"), align: "left" },
    { label: t("models:label.result"), align: "center" },
    { label: t("common:date"), align: "right" },
  ];

  const resultCell = (items) => {
    const head = items[0];
    if (items.length > 1) {
      const significants = items.filter((i) => i.significant).length;
      return (
        <Chip
          label={t("models:label.significantsCount", {
            count: significants,
            total: items.length,
          })}
          size="small"
          variant="outlined"
          color={significants > 0 ? "success" : "default"}
        />
      );
    }
    return (
      <Chip
        label={
          head.significant
            ? t("models:label.significant")
            : t("models:label.notSignificant")
        }
        size="small"
        variant="outlined"
        color={head.significant ? "success" : "default"}
      />
    );
  };

  return (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "flex-end",
          mb: 1,
        }}
      >
        <Tooltip title={t("common:refresh")}>
          <span>
            <IconButton size="small" onClick={fetchTests} disabled={loading}>
              <Refresh />
            </IconButton>
          </span>
        </Tooltip>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 1 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress />
        </Box>
      ) : groups.length === 0 ? (
        <Box sx={{ textAlign: "center", py: 6 }}>
          <Typography variant="body2" color="text.secondary">
            {t("models:label.noSavedTests")}
          </Typography>
        </Box>
      ) : (
        <Box sx={{ overflow: "auto" }}>
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                {tableHeaders.map(({ label, align }) => (
                  <TableCell key={label} align={align}>
                    <Typography variant="subtitle3" sx={{ fontWeight: 700 }}>
                      {label}
                    </Typography>
                  </TableCell>
                ))}
                <TableCell sx={{ width: 48 }} />
              </TableRow>
            </TableHead>
            <TableBody>
              {groups.map((items) => {
                const head = items[0];
                const isBatch = items.length > 1;
                const key = head.group_id || `single:${head.id}`;
                const deleting = items.some((i) => deletingId === i.id);
                return (
                  <TableRow
                    key={key}
                    hover
                    sx={{ cursor: "pointer" }}
                    onClick={() => setSelectedGroup(items)}
                  >
                    <TableCell>{head.name || "—"}</TableCell>
                    <TableCell>{head.test_name}</TableCell>
                    <TableCell>{head.metric_name}</TableCell>
                    <TableCell>
                      {t("models:label." + head.metric_split)}
                    </TableCell>
                    <TableCell align="center">{resultCell(items)}</TableCell>
                    <TableCell align="right">
                      <Typography variant="caption" color="text.secondary">
                        {formatDate(head)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title={t("common:delete")}>
                        <span>
                          <IconButton
                            size="small"
                            onClick={(e) =>
                              handleDelete(
                                e,
                                isBatch ? items.map((i) => i.id) : head.id,
                              )
                            }
                            disabled={deleting}
                          >
                            {deleting ? (
                              <CircularProgress size={16} />
                            ) : (
                              <DeleteOutline fontSize="small" />
                            )}
                          </IconButton>
                        </span>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </Box>
      )}

      <SavedStatisticalTestResults
        open={!!selectedGroup}
        group={selectedGroup}
        onClose={() => setSelectedGroup(null)}
      />
    </Box>
  );
}

StatisticalTestTable.propTypes = {
  session: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  }),
};
