import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  MaterialReactTable,
  useMaterialReactTable,
} from "material-react-table";
import { Box, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import { useTableLocalization } from "../../../utils/useTableLocalization";
import { renameDatasetColumn } from "../../../api/datasets";
import EditableColumnHeader from "./EditableColumnHeader";

const FETCH_SIZE = 50;

export default function MrtDatasetTableInfScroll({
  fetchPage,
  initialPageSize = FETCH_SIZE,
  deps = [],
  datasetPath,
  datasetId,
  columnTypes = {},
  editableColumns = false,
  onEditColumn = null,
  maxHeight = "600px",
}) {
  const { t } = useTranslation(["common"]);
  const theme = useTheme();
  const localization = useTableLocalization();

  const fetchSize = initialPageSize ?? FETCH_SIZE;

  const [allData, setAllData] = useState([]);
  const [rowCount, setRowCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const [loadTrigger, setLoadTrigger] = useState(0);
  const [columnOrder, setColumnOrder] = useState([]);
  const [density, setDensity] = useState("compact");

  const tableContainerRef = useRef(null);
  const rowVirtualizerInstanceRef = useRef(null);

  const totalFetched = allData.length;

  const storageKey = datasetId
    ? `mrt-state-${datasetId}`
    : datasetPath
      ? `mrt-state-${datasetPath}`
      : null;

  const loadPersistedState = (key) => {
    if (!key) return null;
    try {
      const saved = localStorage.getItem(key);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  };

  const [columnFilters, setColumnFilters] = useState(() => {
    const saved = loadPersistedState(storageKey);
    return (saved?.columnFilters ?? []).filter(
      (f) =>
        f.id !== undefined &&
        !Array.isArray(f.value) &&
        f.value !== undefined &&
        f.value !== "",
    );
  });
  const [sorting, setSorting] = useState(() => {
    const saved = loadPersistedState(storageKey);
    return saved?.sorting ?? [];
  });

  const getDefaultFilterFns = () => {
    const defaults = {};
    Object.entries(columnTypes).forEach(([key, typeRaw]) => {
      const type =
        typeof typeRaw === "string" ? typeRaw : (typeRaw?.type ?? "");
      defaults[key] = ["Integer", "Float"].includes(type)
        ? "between"
        : "contains";
    });
    return defaults;
  };

  const [columnFilterFns, setColumnFilterFns] = useState(() => {
    const saved = loadPersistedState(storageKey);
    return saved?.columnFilterFns ?? getDefaultFilterFns();
  });
  const [showColumnFilters, setShowColumnFilters] = useState(() => {
    const saved = loadPersistedState(storageKey);
    return saved?.showColumnFilters ?? false;
  });

  useEffect(() => {
    const saved = loadPersistedState(storageKey);
    const cleanFilters = (saved?.columnFilters ?? []).filter(
      (f) =>
        f.id !== undefined &&
        !Array.isArray(f.value) &&
        f.value !== undefined &&
        f.value !== "",
    );
    setColumnFilters(cleanFilters);
    setSorting(saved?.sorting ?? []);
    setColumnFilterFns(saved?.columnFilterFns ?? getDefaultFilterFns());
    setShowColumnFilters(false);
    setDensity(saved?.density ?? "compact");
  }, deps); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!storageKey) return;
    try {
      localStorage.setItem(
        storageKey,
        JSON.stringify({
          columnFilters,
          columnFilterFns,
          sorting,
          density,
          showColumnFilters,
        }),
      );
    } catch {}
  }, [
    storageKey,
    columnFilters,
    columnFilterFns,
    sorting,
    density,
    showColumnFilters,
  ]);

  const buildFilterModel = useCallback(
    () => ({
      items: columnFilters
        .filter((f) => {
          const fn = columnFilterFns[f.id];
          if (fn === "empty" || fn === "notEmpty") return true;
          if (fn !== "between" && Array.isArray(f.value)) return false;
          return f.value !== undefined && f.value !== "";
        })
        .map((f) => {
          const fn = columnFilterFns[f.id];
          if (fn === "empty")
            return { field: f.id, value: null, operator: "isEmpty" };
          if (fn === "notEmpty")
            return { field: f.id, value: null, operator: "isNotEmpty" };
          const colTypeRaw = columnTypes[f.id];
          const colType =
            typeof colTypeRaw === "string"
              ? colTypeRaw
              : (colTypeRaw?.type ?? "");
          const operator =
            fn ??
            (["Integer", "Float"].includes(colType) ? "between" : "contains");
          const value =
            operator === "between" && typeof f.value === "string"
              ? f.value.split(",").map((v) => v.trim() || null)
              : f.value;
          return { field: f.id, value, operator };
        }),
    }),
    [columnFilters, columnFilterFns, columnTypes],
  );

  useEffect(() => {
    setAllData([]);
    setCurrentPage(0);
    setLoadTrigger((t) => t + 1);
    if (tableContainerRef.current) {
      tableContainerRef.current.scrollTop = 0;
    }
  }, [columnFilters, sorting, ...deps]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const isReset = currentPage === 0;
    const load = async () => {
      if (isReset) setIsLoading(true);
      else setIsFetching(true);
      try {
        const response = await fetchPage(
          currentPage,
          fetchSize,
          buildFilterModel(),
          sorting,
        );
        const rows = response?.rows ?? [];
        setRowCount(response?.total ?? 0);
        setAllData((prev) => (isReset ? rows : [...prev, ...rows]));
        if (rows.length > 0) {
          setColumnOrder(Object.keys(rows[0]));
        }
      } catch (error) {
        console.error("Error loading data:", error);
      } finally {
        setIsLoading(false);
        setIsFetching(false);
      }
    };
    load();
  }, [currentPage, loadTrigger]); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchMoreOnBottomReached = useCallback(
    (el) => {
      if (!el) return;
      const { scrollHeight, scrollTop, clientHeight } = el;
      if (
        scrollHeight - scrollTop - clientHeight < 300 &&
        !isFetching &&
        !isLoading &&
        totalFetched < rowCount
      ) {
        setCurrentPage((p) => p + 1);
      }
    },
    [isFetching, isLoading, totalFetched, rowCount],
  );

  useEffect(() => {
    fetchMoreOnBottomReached(tableContainerRef.current);
  }, [fetchMoreOnBottomReached]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleColumnRename = useCallback(
    async (oldName, newName) => {
      if (!datasetId) {
        throw new Error("Dataset ID is required for renaming columns");
      }
      const result = await renameDatasetColumn(datasetId, oldName, newName);
      onEditColumn && (await onEditColumn(result));

      setColumnOrder((prev) =>
        prev.map((col) => (col === oldName ? newName : col)),
      );

      const response = await fetchPage(0, fetchSize, buildFilterModel());
      const rows = response?.rows ?? [];
      setAllData(rows);
      setRowCount(response?.total ?? 0);

      return result;
    },
    [datasetId, onEditColumn, fetchPage, fetchSize, buildFilterModel],
  );

  const columns = useMemo(() => {
    let columnKeys = [];

    if (allData.length > 0) {
      columnKeys = Object.keys(allData[0]);
    } else if (Object.keys(columnTypes).length > 0) {
      columnKeys = Object.keys(columnTypes);
    } else {
      return [];
    }

    const getColType = (key) => {
      const val = columnTypes[key];
      if (!val) return null;
      return typeof val === "string" ? val : (val.type ?? null);
    };

    return columnKeys.map((key) => {
      const colTypeRaw = columnTypes[key];
      const colType =
        typeof colTypeRaw === "string" ? colTypeRaw : (colTypeRaw?.type ?? "");
      return {
        accessorKey: key,
        header: key,
        size: Math.max(
          180,
          Math.max(key.length, (getColType(key) ?? "").length) * 10 + 48,
        ),
        filterVariant: "text",
        filterFn: ["Integer", "Float"].includes(colType)
          ? "between"
          : "contains",
        columnFilterModeOptions: ["Integer", "Float"].includes(colType)
          ? [
              "equals",
              "between",
              "lessThan",
              "lessThanOrEqualTo",
              "greaterThan",
              "greaterThanOrEqualTo",
              "empty",
              "notEmpty",
            ]
          : [
              "contains",
              "startsWith",
              "endsWith",
              "equals",
              "empty",
              "notEmpty",
            ],
        Header: () =>
          editableColumns && datasetId ? (
            <div onDoubleClick={(e) => e.stopPropagation()}>
              <EditableColumnHeader
                columnName={key}
                columnType={getColType(key)}
                onRename={handleColumnRename}
              />
            </div>
          ) : (
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: "bold" }}>
                {key}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {getColType(key) || t("common:unknown")}
              </Typography>
            </Box>
          ),
      };
    });
  }, [allData, columnTypes, editableColumns, datasetId, handleColumnRename, t]);

  const table = useMaterialReactTable({
    columns,
    data: allData,
    muiTableBodyCellProps: { sx: { whiteSpace: "pre" } },
    localization,
    mrtTheme: { baseBackgroundColor: theme.palette.ui.panelDark },
    muiTablePaperProps: { elevation: 0 },
    enablePagination: false,
    enableRowVirtualization: true,
    rowVirtualizerInstanceRef,
    rowVirtualizerOptions: { overscan: 5 },
    manualFiltering: true,
    manualSorting: true,
    enableFilters: true,
    enableColumnFilterModes: true,
    onColumnFiltersChange: setColumnFilters,
    onColumnFilterFnsChange: setColumnFilterFns,
    onSortingChange: setSorting,
    onDensityChange: setDensity,
    onShowColumnFiltersChange: setShowColumnFilters,
    muiTableContainerProps: {
      ref: tableContainerRef,
      sx: { maxHeight },
      onScroll: (e) => fetchMoreOnBottomReached(e.target),
    },
    muiToolbarAlertBannerProps: undefined,
    renderBottomToolbarCustomActions: () => (
      <Typography variant="body2" sx={{ p: 2 }}>
        {totalFetched} / {rowCount} {t("common:rows")}
      </Typography>
    ),
    state: {
      columnFilters,
      columnFilterFns,
      sorting,
      columnOrder,
      showColumnFilters,
      density,
      isLoading,
      showProgressBars: isFetching,
    },
  });

  return (
    <Box sx={{ width: "100%" }}>
      <MaterialReactTable table={table} />
    </Box>
  );
}
