import React, { useState } from "react";
import PropTypes from "prop-types";
import {
  Box,
  Paper,
  Tooltip,
  IconButton,
  Button,
  Grid,
  Typography,
} from "@mui/material";
import { AddCircleOutline as AddIcon } from "@mui/icons-material";
import VisibilityIcon from "@mui/icons-material/Visibility";
import { DataGrid } from "@mui/x-data-grid";
import { useTranslation } from "react-i18next";
import { formatDate } from "../../../utils";
import PromptViewModal from "./PromptViewModal";
import NewPromptModal from "../../../pages/generative/RAGSession/advanced/NewPromptModal";
import { getRAGPrompts } from "../../../api/rag";

/**
 * Expand default prompts (with `templates` dict) into one row per language.
 * Custom prompts (single `template`) remain as a single row.
 *
 * Each expanded row includes a `_parentPrompt` reference to the original
 * prompt object, used by the view modal to show all language versions.
 *
 * @param {Array} prompts - Raw prompt objects from the API.
 * @returns {Array} Flattened rows ready for the DataGrid.
 */
function expandPromptRows(prompts) {
  const rows = [];
  for (const prompt of prompts) {
    const templates = prompt.parameters?.templates;
    if (templates && Object.keys(templates).length > 0) {
      for (const lang of Object.keys(templates)) {
        rows.push({
          ...prompt,
          id: `${prompt.id}-${lang}`,
          _originalId: prompt.id,
          language: lang,
          _parentPrompt: prompt,
        });
      }
    } else {
      rows.push({
        ...prompt,
        language: prompt.parameters?.language || null,
        _originalId: prompt.id,
        _parentPrompt: prompt,
      });
    }
  }
  return rows;
}

/**
 * DataGrid table of available prompts with expanded multi-language rows,
 * view modal access, and "New Prompt" creation flow.
 *
 * @param {object}   props
 * @param {Array}    [props.prompts=[]] - Initial prompt list.
 * @param {boolean}  [props.loading=false] - Whether the table data is loading.
 * @param {Array}    [props.rowSelectionModel=[]] - Currently selected row IDs.
 * @param {function} [props.onRowSelectionModelChange] - Selection change callback.
 * @param {boolean}  [props.showTableTitle=false] - Whether to show the heading row.
 * @param {function} [props.setSessionData] - State setter for session data (updates prompt_id).
 * @returns {JSX.Element}
 */
export default function PromptSelectionTable({
  prompts = [],
  loading = false,
  rowSelectionModel = [],
  onRowSelectionModelChange,
  showTableTitle = false,
  setSessionData,
}) {
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedPrompt, setSelectedPrompt] = useState(null);
  const [newPromptModalOpen, setNewPromptModalOpen] = useState(false);
  const [promptRows, setPromptRows] = useState([]);
  const [rawPrompts, setRawPrompts] = useState([]);
  const { t } = useTranslation(["generative"]);

  React.useEffect(() => {
    async function fetchPrompts() {
      const initialPrompts = await getRAGPrompts();
      initialPrompts.sort((a, b) => new Date(b.created) - new Date(a.created));
      setRawPrompts(initialPrompts);
      setPromptRows(expandPromptRows(initialPrompts));
    }
    fetchPrompts();
  }, []);

  const handleViewPrompt = (row) => {
    // Always open the full parent prompt so the modal shows all languages
    setSelectedPrompt(row._parentPrompt || row);
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setSelectedPrompt(null);
  };

  const columns = React.useMemo(
    () => [
      {
        field: "id",
        headerName: t("generative:rag.promptView.table.id"),
        minWidth: 50,
        flex: 0.3,
        editable: false,
      },
      {
        field: "name",
        headerName: t("generative:rag.promptView.table.name"),
        minWidth: 140,
        flex: 1,
        editable: false,
      },
      {
        field: "class_name",
        headerName: t("generative:rag.promptView.table.type"),
        minWidth: 140,
        flex: 1,
        editable: false,
      },
      {
        field: "language",
        headerName: t("generative:rag.promptView.table.language"),
        minWidth: 100,
        flex: 0.7,
        editable: false,
        valueGetter: (value, row) => {
          if (row.language) {
            return (
              t(`generative:rag.prompt.languages.${row.language}`) ||
              row.language
            );
          }
          return "-";
        },
      },
      {
        field: "created",
        headerName: t("generative:rag.promptView.table.created"),
        minWidth: 140,
        flex: 1,
        editable: false,
        valueGetter: (value) => formatDate(value),
      },
      {
        field: "last_modified",
        headerName: t("generative:rag.promptView.table.edited"),
        minWidth: 140,
        flex: 1,
        editable: false,
        valueGetter: (value) => formatDate(value),
      },
      {
        field: "actions",
        type: "actions",
        headerName: t("generative:rag.promptView.table.actions"),
        minWidth: 80,
        flex: 0.4,
        getActions: (params) => [
          <Tooltip
            title={t("generative:rag.promptView.table.viewPrompt")}
            key="preview"
          >
            <IconButton
              size="small"
              onClick={() => handleViewPrompt(params.row)}
            >
              <VisibilityIcon fontSize="small" />
            </IconButton>
          </Tooltip>,
        ],
      },
    ],
    [t],
  );

  /**
   * Refetches prompts after creation and selects the newly created one.
   * @param {number|string} newPromptId - ID of the newly created prompt.
   */
  const handlePromptCreated = async (newPromptId) => {
    const updatedPrompts = await getRAGPrompts();
    updatedPrompts.sort((a, b) => new Date(b.created) - new Date(a.created));
    setRawPrompts(updatedPrompts);
    setPromptRows(expandPromptRows(updatedPrompts));
    if (onRowSelectionModelChange && newPromptId) {
      onRowSelectionModelChange([newPromptId]);
    }
    if (setSessionData && newPromptId) {
      setSessionData((prev) => ({
        ...prev,
        parameters: {
          ...prev.parameters,
          prompt_id: newPromptId,
        },
      }));
    }
    setNewPromptModalOpen(false);
  };

  return (
    <Paper sx={{ py: 4, px: 4 }}>
      {showTableTitle && (
        <Grid
          container
          justifyContent="space-between"
          alignItems="center"
          sx={{ mb: 4 }}
        >
          <Typography variant="h5" component="h2">
            {t("generative:rag.promptView.table.currentPrompts")}
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => setNewPromptModalOpen(true)}
            startIcon={<AddIcon />}
          >
            {t("generative:rag.promptView.table.newPrompt")}
          </Button>
        </Grid>
      )}
      {!showTableTitle && (
        <Grid
          container
          justifyContent="space-between"
          alignItems="center"
          sx={{ mb: 4 }}
        >
          <Typography variant="subtitle1" component="p" sx={{ mb: 2 }}>
            {t("generative:rag.promptView.table.choosePrompt")}
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => setNewPromptModalOpen(true)}
            startIcon={<AddIcon />}
          >
            {t("generative:rag.promptView.table.newPrompt")}
          </Button>
        </Grid>
      )}
      <Box sx={{ height: "100%" }}>
        <DataGrid
          rows={promptRows}
          columns={columns}
          hideFooter
          initialState={{
            pagination: {
              paginationModel: {
                pageSize: 5,
              },
            },
          }}
          pageSizeOptions={[5, 10, 25, 50]}
          autoHeight
          loading={loading}
        />
        <PromptViewModal
          key={selectedPrompt?.id ?? "no-prompt"}
          open={modalOpen}
          handleClose={handleCloseModal}
          prompt={selectedPrompt}
        />
        <NewPromptModal
          open={newPromptModalOpen}
          handleClose={() => setNewPromptModalOpen(false)}
          onPromptCreated={handlePromptCreated}
          existingPrompts={rawPrompts}
        />
      </Box>
    </Paper>
  );
}

PromptSelectionTable.propTypes = {
  prompts: PropTypes.array,
  loading: PropTypes.bool,
  rowSelectionModel: PropTypes.array,
  onRowSelectionModelChange: PropTypes.func,
  showTableTitle: PropTypes.bool,
  setSessionData: PropTypes.func,
};
