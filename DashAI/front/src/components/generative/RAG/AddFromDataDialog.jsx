import { useMemo, useState } from "react";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import {
  Box,
  Button,
  ButtonBase,
  Checkbox,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Typography,
} from "@mui/material";
import { alpha, useTheme } from "@mui/material/styles";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import DocumentIcon from "@mui/icons-material/Description";
import SearchBar from "../../threeSectionLayout/SearchBar";
import { useDatasetsAndNotebooks } from "../../custom/contexts/DatasetsAndNotebooksContext";
import { DOCUMENT_STATUS } from "../../../hooks/datasets/useDocuments";
import { formatDate } from "../../../pages/results/constants/formatDate";

function statusChip(doc, attached, t) {
  if (attached)
    return {
      label: t("generative:documentsBar.alreadyAttached"),
      color: "success",
    };
  if (doc.status === DOCUMENT_STATUS.ERROR)
    return { label: t("datasets:document.statusError"), color: "error" };
  if (doc.status !== DOCUMENT_STATUS.FINISHED)
    return {
      label: t("generative:documentsBar.stillProcessing"),
      color: "info",
    };
  return null;
}

function DocumentTile({ doc, attached, checked, focused, onClick }) {
  const theme = useTheme();
  const { t } = useTranslation(["generative", "datasets"]);
  const selectable = !attached && doc.status === DOCUMENT_STATUS.FINISHED;
  const accent = theme.palette.primary.main;
  const chip = statusChip(doc, attached, t);

  return (
    <ButtonBase
      onClick={onClick}
      aria-pressed={selectable ? checked : undefined}
      title={doc.name}
      sx={{
        position: "relative",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-start",
        gap: 1,
        p: 1.5,
        pt: 2.5,
        minWidth: 0,
        height: 150,
        borderRadius: 1.5,
        border: 1,
        borderColor: checked
          ? alpha(accent, 0.6)
          : focused
            ? "divider"
            : "transparent",
        bgcolor: checked
          ? alpha(accent, 0.12)
          : focused
            ? "action.selected"
            : "transparent",
        transition: "background-color 0.15s, border-color 0.15s",
        "&:hover": {
          bgcolor: checked ? alpha(accent, 0.18) : "action.hover",
        },
        "&:hover .tile-check, &.Mui-focusVisible .tile-check": {
          opacity: 1,
        },
        "&.Mui-focusVisible": {
          outline: `2px solid ${accent}`,
          outlineOffset: "-2px",
        },
      }}
    >
      {selectable && (
        <Checkbox
          className="tile-check"
          size="small"
          checked={checked}
          tabIndex={-1}
          disableRipple
          sx={{
            position: "absolute",
            top: 2,
            left: 2,
            p: 0.5,
            opacity: checked ? 1 : 0,
            transition: "opacity 0.15s",
          }}
        />
      )}
      <Box
        sx={{
          position: "relative",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          width: 64,
          height: 64,
          color: selectable ? "text.secondary" : "text.disabled",
          opacity: selectable ? 1 : 0.6,
        }}
      >
        <DocumentIcon sx={{ fontSize: 56 }} />
      </Box>
      <Typography
        variant="body2"
        sx={{
          width: "100%",
          textAlign: "center",
          lineHeight: 1.3,
          wordBreak: "break-word",
          display: "-webkit-box",
          WebkitLineClamp: 2,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
          color: selectable ? "text.primary" : "text.secondary",
        }}
      >
        {doc.name}
      </Typography>
      {chip && (
        <Chip
          size="small"
          variant="outlined"
          color={chip.color}
          label={chip.label}
          sx={{
            height: 18,
            maxWidth: "100%",
            "& .MuiChip-label": { px: 0.75, fontSize: 10 },
          }}
        />
      )}
    </ButtonBase>
  );
}

function DetailRow({ label, value }) {
  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: "minmax(0, 2fr) minmax(0, 3fr)",
        gap: 1,
        py: 0.75,
      }}
    >
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography
        variant="caption"
        sx={{ wordBreak: "break-word", fontVariantNumeric: "tabular-nums" }}
      >
        {value}
      </Typography>
    </Box>
  );
}

function DocumentDetails({ doc, attached }) {
  const { t } = useTranslation(["generative", "datasets", "common"]);

  if (!doc) {
    return (
      <Box
        sx={{
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 1,
          px: 2,
          textAlign: "center",
          color: "text.secondary",
        }}
      >
        <InfoOutlinedIcon />
        <Typography variant="body2">
          {t("generative:documentsBar.selectToSeeDetails")}
        </Typography>
      </Box>
    );
  }

  const counts = doc.content_counts || {};
  const finished = doc.status === DOCUMENT_STATUS.FINISHED;
  const chip = statusChip(doc, attached, t);
  const rows = [
    [t("datasets:document.fileName"), doc.file_name],
    [t("datasets:document.loader"), doc.dataloader],
    [t("datasets:document.pages"), finished ? doc.total_pages : null],
    [t("datasets:document.textCount"), finished ? (counts.Text ?? 0) : null],
    [t("datasets:document.imageCount"), finished ? (counts.Image ?? 0) : null],
    [t("common:created"), doc.created && formatDate(doc.created)],
    [
      t("common:lastModified"),
      doc.last_modified && formatDate(doc.last_modified),
    ],
  ].filter(
    ([, value]) => value !== null && value !== undefined && value !== "",
  );

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 1,
          pt: 1,
        }}
      >
        <DocumentIcon sx={{ fontSize: 72, color: "text.secondary" }} />
        <Typography
          variant="subtitle1"
          sx={{ fontWeight: 600, textAlign: "center", wordBreak: "break-word" }}
        >
          {doc.name}
        </Typography>
        {chip && (
          <Chip
            size="small"
            variant="outlined"
            color={chip.color}
            label={chip.label}
          />
        )}
      </Box>
      <Divider />
      <Box>
        <Typography
          variant="overline"
          color="text.secondary"
          sx={{ display: "block", lineHeight: 2 }}
        >
          {t("datasets:document.details")}
        </Typography>
        {rows.map(([label, value]) => (
          <DetailRow key={label} label={label} value={value} />
        ))}
      </Box>
    </Box>
  );
}

export default function AddFromDataDialog({
  open,
  onClose,
  attachedIds,
  onConfirm,
}) {
  const { t } = useTranslation(["generative", "datasets", "common"]);
  const { documents = [] } = useDatasetsAndNotebooks();
  const [selected, setSelected] = useState([]);
  const [focusedId, setFocusedId] = useState(null);
  const [query, setQuery] = useState("");

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return documents.filter(
      (doc) => !needle || doc.name.toLowerCase().includes(needle),
    );
  }, [documents, query]);

  const focusedDoc = documents.find((doc) => doc.id === focusedId) ?? null;

  const handleTileClick = (doc) => {
    setFocusedId(doc.id);
    if (attachedIds.has(doc.id) || doc.status !== DOCUMENT_STATUS.FINISHED)
      return;
    setSelected((previous) =>
      previous.includes(doc.id)
        ? previous.filter((value) => value !== doc.id)
        : [...previous, doc.id],
    );
  };

  const handleClose = () => {
    setSelected([]);
    setFocusedId(null);
    setQuery("");
    onClose();
  };

  const handleConfirm = async () => {
    const ids = selected;
    handleClose();
    await onConfirm(ids);
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="lg"
      fullWidth
      slotProps={{ paper: { sx: { height: "80vh" } } }}
    >
      <DialogTitle>{t("generative:documentsBar.addFromDataTitle")}</DialogTitle>
      <DialogContent
        dividers
        sx={{ p: 0, display: "flex", minHeight: 0, overflow: "hidden" }}
      >
        <Box
          sx={{
            flex: 3,
            minWidth: 0,
            display: "flex",
            flexDirection: "column",
          }}
        >
          <Box sx={{ p: 2, pb: 1.5 }}>
            <SearchBar
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onClear={() => setQuery("")}
              placeholder={t("generative:documentsBar.searchPlaceholder")}
            />
          </Box>
          <Box sx={{ flex: 1, minHeight: 0, overflowY: "auto", px: 2, pb: 2 }}>
            {visible.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                {documents.length === 0
                  ? t("generative:documentsBar.noLibraryDocuments")
                  : t("generative:documentsBar.noDocumentsFound")}
              </Typography>
            ) : (
              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(132px, 1fr))",
                  gap: 1,
                }}
              >
                {visible.map((doc) => (
                  <DocumentTile
                    key={doc.id}
                    doc={doc}
                    attached={attachedIds.has(doc.id)}
                    checked={selected.includes(doc.id)}
                    focused={focusedId === doc.id}
                    onClick={() => handleTileClick(doc)}
                  />
                ))}
              </Box>
            )}
          </Box>
        </Box>
        <Box
          sx={{
            flex: 1,
            minWidth: 0,
            borderLeft: 1,
            borderColor: "divider",
            overflowY: "auto",
            p: 2,
          }}
        >
          <DocumentDetails
            doc={focusedDoc}
            attached={focusedDoc ? attachedIds.has(focusedDoc.id) : false}
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>{t("common:cancel")}</Button>
        <Button
          variant="contained"
          disabled={selected.length === 0}
          onClick={handleConfirm}
        >
          {t("generative:documentsBar.addSelected", {
            count: selected.length,
          })}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

DocumentTile.propTypes = {
  doc: PropTypes.object.isRequired,
  attached: PropTypes.bool.isRequired,
  checked: PropTypes.bool.isRequired,
  focused: PropTypes.bool.isRequired,
  onClick: PropTypes.func.isRequired,
};

DetailRow.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.node.isRequired,
};

DocumentDetails.propTypes = {
  doc: PropTypes.object,
  attached: PropTypes.bool.isRequired,
};

AddFromDataDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  attachedIds: PropTypes.instanceOf(Set).isRequired,
  onConfirm: PropTypes.func.isRequired,
};
