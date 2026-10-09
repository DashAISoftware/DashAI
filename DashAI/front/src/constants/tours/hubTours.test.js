import { tours, TOUR_KEYS } from ".";
import en from "../../utils/i18n/locales/en/hubTour.json";
import es from "../../utils/i18n/locales/es/hubTour.json";
import pt from "../../utils/i18n/locales/pt/hubTour.json";
import de from "../../utils/i18n/locales/de/hubTour.json";
import zh from "../../utils/i18n/locales/zh/hubTour.json";
import {
  isTourAtTarget,
  tourStepIndexOf,
} from "../../components/tour/tourUtils";

const locales = { en, es, pt, de, zh };
const hubTourKeys = [TOUR_KEYS.HUB, TOUR_KEYS.HUB_IMPORT];

describe.each(hubTourKeys)("%s tour", (tourKey) => {
  const { steps, config } = tours[tourKey];

  it("is registered with steps and config", () => {
    expect(steps.length).toBeGreaterThan(0);
    expect(config.continuous).toBe(true);
  });

  it("targets body or a data-tour anchor on every step", () => {
    steps.forEach((step) => {
      expect(step.target).toMatch(/^(body|\[data-tour="[\w-]+"\])$/);
    });
  });

  it.each(Object.keys(locales))("has every step text in %s", (lang) => {
    steps.forEach((step) => {
      const [ns, key] = step.content.props.i18nKey.split(":");
      expect(ns).toBe("hubTour");
      expect(locales[lang][key]).toEqual(expect.any(String));
    });
  });

  it("ends on an interactive step", () => {
    expect(steps[steps.length - 1].isInteractive).toBe(true);
  });
});

describe("tourUtils", () => {
  const steps = tours[TOUR_KEYS.HUB].steps;

  it("matches the running step by its data-tour target", () => {
    const index = tourStepIndexOf({ steps }, "hub-search");
    expect(index).toBeGreaterThan(0);
    expect(
      isTourAtTarget({ run: true, steps, stepIndex: index }, "hub-search"),
    ).toBe(true);
    expect(
      isTourAtTarget({ run: false, steps, stepIndex: index }, "hub-search"),
    ).toBe(false);
    expect(
      isTourAtTarget({ run: true, steps, stepIndex: 0 }, "hub-search"),
    ).toBe(false);
  });
});
