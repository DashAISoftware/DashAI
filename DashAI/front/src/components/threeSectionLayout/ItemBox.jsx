import { useState, useRef, useEffect, forwardRef } from "react";
import { Box, Checkbox, Typography, TextField } from "@mui/material";
import ItemMenu from "./ItemMenu";
import { useTheme } from "@mui/material/styles";

const ItemBox = forwardRef(function ItemBox(
  {
    isSelected,
    name,
    description,
    id,
    onClick,
    onDelete,
    onEdit,
    onInfo,
    deleteConfirmationContent,
    deleteConfirmationWarning,
    selectable = false,
    checked = false,
    onToggleSelect,
  },
  ref,
) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedName, setEditedName] = useState(name);
  const inputRef = useRef(null);
  const theme = useTheme();

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isEditing]);

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleKeyDown = async (e) => {
    if (e.key === "Enter") {
      if (editedName.trim() !== name) {
        try {
          await onEdit(editedName.trim());
          setIsEditing(false);
        } catch (error) {
          setEditedName(name);
          setIsEditing(false);
        }
      } else {
        setIsEditing(false);
        setEditedName(name);
      }
    }
    if (e.key === "Escape") {
      setIsEditing(false);
      setEditedName(name);
    }
  };

  const handleBlur = async (e) => {
    const next = e.relatedTarget;

    if (
      next &&
      (next.closest("#dataset-menu") || next.closest(".MuiMenu-root"))
    ) {
      return;
    }

    if (editedName.trim() !== name) {
      try {
        await onEdit(editedName.trim());
        setIsEditing(false);
      } catch (error) {
        // If edit fails, restore original name and exit editing mode
        setEditedName(name);
        setIsEditing(false);
      }
    } else {
      setIsEditing(false);
      setEditedName(name);
    }
  };

  const handleRowClick = () => {
    if (selectable) {
      onToggleSelect?.(id);
      return;
    }
    if (isSelected || isEditing) return;
    onClick?.();
  };

  return (
    <Box
      ref={ref}
      sx={{
        width: "100%",
        height: "50px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        borderRadius: 1,
        cursor:
          selectable || !(isSelected || isEditing) ? "pointer" : "default",
        bgcolor: isSelected ? theme.palette.action.selected : "transparent",
        p: 1,
        "&:hover": {
          backgroundColor: isSelected
            ? theme.palette.action.selected
            : theme.palette.action.hover,
        },
      }}
      onClick={handleRowClick}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "flex-start",
          width: "100%",
          minWidth: 0,
          flex: 1,
        }}
      >
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "flex-start",
            width: "100%",
            minWidth: 0, // Permite que el contenido se encoja
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", minWidth: 0 }}>
            {selectable && (
              <Checkbox
                checked={checked}
                onChange={() => onToggleSelect?.(id)}
                onClick={(e) => e.stopPropagation()}
                size="small"
                sx={{ p: 0.5, mr: 1 }}
              />
            )}
            {isEditing ? (
              <TextField
                inputRef={inputRef}
                value={editedName}
                onChange={(e) => setEditedName(e.target.value)}
                onKeyDown={handleKeyDown}
                onBlur={handleBlur}
                size="small"
                variant="outlined"
                sx={{
                  width: "100%",
                  fontSize: 14,
                  "& .MuiInputBase-input": { fontSize: 14, padding: "2px 6px" },
                }}
              />
            ) : (
              <Typography variant="body1" color="text.primary" noWrap>
                {editedName}
              </Typography>
            )}
          </Box>
          <Typography
            variant="body2"
            color="text.secondary"
            noWrap
            sx={{ pl: 1 }}
          >
            {description ? description : ""}
          </Typography>
        </Box>
      </Box>
      {!selectable && (
        <ItemMenu
          itemId={id}
          onInfo={onInfo}
          onDelete={onDelete}
          onEdit={onEdit ? handleEdit : undefined}
          deleteConfirmationContent={deleteConfirmationContent}
          deleteConfirmationWarning={deleteConfirmationWarning}
        />
      )}
    </Box>
  );
});

export default ItemBox;
