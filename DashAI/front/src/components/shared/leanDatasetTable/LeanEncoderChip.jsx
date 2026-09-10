import { memo, useState } from "react";
import PropTypes from "prop-types";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";

import { updateColumnEncoder } from "../../../api/datasets";
import EncoderChipBase from "./EncoderChipBase";

function useEncoderLabel() {
  const { t } = useTranslation(["common"]);
  return (enc) => {
    if (enc === "one_hot") return t("common:encoderOneHot");
    if (enc === "label") return t("common:encoderLabel");
    return enc ?? "-";
  };
}

const LeanEncoderChip = memo(function LeanEncoderChip({
  columnName,
  encoder,
  datasetId,
  onChanged,
}) {
  const [pending, setPending] = useState(false);
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["datasets"]);
  const encoderLabel = useEncoderLabel();

  const handleSelect = async (next) => {
    if (next === encoder) return;
    setPending(true);
    try {
      await updateColumnEncoder(datasetId, columnName, next);
      if (onChanged) onChanged();
    } catch (e) {
      enqueueSnackbar(
        t("datasets:table.failedToUpdateEncoder", { columnName }),
        { variant: "error" },
      );
    } finally {
      setPending(false);
    }
  };

  return (
    <EncoderChipBase
      encoder={pending ? "..." : encoder}
      onSelect={handleSelect}
      disabled={pending}
      encoderLabel={encoderLabel}
    />
  );
});

LeanEncoderChip.propTypes = {
  columnName: PropTypes.string.isRequired,
  encoder: PropTypes.string,
  datasetId: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  onChanged: PropTypes.func,
};

export default LeanEncoderChip;
