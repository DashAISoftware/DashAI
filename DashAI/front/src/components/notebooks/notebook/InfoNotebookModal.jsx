import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { formatDate } from "../../../utils";
import { useTranslation } from "react-i18next";
import InfoModal from "../../shared/InfoModal";

export default function InfoNotebookModal({
  notebookData,
  datasets = [],
  open,
  onClose,
}) {
  const { t } = useTranslation(["datasets", "common"]);

  // Find the associated dataset name
  const getDatasetName = () => {
    if (!notebookData.dataset_id || !datasets.length) {
      return t("common:unknown");
    }
    const dataset = datasets.find((d) => d.id === notebookData.dataset_id);
    return dataset ? dataset.name : t("common:datasetNotFound");
  };

  // If no notebook data is provided, don't render anything
  if (!notebookData) return null;

  const rows = [
    { label: t("common:id"), value: notebookData.id },
    { label: t("datasets:label.associatedDataset"), value: getDatasetName() },
    { label: t("common:created"), value: formatDate(notebookData.created) },
    {
      label: t("common:lastModified"),
      value: formatDate(notebookData.last_modified),
    },
  ];

  const extraContent = notebookData.description &&
    notebookData.description.trim() && (
      <Box sx={{ mb: 6 }}>
        <Typography variant="subtitle2" sx={{ mb: 2 }}>
          {t("common:description")}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
          {notebookData.description}
        </Typography>
      </Box>
    );

  return (
    <InfoModal
      title={t("datasets:label.notebookInformation")}
      subtitle={notebookData.name}
      rows={rows}
      extraContent={extraContent}
      open={open}
      onClose={onClose}
    />
  );
}
