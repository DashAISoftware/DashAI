import { React } from "react";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";

import ArtifactViewer from "../shared/ArtifactViewer";

const FALLBACK_LANG = "en";

/**
 * Shows the narrative the backend generated for one explainer artifact, in
 * whichever language is currently active. `story` carries every supported
 * language at once (`{"en": ..., "es": ..., ...}`), so switching the app's
 * language selector re-renders this with the matching text already in hand
 * — no refetch. Rendered as a plain "text" artifact through ArtifactViewer,
 * so it is the exact same box as any other artifact (border, background,
 * download button), not a lookalike.
 */
export default function StoryBox({ story, groupTitle = null }) {
  const { t, i18n } = useTranslation(["explainers"]);

  if (!story) return null;

  const lang = i18n.language?.split("-")[0];
  const text = story[lang] ?? story[FALLBACK_LANG];
  if (!text) return null;

  const label = groupTitle
    ? `${t("explainers:label.storyTitle")} — ${groupTitle}`
    : t("explainers:label.storyTitle");

  return (
    <ArtifactViewer artifact={{ type: "text", title: label, payload: text }} />
  );
}

StoryBox.propTypes = {
  story: PropTypes.objectOf(PropTypes.string),
  groupTitle: PropTypes.string,
};
