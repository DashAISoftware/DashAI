import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
} from "react";
import Joyride from "react-joyride";
import GlobalStyles from "@mui/material/GlobalStyles";
import { useTranslation } from "react-i18next";
import { useTour } from "../../hooks/useTour";
import { tours } from "../../constants/tours";
import { getTourStyles } from "./tourStyles";
import { useTheme } from "@mui/material/styles";
import { CustomTooltip } from "./CustomTooltip";
import { useTourRegistry } from "../../contexts/TourRegistryContext";

// The overlay (not the spotlight) has mix-blend-mode: hard-light.
// Everything inside the overlay (including spotlight box-shadow) blends
// with the PAGE CONTENT behind, so we must pre-invert colors differently
// depending on whether the page is dark (≈black) or light (≈white).
//
// Dark (dst≈0): hard-light(src,0) = 2*src-1 for src>0.5  → inverse: (target+1)/2
// Light (dst≈1): hard-light(src,1) = 2*src   for src≤0.5 → inverse: target/2
function hlInverse(hexColor, isDark) {
  const r = parseInt(hexColor.slice(1, 3), 16);
  const g = parseInt(hexColor.slice(3, 5), 16);
  const b = parseInt(hexColor.slice(5, 7), 16);
  if (isDark) {
    return `rgb(${Math.min(255, Math.round((255 + r) / 2))},${Math.min(255, Math.round((255 + g) / 2))},${Math.min(255, Math.round((255 + b) / 2))})`;
  }
  return `rgb(${Math.round(r / 2)},${Math.round(g / 2)},${Math.round(b / 2)})`;
}

const SpotlightHighlight = ({ isInteractive }) => (
  <GlobalStyles
    styles={(theme) => {
      const isDark = theme.palette.mode === "dark";
      const c = hlInverse(theme.palette.primary.main, isDark);
      const baseShadow = isDark
        ? `0 0 0 2px ${c}, 0 0 8px ${c}`
        : `0 0 0 2px ${c}`;
      const interactiveShadow = isDark
        ? `0 0 0 2px ${c}, 0 0 8px ${c}`
        : `0 0 0 2px ${c}, 0 0 2px ${c}`;
      const base = {
        ".react-joyride__spotlight": {
          boxShadow: `${baseShadow} !important`,
        },
      };
      if (!isInteractive) return base;
      return {
        "@keyframes tourSpotlightGlow": {
          "0%": { filter: `drop-shadow(0 0 1px ${c})` },
          "50%": {
            filter: isDark
              ? `drop-shadow(0 0 5px ${c}) drop-shadow(0 0 8px ${c})`
              : `drop-shadow(0 0 2px ${c}) drop-shadow(0 0 3px ${c})`,
          },
          "100%": { filter: `drop-shadow(0 0 1px ${c})` },
        },
        ".react-joyride__spotlight": {
          boxShadow: `${interactiveShadow} !important`,
          animation: "tourSpotlightGlow 2.2s ease-in-out infinite !important",
        },
      };
    }}
  />
);

const TourContext = createContext(null);
export const useTourContext = () => useContext(TourContext);

const NOOP_REGISTRY = {
  register: () => null,
  unregister: () => {},
  update: () => {},
};

export const TourProvider = ({
  tourKey,
  children,
  disabled: disabledProp = false,
  disabledMessage: disabledMessageProp = "Tour not available",
}) => {
  const { t } = useTranslation(["common"]);
  const theme = useTheme();
  const registry = useTourRegistry() ?? NOOP_REGISTRY;
  const regIdRef = useRef(null);

  const {
    run,
    stepIndex,
    startTour,
    stopTour,
    resetTour,
    resetAllTours,
    handleJoyrideCallback,
    goToStep,
    nextStep,
    resumeAtStep,
  } = useTour(tourKey);

  const tourData = tours[tourKey];

  const [disabled, setDisabledState] = useState(disabledProp);
  const [disabledMessage, setDisabledMessageState] =
    useState(disabledMessageProp);

  // Exposed via context so child components can update the navbar button's disabled state
  const setDisabled = useCallback((d, msg) => {
    setDisabledState(d);
    if (msg !== undefined) setDisabledMessageState(msg);
  }, []);

  // Sync if disabled/disabledMessage props change from parent
  useEffect(() => {
    setDisabledState(disabledProp);
    setDisabledMessageState(disabledMessageProp);
  }, [disabledProp, disabledMessageProp]);

  // Register with app-level registry on mount, unregister on unmount
  useEffect(() => {
    if (!tourData) return;
    regIdRef.current = registry.register(tourKey, {
      startTour,
      resetTour,
      disabled,
      disabledMessage,
    });
    return () => {
      if (regIdRef.current) {
        registry.unregister(regIdRef.current);
        regIdRef.current = null;
      }
    };
  }, []);

  // Keep registry entry in sync when disabled/message state changes
  useEffect(() => {
    if (regIdRef.current) {
      registry.update(regIdRef.current, { disabled, disabledMessage });
    }
  }, [disabled, disabledMessage, registry]);

  if (!tourData) {
    return children;
  }

  const isInteractiveStep = run && !!tourData.steps[stepIndex]?.isInteractive;

  // Internacionalized locale for tour buttons
  const locale = {
    back: t("common:back"),
    close: t("common:close"),
    last: t("common:finish"),
    next: t("common:next"),
    skip: t("common:skipTour"),
  };

  const contextValue = {
    run,
    stepIndex,
    steps: tourData.steps,
    startTour,
    stopTour,
    resetTour,
    resetAllTours,
    goToStep,
    nextStep,
    resumeAtStep,
    setDisabled,
  };

  return (
    <TourContext.Provider value={contextValue}>
      <SpotlightHighlight isInteractive={isInteractiveStep} />
      <Joyride
        steps={tourData.steps}
        run={run}
        stepIndex={stepIndex}
        callback={handleJoyrideCallback}
        continuous={tourData.config.continuous}
        showProgress={tourData.config.showProgress}
        showBackButton={tourData.config.showBackButton}
        showSkipButton={tourData.config.showSkipButton}
        disableOverlayClose={tourData.config.disableOverlayClose}
        disableCloseOnEsc={tourData.config.disableCloseOnEsc}
        locale={locale}
        disableScrollParentFix={true}
        styles={getTourStyles(theme)}
        tooltipComponent={CustomTooltip}
        scrollToFirstStep
        scrollOffset={100}
        floaterProps={{
          disableFlip: true,
          hideArrow: true,
          offset: 18,
        }}
      />
      {children}
    </TourContext.Provider>
  );
};
