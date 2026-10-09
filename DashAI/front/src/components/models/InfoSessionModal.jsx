import { useTranslation } from "react-i18next";
import InfoModal from "../shared/InfoModal";
import SessionInfoContent from "./SessionInfoContent";

export default function InfoSessionModal({
  sessionData,
  datasets = [],
  tasks = [],
  open,
  onClose,
}) {
  const { t } = useTranslation(["common"]);

  // If no session data is provided, don't render anything
  if (!sessionData) return null;

  return (
    <InfoModal
      title={t("common:sessionInformation")}
      subtitle={sessionData.name}
      rows={[]}
      extraContent={
        <SessionInfoContent
          session={sessionData}
          datasets={datasets}
          tasks={tasks}
        />
      }
      open={open}
      onClose={onClose}
    />
  );
}
