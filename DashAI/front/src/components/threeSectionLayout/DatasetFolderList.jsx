import { useState, useRef, useEffect } from "react";
import {
  Box,
  Button,
  Checkbox,
  Typography,
  Collapse,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Tooltip,
  TextField,
  styled,
} from "@mui/material";
import { LoadingButton } from "@mui/lab";
import { useTheme } from "@mui/material/styles";
import FolderIcon from "@mui/icons-material/Folder";
import FolderOpenIcon from "@mui/icons-material/FolderOpen";
import KeyboardArrowRightIcon from "@mui/icons-material/KeyboardArrowRight";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import CreateNewFolderIcon from "@mui/icons-material/CreateNewFolder";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import MoreHorizIcon from "@mui/icons-material/MoreHoriz";
import StorageIcon from "@mui/icons-material/Storage";
import { DisabledByDefaultOutlined as SelectItemsIcon } from "@mui/icons-material";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { t } from "i18next";
import DeleteConfirmationModal from "./DeleteConfirmationModal";
import ItemBox from "./ItemBox";

const DeleteMenuItem = styled(MenuItem)(({ theme }) => ({
  color: theme.palette.error.main,
  "& .MuiListItemIcon-root": {
    color: theme.palette.error.main,
  },
}));

const NO_FOLDER_ID = "__no_folder__";

function DraggableDataset({ dataset, children }) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: String(dataset.id),
    data: { type: "dataset", datasetId: dataset.id },
  });

  return (
    <Box
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      sx={{ opacity: isDragging ? 0.4 : 1, touchAction: "none" }}
    >
      {children}
    </Box>
  );
}

function DroppableFolder({ id, isOver, children }) {
  const { setNodeRef } = useDroppable({ id });
  const theme = useTheme();

  return (
    <Box
      ref={setNodeRef}
      sx={{
        borderRadius: 1,
        transition: "background-color 0.15s",
        bgcolor: isOver ? theme.palette.action.selected : "transparent",
        outline: isOver ? `2px dashed ${theme.palette.primary.main}` : "none",
      }}
    >
      {children}
    </Box>
  );
}

function FolderSection({
  folderId,
  folderName,
  items,
  isOver,
  defaultOpen,
  open: controlledOpen,
  onToggleOpen,
  selectedItemId,
  onItemClick,
  onItemDelete,
  onItemEdit,
  onItemInfo,
  getItemDescription,
  getDeleteConfirmationContent,
  getDeleteConfirmationWarning,
  onRenameFolder,
  onDeleteFolder,
  selectionMode,
  selectedIds,
  onToggleSelect,
}) {
  const theme = useTheme();
  const isControlled = controlledOpen !== undefined;
  const [internalOpen, setInternalOpen] = useState(defaultOpen ?? true);
  const open = isControlled ? controlledOpen : internalOpen;
  const setOpen = (updater) => {
    const next = typeof updater === "function" ? updater(open) : updater;
    if (isControlled) {
      onToggleOpen?.(next);
    } else {
      setInternalOpen(next);
    }
  };
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState(folderName);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [menuAnchorEl, setMenuAnchorEl] = useState(null);
  const renameInputRef = useRef(null);

  useEffect(() => {
    if (isRenaming && renameInputRef.current) {
      renameInputRef.current.focus();
    }
  }, [isRenaming]);

  const handleRenameKeyDown = async (e) => {
    if (e.key === "Enter") {
      if (renameValue.trim() && renameValue.trim() !== folderName) {
        try {
          await onRenameFolder(folderId, renameValue.trim());
          setIsRenaming(false);
        } catch {
          setRenameValue(folderName);
          setIsRenaming(false);
        }
      } else {
        setIsRenaming(false);
        setRenameValue(folderName);
      }
    }
    if (e.key === "Escape") {
      setIsRenaming(false);
      setRenameValue(folderName);
    }
  };

  const handleRenameBlur = async () => {
    if (renameValue.trim() && renameValue.trim() !== folderName) {
      try {
        await onRenameFolder(folderId, renameValue.trim());
        setIsRenaming(false);
      } catch {
        setRenameValue(folderName);
        setIsRenaming(false);
      }
    } else {
      setIsRenaming(false);
      setRenameValue(folderName);
    }
  };

  const FolderIconComp = open ? FolderOpenIcon : FolderIcon;
  const count = items?.length ?? 0;

  return (
    <DroppableFolder id={String(folderId)} isOver={isOver}>
      <Box mb={1}>
        {/* Folder header */}
        <Box
          display="flex"
          alignItems="center"
          sx={{
            cursor: "pointer",
            py: 1,
            px: 2,
            borderRadius: 1,
            "&:hover": { bgcolor: theme.palette.ui.hover },
          }}
          onClick={() => !isRenaming && setOpen((v) => !v)}
        >
          {open ? (
            <KeyboardArrowDownIcon
              sx={{ fontSize: 16, color: theme.palette.primary.main, mr: 1 }}
            />
          ) : (
            <KeyboardArrowRightIcon
              sx={{ fontSize: 16, color: theme.palette.primary.main, mr: 1 }}
            />
          )}

          <FolderIconComp
            sx={{ fontSize: 18, color: theme.palette.primary.main, mr: 2 }}
          />

          {isRenaming ? (
            <TextField
              inputRef={renameInputRef}
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              onKeyDown={handleRenameKeyDown}
              onBlur={handleRenameBlur}
              onClick={(e) => e.stopPropagation()}
              size="small"
              variant="outlined"
              sx={{
                flex: 1,
                "& .MuiInputBase-input": { fontSize: 12, padding: "2px 6px" },
              }}
            />
          ) : (
            <Typography
              variant="h5"
              sx={{
                flex: 1,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
              color="text.primary"
            >
              {folderName}
            </Typography>
          )}

          <Typography
            variant="body2"
            component="div"
            sx={{
              ml: 1,
              mr: 1,
              bgcolor: "primary.main",
              color: "primary.contrastText",
              borderRadius: "50%",
              width: 18,
              height: 18,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 12,
              flexShrink: 0,
            }}
          >
            {count}
          </Typography>

          <>
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                setMenuAnchorEl(e.currentTarget);
              }}
              sx={{ ml: 1, flexShrink: 0 }}
            >
              <MoreHorizIcon sx={{ fontSize: 16 }} />
            </IconButton>
            <Menu
              anchorEl={menuAnchorEl}
              open={Boolean(menuAnchorEl)}
              onClose={() => setMenuAnchorEl(null)}
              onClick={(e) => e.stopPropagation()}
            >
              <MenuItem
                onClick={() => {
                  setMenuAnchorEl(null);
                  setRenameValue(folderName);
                  setIsRenaming(true);
                }}
              >
                <ListItemIcon>
                  <EditIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>{t("common:edit", "Edit")}</ListItemText>
              </MenuItem>
              <Divider />
              <DeleteMenuItem
                onClick={() => {
                  setMenuAnchorEl(null);
                  setDeleteDialogOpen(true);
                }}
              >
                <ListItemIcon>
                  <DeleteIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>{t("common:delete", "Delete")}</ListItemText>
              </DeleteMenuItem>
            </Menu>
          </>
        </Box>

        {/* Items */}
        <Collapse in={open} timeout="auto">
          <Box pl={6}>
            {items?.length ? (
              items.map((item) => {
                const itemBox = (
                  <ItemBox
                    isSelected={item.id === selectedItemId}
                    name={item.name}
                    description={
                      getItemDescription ? getItemDescription(item) : ""
                    }
                    id={item.id}
                    onClick={() => onItemClick(item.id)}
                    onDelete={() => onItemDelete(item.id)}
                    onEdit={
                      onItemEdit
                        ? (name) => onItemEdit(item.id, name)
                        : undefined
                    }
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
                    checked={selectedIds?.has(item.id)}
                    onToggleSelect={onToggleSelect}
                  />
                );
                return selectionMode ? (
                  <Box key={item.id}>{itemBox}</Box>
                ) : (
                  <DraggableDataset key={item.id} dataset={item}>
                    {itemBox}
                  </DraggableDataset>
                );
              })
            ) : (
              <Typography
                variant="body2"
                sx={{
                  color: theme.palette.text.primary,
                  opacity: 0.4,
                  textAlign: "center",
                  py: 2,
                }}
              >
                {t("common:noItemsAvailable", "No items available.")}
              </Typography>
            )}
          </Box>
        </Collapse>
      </Box>

      <DeleteConfirmationModal
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={() => {
          setDeleteDialogOpen(false);
          onDeleteFolder(folderId);
        }}
        content={t(
          "datasets:label.confirmDeleteFolderContent",
          'Are you sure you want to delete the folder "{{name}}"? Datasets inside will be moved to no folder.',
          { name: folderName },
        )}
      />
    </DroppableFolder>
  );
}

export default function DatasetFolderList({
  datasets = [],
  folders = [],
  selectedItemId,
  onItemClick,
  onItemDelete,
  onItemEdit,
  onItemInfo,
  onMoveDataset,
  onCreateFolder,
  onRenameFolder,
  onDeleteFolder,
  onBulkDelete,
  getItemDescription,
  getDeleteConfirmationContent,
  getDeleteConfirmationWarning,
  title,
  openFolderIds = {},
  setOpenFolderIds,
}) {
  const theme = useTheme();
  const [activeId, setActiveId] = useState(null);
  const [overId, setOverId] = useState(null);
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const newFolderInputRef = useRef(null);
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState(() => new Set());
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false);
  const [bulkDeleting, setBulkDeleting] = useState(false);

  useEffect(() => {
    if (isCreatingFolder && newFolderInputRef.current) {
      newFolderInputRef.current.focus();
    }
  }, [isCreatingFolder]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 5 },
    }),
  );

  const datasetById = Object.fromEntries(
    datasets.map((d) => [String(d.id), d]),
  );
  const activeDataset = activeId ? datasetById[activeId] : null;

  const handleDragStart = ({ active }) => {
    setActiveId(active.id);
  };

  const handleDragOver = ({ over }) => {
    setOverId(over ? over.id : null);
  };

  const handleDragEnd = ({ active, over }) => {
    setActiveId(null);
    setOverId(null);
    if (!over) return;
    const targetFolderId = over.id === NO_FOLDER_ID ? null : Number(over.id);
    const dataset = datasetById[active.id];
    if (!dataset) return;
    const currentFolderId = dataset.folder_id ?? null;
    if (currentFolderId === targetFolderId) return;
    onMoveDataset(dataset.id, targetFolderId);
  };

  const handleCreateFolder = async () => {
    const name = newFolderName.trim();
    if (!name) {
      setIsCreatingFolder(false);
      setNewFolderName("");
      return;
    }
    try {
      await onCreateFolder(name);
    } catch {
      // error shown by hook
    } finally {
      setIsCreatingFolder(false);
      setNewFolderName("");
    }
  };

  const handleNewFolderKeyDown = (e) => {
    if (e.key === "Enter") handleCreateFolder();
    if (e.key === "Escape") {
      setIsCreatingFolder(false);
      setNewFolderName("");
    }
  };

  const noFolderDatasets = datasets.filter((d) => !d.folder_id);
  const totalCount = datasets.length;

  const handleToggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const allSelected =
    totalCount > 0 && datasets.every((d) => selectedIds.has(d.id));

  const handleToggleSelectAll = () => {
    setSelectedIds(
      allSelected ? new Set() : new Set(datasets.map((d) => d.id)),
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
      sx={{ overflowY: "hidden", flex: 1, pl: 4, pr: 4, pt: 4 }}
    >
      {/* Header */}
      <Box
        display="flex"
        alignItems="center"
        py={2}
        px={4}
        mb={2}
        sx={{ borderRadius: 1 }}
      >
        {selectionMode ? (
          <>
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
              title={t("datasets:button.deleteSelectedDatasets", {
                defaultValue: "Delete Selected ({{count}})",
                count: selectedIds.size,
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
          </>
        ) : (
          <>
            <StorageIcon
              sx={{ color: theme.palette.primary.main, mr: 2, fontSize: 20 }}
            />
            <Typography
              sx={{
                ...theme.typography.h5,
                flex: 1,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
              color="text.primary"
            >
              {title || t("common:availableItems", "Available Items")}
            </Typography>
            <Typography
              variant="body2"
              component="div"
              sx={{
                bgcolor: "primary.main",
                color: "primary.contrastText",
                borderRadius: "50%",
                width: 20,
                height: 20,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                mr: 2,
              }}
            >
              {totalCount}
            </Typography>
            <Tooltip title={t("datasets:label.newFolder", "New folder")}>
              <IconButton
                size="small"
                onClick={() => setIsCreatingFolder(true)}
              >
                <CreateNewFolderIcon sx={{ fontSize: 18 }} />
              </IconButton>
            </Tooltip>
            {onBulkDelete && (
              <Tooltip
                title={t(
                  "datasets:label.selectDatasetsToDelete",
                  "Select datasets to delete",
                )}
              >
                <span>
                  <IconButton
                    size="small"
                    disabled={totalCount === 0}
                    onClick={() => setSelectionMode(true)}
                  >
                    <SelectItemsIcon sx={{ fontSize: 18 }} />
                  </IconButton>
                </span>
              </Tooltip>
            )}
          </>
        )}
      </Box>

      {/* New folder input */}
      {!selectionMode && isCreatingFolder && (
        <Box display="flex" alignItems="center" px={4} pb={2} gap={1}>
          <FolderIcon
            sx={{ fontSize: 18, color: theme.palette.primary.main }}
          />
          <TextField
            inputRef={newFolderInputRef}
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            onKeyDown={handleNewFolderKeyDown}
            onBlur={handleCreateFolder}
            placeholder={t("datasets:label.folderName", "Folder name")}
            size="small"
            variant="outlined"
            sx={{
              flex: 1,
              "& .MuiInputBase-input": { fontSize: 12, padding: "4px 8px" },
            }}
          />
        </Box>
      )}

      {/* Folders + datasets — scrollable */}
      <Box
        sx={{
          flex: 1,
          overflowY: "auto",
          scrollbarGutter: "stable",
          "&::-webkit-scrollbar": { width: "6px" },
          "&::-webkit-scrollbar-thumb": {
            backgroundColor: theme.palette.ui.scrollbar,
            borderRadius: "3px",
          },
          "&::-webkit-scrollbar-thumb:hover": {
            backgroundColor: theme.palette.ui.scrollbarHover,
          },
        }}
      >
        <DndContext
          sensors={sensors}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragEnd={handleDragEnd}
        >
          {/* Named folders */}
          {folders.map((folder) => {
            const folderDatasets = datasets.filter(
              (d) => d.folder_id === folder.id,
            );
            return (
              <FolderSection
                key={folder.id}
                folderId={folder.id}
                folderName={folder.name}
                items={folderDatasets}
                isOver={overId === String(folder.id)}
                open={selectionMode || (openFolderIds[folder.id] ?? true)}
                onToggleOpen={(next) =>
                  setOpenFolderIds?.((prev) => ({
                    ...prev,
                    [folder.id]: next,
                  }))
                }
                selectedItemId={selectedItemId}
                onItemClick={onItemClick}
                onItemDelete={onItemDelete}
                onItemEdit={onItemEdit}
                onItemInfo={onItemInfo}
                getItemDescription={getItemDescription}
                getDeleteConfirmationContent={getDeleteConfirmationContent}
                getDeleteConfirmationWarning={getDeleteConfirmationWarning}
                onRenameFolder={onRenameFolder}
                onDeleteFolder={onDeleteFolder}
                selectionMode={selectionMode}
                selectedIds={selectedIds}
                onToggleSelect={handleToggleSelect}
              />
            );
          })}

          {/* Loose datasets — no folder */}
          <DroppableFolder id={NO_FOLDER_ID} isOver={overId === NO_FOLDER_ID}>
            {noFolderDatasets.map((item) => {
              const itemBox = (
                <ItemBox
                  isSelected={item.id === selectedItemId}
                  name={item.name}
                  description={
                    getItemDescription ? getItemDescription(item) : ""
                  }
                  id={item.id}
                  onClick={() => onItemClick(item.id)}
                  onDelete={() => onItemDelete(item.id)}
                  onEdit={
                    onItemEdit ? (name) => onItemEdit(item.id, name) : undefined
                  }
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
              );
              return selectionMode ? (
                <Box key={item.id}>{itemBox}</Box>
              ) : (
                <DraggableDataset key={item.id} dataset={item}>
                  {itemBox}
                </DraggableDataset>
              );
            })}
          </DroppableFolder>

          {/* Drag overlay — ghost item while dragging */}
          <DragOverlay>
            {activeDataset ? (
              <Box
                sx={{
                  bgcolor: theme.palette.background.paper,
                  border: `1px solid ${theme.palette.primary.main}`,
                  borderRadius: 1,
                  px: 2,
                  py: 1,
                  boxShadow: 4,
                  maxWidth: 200,
                }}
              >
                <Typography variant="body2" noWrap>
                  {activeDataset.name}
                </Typography>
              </Box>
            ) : null}
          </DragOverlay>
        </DndContext>
      </Box>

      <DeleteConfirmationModal
        open={bulkDeleteOpen}
        onClose={() => setBulkDeleteOpen(false)}
        onConfirm={handleBulkDeleteConfirm}
        content={t(
          "datasets:label.confirmBulkDeleteDatasets",
          "Are you sure you want to delete the {{count}} selected datasets? This action cannot be undone.",
          { count: selectedIds.size },
        )}
        warning={t(
          "datasets:label.confirmDeleteDatasetLinkedWarning",
          "All notebooks and sessions linked to this dataset will also be deleted.",
        )}
      />
    </Box>
  );
}
