import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import SelectOptionMenu from "../threeSectionLayout/SelectOptionMenu";
import { useTourContext } from "../tour/TourProvider";
import { useGenerative } from "./GenerativeContext";
import {
  STANDALONE_ENTRY_POINTS,
  isStandaloneTask,
  standaloneRouteFor,
} from "./standaloneEntryPoints";

const CREATE_SESSION = "new_session";

/**
 * Landing of the Generative module.
 *
 * Offers "create a session" alongside every task that owns a dedicated entry
 * point, so those tasks sit at the same level rather than hidden inside the
 * session-creation flow. The option list is built from the tasks the backend
 * reports, including their names and descriptions.
 *
 * @returns {JSX.Element} The module landing menu.
 */
export default function CreateSessionLanding() {
  const navigate = useNavigate();
  const { t } = useTranslation(["generative", "common"]);
  const tourContext = useTourContext();
  const { tasks } = useGenerative();

  const options = useMemo(() => {
    const standalone = (tasks ?? [])
      .filter(isStandaloneTask)
      .filter((task) => STANDALONE_ENTRY_POINTS[task.name])
      .map((task) => ({
        name: task.name,
        display_name: task.display_name || task.name,
        description: task.description || "",
        Icon: STANDALONE_ENTRY_POINTS[task.name].Icon,
      }));

    return [
      {
        name: CREATE_SESSION,
        display_name: t("generative:label.createNewSession"),
        description: t("generative:label.createNewSessionDescription"),
        Icon: AutoAwesomeIcon,
      },
      ...standalone,
    ];
  }, [tasks, t]);

  /**
   * Navigate to the chosen entry point.
   * @param {string} name - The option name (a task name, or "new_session").
   */
  const handleOption = (name) => {
    if (tourContext?.run) {
      tourContext.nextStep();
    }
    navigate(standaloneRouteFor(name) ?? "/app/generative/sessions/new");
  };

  return (
    <SelectOptionMenu
      goToNextStep={handleOption}
      title={t("generative:label.generativeModule")}
      subtitle={t("generative:label.createNewSessionDescription")}
      options={options}
      searchBar={false}
      dataTour="create-session-landing"
      dataTourTarget={CREATE_SESSION}
    />
  );
}
