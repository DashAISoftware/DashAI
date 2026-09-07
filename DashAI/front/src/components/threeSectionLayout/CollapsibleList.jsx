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
import FolderIcon from "@mui/icons-material/Folder";
import KeyboardArrowRightIcon from "@mui/icons-material/KeyboardArrowRight";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import DeleteIcon from "@mui/icons-material/Delete";
import { DisabledByDefaultOutlined as SelectItemsIcon } from "@mui/icons-material";
import ItemBox from "./ItemBox";
import DeleteConfirmationModal from "./DeleteConfirmationModal";
import { t } from "i18next";

export default function CollapsibleList({
  items = [],
  selectedItemId,
  onItemClick,
  onItemDelete,
  onItemEdit,
  onItemInfo,
  defaultOpen = true,
  collapsible = true,
  title = t("common:availableItems", "Available Items"),
  Icon = FolderIcon,
  getItemDescription,
  getDeleteConfirmationContent,
  getDeleteConfirmationWarning,
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
  const [open, setOpen] = useState(defaultOpen);
  const count = items?.length ?? 0;
  const prevCountRef = useRef(count);
  const lastItemRef = useRef(null);
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState(() => new Set());
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false);
  const [bulkDeleting, setBulkDeleting] = useState(false);

  useEffect(() => {
    const prevCount = prevCountRef.current;

    if (count > prevCount && prevCount > 0) {
      setOpen(true);

      setTimeout(() => {
        if (lastItemRef.current) {
          lastItemRef.current.scrollIntoView({
            behavior: "smooth",
            block: "nearest",
          });
        }
      }, 300);
    }

    prevCountRef.current = count;
  }, [count]);

  const defaultGetDescription = (item) => item.description || "";

  const handleToggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const allSelected =
    count > 0 && items.every((item) => selectedIds.has(item.id));

  const handleToggleSelectAll = () => {
    setSelectedIds(
      allSelected ? new Set() : new Set(items.map((item) => item.id)),
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
      {/* Header de la carpeta */}
      {selectionMode ? (
        <Box
          display="flex"
          alignItems="center"
          py={2}
          px={4}
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
          sx={{
            cursor: collapsible ? "pointer" : "default",
            py: 2,
            px: 4,
            borderRadius: 1,
            ...(collapsible && {
              "&:hover": { bgcolor: theme.palette.ui.hover },
            }),
          }}
          onClick={collapsible ? () => setOpen((v) => !v) : undefined}
        >
          <Icon
            sx={{ fontSize: 20, color: theme.palette.primary.main, mr: 4 }}
          />

          <Typography
            variant="h5"
            sx={{
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
              mr: 2,
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
            {count}
          </Typography>

          {onBulkDelete && (
            <Tooltip title={selectItemsTooltip}>
              <span>
                <IconButton
                  size="small"
                  disabled={count === 0}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectionMode(true);
                  }}
                >
                  <SelectItemsIcon sx={{ fontSize: 18 }} />
                </IconButton>
              </span>
            </Tooltip>
          )}

          {collapsible && (
            <IconButton
              size="small"
              disableRipple
              disableFocusRipple
              sx={{ cursor: "inherit" }}
            >
              {open ? (
                <KeyboardArrowDownIcon
                  sx={{ fontSize: 20, color: theme.palette.primary.main }}
                />
              ) : (
                <KeyboardArrowRightIcon
                  sx={{ fontSize: 20, color: theme.palette.primary.main }}
                />
              )}
            </IconButton>
          )}
        </Box>
      )}

      {/* Collapsible list */}
      <Collapse
        in={collapsible ? open : true}
        timeout="auto"
        sx={{
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
        <Box pl={4}>
          {items?.length ? (
            items.map((ds, index) => (
              <ItemBox
                key={ds.id ?? ds.name}
                ref={index === items.length - 1 ? lastItemRef : null}
                isSelected={ds.id === selectedItemId}
                name={ds.name}
                description={
                  getItemDescription
                    ? getItemDescription(ds)
                    : defaultGetDescription(ds)
                }
                id={ds.id}
                onClick={() => onItemClick(ds.id)}
                onDelete={() => onItemDelete(ds.id)}
                onEdit={
                  onItemEdit ? (name) => onItemEdit(ds.id, name) : undefined
                }
                onInfo={onItemInfo ? () => onItemInfo(ds.id) : undefined}
                deleteConfirmationContent={
                  getDeleteConfirmationContent
                    ? getDeleteConfirmationContent(ds)
                    : undefined
                }
                deleteConfirmationWarning={
                  getDeleteConfirmationWarning
                    ? getDeleteConfirmationWarning(ds)
                    : undefined
                }
                selectable={selectionMode}
                checked={selectedIds.has(ds.id)}
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
              {t("common:noItemsAvailable", "No items available.")}
            </Typography>
          )}
        </Box>
      </Collapse>

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
