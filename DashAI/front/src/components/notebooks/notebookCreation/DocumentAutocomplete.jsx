import PropTypes from "prop-types";
import { Box, Typography, Autocomplete, TextField, Chip } from "@mui/material";
import { useTranslation } from "react-i18next";
import { formatDate } from "../../../pages/results/constants/formatDate";
import { DOCUMENT_STATUS } from "../../../hooks/datasets/useDocuments";

function describeContent(sourceDocument, t) {
  const counts = sourceDocument.content_counts || {};
  return t("datasets:document.contentSummary", {
    text: counts.Text ?? 0,
    image: counts.Image ?? 0,
  });
}

export default function DocumentAutocomplete({
  documents,
  selectedDocument = null,
  setSelectedDocument,
  showDetails = true,
}) {
  const { t } = useTranslation(["datasets", "common"]);

  return (
    <Box width="100%">
      <Autocomplete
        options={documents}
        getOptionLabel={(option) => option.name}
        getOptionDisabled={(option) =>
          option.status !== DOCUMENT_STATUS.FINISHED
        }
        isOptionEqualToValue={(option, value) => option.id === value.id}
        value={selectedDocument}
        onChange={(event, newValue) => {
          setSelectedDocument(newValue);
        }}
        renderInput={(params) => (
          <TextField
            {...params}
            label={t("datasets:documentNotebook.selectDocument")}
            variant="outlined"
            placeholder={t("datasets:documentNotebook.typeToSearchDocuments")}
          />
        )}
        renderOption={(props, option) => {
          const { key, ...rootProps } = props;
          return (
            <Box component="li" key={key} {...rootProps}>
              <Box
                sx={{
                  display: "flex",
                  flexDirection: "column",
                  width: "100%",
                  gap: 1,
                }}
              >
                <Typography variant="body1" fontWeight="medium">
                  {option.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {option.status === DOCUMENT_STATUS.FINISHED
                    ? [
                        option.file_name,
                        `${t("common:created")}: ${formatDate(option.created)}`,
                      ]
                        .filter(Boolean)
                        .join(" | ")
                    : t("datasets:documentNotebook.documentNotReady")}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {describeContent(option, t)}
                </Typography>
              </Box>
            </Box>
          );
        }}
        sx={{ mb: 6 }}
      />

      {showDetails && selectedDocument && (
        <Box
          sx={{
            mt: 6,
            p: 6,
            border: 1,
            borderColor: "divider",
            borderRadius: 2,
          }}
        >
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
              <Typography variant="body2" fontWeight="medium">
                {t("common:name")}:
              </Typography>
              <Chip label={selectedDocument.name} size="small" />
            </Box>
            <Typography variant="body2">
              {[selectedDocument.file_name, selectedDocument.dataloader]
                .filter(Boolean)
                .join(" | ")}
            </Typography>
            <Typography variant="body2" fontWeight="medium">
              {describeContent(selectedDocument, t)}
            </Typography>
          </Box>
        </Box>
      )}
    </Box>
  );
}

DocumentAutocomplete.propTypes = {
  documents: PropTypes.arrayOf(PropTypes.object).isRequired,
  selectedDocument: PropTypes.object,
  setSelectedDocument: PropTypes.func.isRequired,
  showDetails: PropTypes.bool,
};
