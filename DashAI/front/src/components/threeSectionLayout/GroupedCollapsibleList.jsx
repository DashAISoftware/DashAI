import { useState, useEffect, useRef } from "react";
import {
  Box,
  Button,
  Checkbox,
  Typography,
  Collapse,
  IconButton,
  Tooltip,
} from "@mui/material";
import { LoadingButton } from "@mui/lab";
import { useTheme } from "@mui/material/styles";
import KeyboardArrowRightIcon from "@mui/icons-material/KeyboardArrowRight";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import DeleteIcon from "@mui/icons-material/Delete";
import { DisabledByDefaultOutlined as SelectItemsIcon } from "@mui/icons-material";
import ItemBox from "./ItemBox";
import DeleteConfirmationModal from "./DeleteConfirmationModal";
import { t } from "i18next";

export default function GroupedCollapsibleList({
  groups = {}, // Object with group names as keys and items arrays as values
  selectedItemId,
  onItemClick,
  onItemDelete,
  onItemEdit,
  onItemInfo,
  title = t("common:items", "Items"),
  Icon,
  getItemDescription,
  getDeleteConfirmationContent,
  getDeleteConfirmationWarning,
  initialOpenGroups = {},
  openGroups: controlledOpenGroups,
  onOpenGroupsChange,
  onBulkDelete,
  selectItemsTooltip = t(
    "common:selectItemsToDelete",
    "Select items to delete",
  ),
  getBulkDeleteConfirmationContent = (count) =>
    t("common:confirmBulkDeleteItems", {
      count,
      defaultValue:
        "Are you sure you want to delete the {{count}} selected items? This action cannot be undone.",
    }),
  bulkDeleteConfirmationWarning,
}) {
  const theme = useTheme();
  const isControlled = controlledOpenGroups !== undefined;
  const [internalOpenGroups, setInternalOpenGroups] =
    useState(initialOpenGroups);
  const openGroups = isControlled ? controlledOpenGroups : internalOpenGroups;
  const setOpenGroups = (updater) => {
    const next = typeof updater === "function" ? updater(openGroups) : updater;
    // Bail out on no-op updates. These are flat {groupName: boolean} maps, so a
    // shallow key/value comparison is enough. Without this, a "set group X open"
    // call for an already-open group would still notify the controlled parent,
    // which re-renders the caller, which rebuilds `groups`, which re-triggers
    // the auto-open effect below -> infinite render loop.
    const isSame =
      next === openGroups ||
      (!!next &&
        !!openGroups &&
        Object.keys(next).length === Object.keys(openGroups).length &&
        Object.keys(next).every((key) => next[key] === openGroups[key]));
    if (isSame) return;
    if (isControlled) {
      onOpenGroupsChange?.(next);
    } else {
      setInternalOpenGroups(next);
    }
  };
  const selectedItemRef = useRef(null);
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState(() => new Set());
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false);
  const [bulkDeleting, setBulkDeleting] = useState(false);

  const groupEntries = Object.entries(groups || {});
  const allItems = groupEntries.flatMap(([, items]) => items ?? []);
  // One group under a section header that already names the list adds a level
  // of nesting that carries no information, so it is rendered flat.
  const showGroupHeaders = groupEntries.length > 1;

  // Auto-open group when an item is selected. A flattened single group is
  // always visible, so there is nothing to open.
  useEffect(() => {
    if (selectedItemId && showGroupHeaders) {
      // Find which group contains the selected item
      for (const [groupName, items] of Object.entries(groups)) {
        if (items?.some((item) => item.id === selectedItemId)) {
          setOpenGroups((prev) => ({
            ...prev,
            [groupName]: true,
          }));
          break;
        }
      }
    }
  }, [selectedItemId, groups]);

  // Scroll to selected item after group is opened
  useEffect(() => {
    if (selectedItemId && selectedItemRef.current) {
      // Use setTimeout to ensure the Collapse animation has completed
      setTimeout(() => {
        selectedItemRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
        });
      }, 350);
    }
  }, [selectedItemId, openGroups]);

  const toggleGroup = (groupName) => {
    setOpenGroups((prev) => ({
      ...prev,
      [groupName]: !prev[groupName],
    }));
  };

  const totalCount = allItems.length;

  const defaultGetDescription = (item) => item.description || "";

  /**
   * Render one group's items, or the empty notice when it has none.
   * @param {Array} items - The items to render.
   * @returns {JSX.Element|JSX.Element[]} The rendered rows.
   */
  const renderItems = (items) =>
    items?.length ? (
      items.map((item) => (
        <ItemBox
          key={item.id ?? item.name}
          ref={item.id === selectedItemId ? selectedItemRef : null}
          isSelected={item.id === selectedItemId}
          name={item.name}
          description={
            getItemDescription
              ? getItemDescription(item)
              : defaultGetDescription(item)
          }
          id={item.id}
          onClick={() => onItemClick(item.id)}
          onDelete={() => onItemDelete(item.id)}
          onEdit={(name) => onItemEdit(item.id, name)}
          onInfo={onItemInfo ? () => onItemInfo(item.id) : undefined}
          deleteConfirmationContent={
            getDeleteConfirmationContent
              ? getDeleteConfirmationContent(item)
              : undefined
          }
          deleteConfirmationWarning={
            getDeleteConfirmationWarning
              ? getDeleteConfirmationWarning(item)
              : undefined
          }
          selectable={selectionMode}
          checked={selectedIds.has(item.id)}
          onToggleSelect={handleToggleSelect}
        />
      ))
    ) : (
      <Typography
        sx={{
          color: theme.palette.text.primary,
          opacity: 0.5,
          textAlign: "center",
          p: 8,
        }}
      >
        {t("common:noItemsInGroup", "No items found.")}
      </Typography>
    );

  const handleToggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const allSelected =
    totalCount > 0 && allItems.every((item) => selectedIds.has(item.id));

  const handleToggleSelectAll = () => {
    setSelectedIds(
      allSelected ? new Set() : new Set(allItems.map((item) => item.id)),
    );
  };

  const handleExitSelectionMode = () => {
    setSelectionMode(false);
    setSelectedIds(new Set());
  };

  const handleBulkDeleteConfirm = async () => {
    const ids = [...selectedIds];
    if (ids.length === 0) {
      setBulkDeleteOpen(false);
      return;
    }
    setBulkDeleting(true);
    try {
      const success = await onBulkDelete(ids);
      setBulkDeleteOpen(false);
      if (success !== false) {
        handleExitSelectionMode();
      }
    } finally {
      setBulkDeleting(false);
    }
  };

  return (
    <Box
      display="flex"
      flexDirection="column"
      pb={4}
      sx={{
        overflowY: "hidden",
        flex: 1,
        pl: 4,
        pr: 4,
        pt: 4,
      }}
    >
      {/* Main Header */}
      {selectionMode ? (
        <Box
          display="flex"
          alignItems="center"
          py={2}
          px={4}
          mb={2}
          sx={{ borderRadius: 1 }}
        >
          <Checkbox
            size="small"
            checked={allSelected}
            indeterminate={!allSelected && selectedIds.size > 0}
            onChange={handleToggleSelectAll}
            sx={{ p: 0.5, mr: 1 }}
          />
          <Typography variant="body2" color="text.secondary" sx={{ flex: 1 }}>
            {t("common:selected", "Selected")} ({selectedIds.size})
          </Typography>
          <Tooltip
            title={t("common:deleteSelected", {
              count: selectedIds.size,
              defaultValue: "Delete Selected ({{count}})",
            })}
          >
            <span>
              <LoadingButton
                size="small"
                variant="contained"
                color="error"
                startIcon={<DeleteIcon fontSize="small" />}
                disabled={selectedIds.size === 0}
                loading={bulkDeleting}
                onClick={() => setBulkDeleteOpen(true)}
                sx={{
                  textTransform: "none",
                  fontWeight: 500,
                  mr: 1,
                  minWidth: 0,
                }}
              >
                ({selectedIds.size})
              </LoadingButton>
            </span>
          </Tooltip>
          <Button size="small" onClick={handleExitSelectionMode}>
            {t("common:cancel")}
          </Button>
        </Box>
      ) : (
        <Box
          display="flex"
          alignItems="center"
          py={2}
          px={4}
          mb={2}
          sx={{
            position: "sticky",
            top: 0,
            zIndex: 10,
            borderRadius: 1,
            "&:hover": { bgcolor: theme.palette.ui.hover },
          }}
        >
          {Icon && (
            <Icon
              sx={{ color: theme.palette.primary.main, mr: 4, fontSize: 20 }}
            />
          )}
          <Typography
            sx={{
              ...theme.typography.h5,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
              flex: 1,
            }}
            title={title}
            color="text.primary"
          >
            {title}
          </Typography>
          <Typography
            variant="body2"
            component="div"
            sx={{
              mr: onBulkDelete ? 2 : 0,
              bgcolor: "primary.main",
              color: "primary.contrastText",
              borderRadius: "50%",
              width: 20,
              height: 20,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {totalCount}
          </Typography>
          {onBulkDelete && (
            <Tooltip title={selectItemsTooltip}>
              <span>
                <IconButton
                  size="small"
                  disabled={totalCount === 0}
                  onClick={() => {
                    setSelectionMode(true);
                    setOpenGroups((prev) => {
                      const next = { ...prev };
                      Object.keys(groups).forEach((groupName) => {
                        next[groupName] = true;
                      });
                      return next;
                    });
                  }}
                >
                  <SelectItemsIcon sx={{ fontSize: 18 }} />
                </IconButton>
              </span>
            </Tooltip>
          )}
        </Box>
      )}

      {/* Groups - Scrollable */}
      <Box
        sx={{
          flex: 1,
          overflow: "auto",
          scrollbarGutter: "stable",
          "&::-webkit-scrollbar": { width: "6px" },
          "&::-webkit-scrollbar-thumb": {
            backgroundColor: theme.palette.ui.scrollbar,
            borderRadius: "3px",
          },
          "&::-webkit-scrollbar-thumb:hover": {
            backgroundColor: theme.palette.ui.scrollbarHover,
          },
          overflowY: "auto",
        }}
      >
        {!showGroupHeaders && (
          <Box pl={4}>{renderItems(groupEntries[0]?.[1] ?? [])}</Box>
        )}

        {showGroupHeaders &&
          groupEntries.map(([groupName, items]) => (
            <Box key={groupName} mb={2}>
              {/* Group Header */}
              <Box
                display="flex"
                alignItems="center"
                sx={{
                  cursor: "pointer",
                  py: 2,
                  px: 4,
                  borderRadius: 1,
                  "&:hover": {
                    bgcolor: theme.palette.ui.hover,
                  },
                }}
                onClick={() => toggleGroup(groupName)}
              >
                {openGroups[groupName] ? (
                  <KeyboardArrowDownIcon
                    sx={{ fontSize: 20, color: theme.palette.primary.main }}
                  />
                ) : (
                  <KeyboardArrowRightIcon
                    sx={{ fontSize: 20, color: theme.palette.primary.main }}
                  />
                )}
                <Typography
                  sx={{
                    ml: 4,
                    ...theme.typography.h5,
                    textTransform: "capitalize",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    wordBreak: "break-all",
                    whiteSpace: "nowrap",
                    flex: 1,
                  }}
                  color="text.primary"
                >
                  {groupName}
                </Typography>
                <Typography
                  variant="body2"
                  component="div"
                  sx={{
                    ml: 4,
                    bgcolor: "primary.main",
                    color: "primary.contrastText",
                    borderRadius: "50%",
                    width: 20,
                    height: 20,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  {items?.length || 0}
                </Typography>
              </Box>

              {/* Group Items */}
              <Collapse in={openGroups[groupName]} timeout="auto">
                <Box pl={4}>{renderItems(items)}</Box>
              </Collapse>
            </Box>
          ))}
      </Box>

      {onBulkDelete && (
        <DeleteConfirmationModal
          open={bulkDeleteOpen}
          onClose={() => setBulkDeleteOpen(false)}
          onConfirm={handleBulkDeleteConfirm}
          content={getBulkDeleteConfirmationContent(selectedIds.size)}
          warning={bulkDeleteConfirmationWarning}
        />
      )}
    </Box>
  );
}
