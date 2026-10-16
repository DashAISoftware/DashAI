import { useState } from "react";
import {
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  styled,
  Box,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import MoreHorizIcon from "@mui/icons-material/MoreHoriz";
import DeleteIcon from "@mui/icons-material/Delete";
import InfoIcon from "@mui/icons-material/Info";
import EditIcon from "@mui/icons-material/Edit";
import FileDownloadIcon from "@mui/icons-material/FileDownload";
import DeleteConfirmationModal from "./DeleteConfirmationModal";
import { useTranslation } from "react-i18next";

const DeleteMenuItem = styled(MenuItem)(({ theme }) => ({
  color: theme.palette.error.main,
  "& .MuiListItemIcon-root": {
    color: theme.palette.error.main,
  },
}));

export default function ItemMenu({
  itemId,
  onInfo,
  onDelete,
  onEdit,
  onExport,
  deleteConfirmationContent,
  deleteConfirmationWarning,
}) {
  const theme = useTheme();
  const [anchorEl, setAnchorEl] = useState(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const open = Boolean(anchorEl);
  const { t } = useTranslation(["common"]);

  const handleClick = (event) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleAction = (action, id) => {
    if (action === onDelete) {
      // Open confirmation modal instead of deleting immediately
      setDeleteModalOpen(true);
    } else if (action) {
      action(id);
    }
    handleClose();
  };

  const handleDeleteConfirm = (id) => {
    if (onDelete) {
      onDelete(id);
    }
  };

  return (
    <>
      <IconButton
        aria-label="more options"
        aria-controls={open ? "dataset-menu" : undefined}
        aria-haspopup="true"
        aria-expanded={open ? "true" : undefined}
        onClick={handleClick}
        size="small"
        sx={{ color: theme.palette.text.secondary }}
      >
        <MoreHorizIcon fontSize="small" />
      </IconButton>
      <Menu
        id="dataset-menu"
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "right",
        }}
        transformOrigin={{
          vertical: "top",
          horizontal: "right",
        }}
        onClick={(e) => e.stopPropagation()}
        slotProps={{
          list: {
            "aria-labelledby": "dataset-menu-button",
            dense: true,
          },
        }}
      >
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 1,
          }}
        >
          {/* Only show Info button if onInfo is provided */}
          {onInfo && (
            <MenuItem
              onClick={(e) => {
                e.stopPropagation();
                handleAction(onInfo, itemId);
              }}
            >
              <ListItemIcon>
                <InfoIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>{t("common:info")}</ListItemText>
            </MenuItem>
          )}
          {onEdit && (
            <MenuItem
              onClick={(e) => {
                e.stopPropagation();
                handleAction(onEdit, itemId);
              }}
            >
              <ListItemIcon>
                <EditIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>{t("common:edit")}</ListItemText>
            </MenuItem>
          )}
          {onExport && (
            <MenuItem
              onClick={(e) => {
                e.stopPropagation();
                handleAction(onExport, itemId);
              }}
            >
              <ListItemIcon>
                <FileDownloadIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>{t("common:export")}</ListItemText>
            </MenuItem>
          )}
          <Divider />
        </Box>
        <DeleteMenuItem
          onClick={(e) => {
            e.stopPropagation();
            handleAction(onDelete, itemId);
          }}
        >
          <ListItemIcon>
            <DeleteIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>{t("common:delete")}</ListItemText>
        </DeleteMenuItem>
      </Menu>
      {/* Confirmation Modal */}
      <DeleteConfirmationModal
        content={deleteConfirmationContent}
        warning={deleteConfirmationWarning}
        open={deleteModalOpen}
        onClose={(e) => {
          e.stopPropagation();
          setDeleteModalOpen(false);
        }}
        onConfirm={(e) => {
          e.stopPropagation();
          handleDeleteConfirm(itemId);
          setDeleteModalOpen(false);
        }}
      />
    </>
  );
}
