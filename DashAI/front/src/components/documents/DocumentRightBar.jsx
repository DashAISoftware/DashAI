import { useMemo } from "react";
import PropTypes from "prop-types";
import { Box, ButtonBase, Tooltip, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import SideBar from "../threeSectionLayout/panelContainers/SideBar";
import { KIND_ORDER, kindColor, kindLabel } from "./documentKinds";

const STRIP_HEIGHT = 320;
const MAX_BANDS = 320;

function Section({ title, hint, children }) {
  const theme = useTheme();
  return (
    <Box
      sx={{
        px: 3,
        py: 2.5,
        borderBottom: `1px solid ${theme.palette.ui.borderLight}`,
      }}
    >
      <Typography sx={{ fontSize: "13px", fontWeight: 600 }}>
        {title}
      </Typography>
      {hint && (
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ display: "block", mt: 0.5 }}
        >
          {hint}
        </Typography>
      )}
      <Box sx={{ mt: 1.5 }}>{children}</Box>
    </Box>
  );
}

function buildBands(outline) {
  const size = Math.max(1, Math.ceil(outline.length / MAX_BANDS));
  const bands = [];
  for (let start = 0; start < outline.length; start += size) {
    const slice = outline.slice(start, start + size);
    const counts = {};
    slice.forEach((item) => {
      counts[item.kind] = (counts[item.kind] || 0) + 1;
    });
    const kind = Object.keys(counts).sort((a, b) => counts[b] - counts[a])[0];
    bands.push({ first: slice[0], last: slice[slice.length - 1], kind });
  }
  return bands;
}

function ReadingOrderStrip({ outline, onJump }) {
  const { t } = useTranslation(["datasets"]);
  const theme = useTheme();
  const bands = useMemo(() => buildBands(outline), [outline]);
  return (
    <Box
      role="list"
      aria-label={t("datasets:document.readingOrder")}
      sx={{
        display: "flex",
        flexDirection: "column",
        height: Math.min(STRIP_HEIGHT, Math.max(bands.length * 10, 48)),
        width: "100%",
        borderRadius: 1,
        overflow: "hidden",
        border: `1px solid ${theme.palette.ui.border}`,
      }}
    >
      {bands.map((band) => {
        const label =
          band.first.position === band.last.position
            ? t("datasets:document.bandLabel", {
                position: band.first.position + 1,
                kind: kindLabel(t, band.kind),
              })
            : t("datasets:document.bandRangeLabel", {
                from: band.first.position + 1,
                to: band.last.position + 1,
                kind: kindLabel(t, band.kind),
              });
        return (
          <Tooltip key={band.first.position} title={label} placement="left">
            <ButtonBase
              role="listitem"
              aria-label={label}
              onClick={() => onJump(band.first.position)}
              sx={{
                flex: 1,
                minHeight: "1px",
                width: "100%",
                bgcolor: kindColor(theme, band.kind),
                opacity: 0.85,
                "&:hover": { opacity: 1 },
                "&.Mui-focusVisible": {
                  opacity: 1,
                  outline: `2px solid ${theme.palette.primary.main}`,
                  outlineOffset: "-2px",
                },
              }}
            />
          </Tooltip>
        );
      })}
    </Box>
  );
}

function OutlineList({ outline, onJump }) {
  const { t } = useTranslation(["datasets"]);
  const headings = outline.filter(
    (item) => item.kind === "title" || item.kind === "heading",
  );
  const entries =
    headings.length > 0
      ? headings.map((item) => ({
          position: item.position,
          label: item.label || kindLabel(t, item.kind),
          depth: item.kind === "title" ? 0 : Math.max((item.level ?? 1) - 1, 0),
          strong: item.kind === "title" || item.level === 1,
        }))
      : Object.values(
          outline.reduce((pages, item) => {
            if (item.page !== null && !(item.page in pages)) {
              pages[item.page] = {
                position: item.position,
                label: t("datasets:document.pageLabel", { page: item.page }),
                depth: 0,
                strong: false,
              };
            }
            return pages;
          }, {}),
        );
  if (entries.length === 0) {
    return (
      <Typography variant="caption" color="text.secondary">
        {t("datasets:document.noOutline")}
      </Typography>
    );
  }
  return (
    <Box
      component="nav"
      sx={{
        display: "flex",
        flexDirection: "column",
        maxHeight: 280,
        overflowY: "auto",
      }}
    >
      {entries.map((entry) => (
        <ButtonBase
          key={entry.position}
          onClick={() => onJump(entry.position)}
          sx={{
            justifyContent: "flex-start",
            textAlign: "left",
            py: 0.5,
            pl: 1 + entry.depth * 1.5,
            pr: 1,
            borderRadius: 1,
            "&:hover, &.Mui-focusVisible": { bgcolor: "action.hover" },
          }}
        >
          <Typography
            noWrap
            sx={{
              fontSize: "13px",
              fontWeight: entry.strong ? 600 : 400,
              color: entry.strong ? "text.primary" : "text.secondary",
            }}
          >
            {entry.label}
          </Typography>
        </ButtonBase>
      ))}
    </Box>
  );
}

function Composition({ outline }) {
  const { t } = useTranslation(["datasets"]);
  const theme = useTheme();
  const counts = outline.reduce((acc, item) => {
    acc[item.kind] = (acc[item.kind] || 0) + 1;
    return acc;
  }, {});
  const kinds = KIND_ORDER.filter((kind) => counts[kind]).concat(
    Object.keys(counts).filter((kind) => !KIND_ORDER.includes(kind)),
  );
  const max = Math.max(...kinds.map((kind) => counts[kind]), 1);
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
      {kinds.map((kind) => (
        <Box
          key={kind}
          sx={{
            display: "grid",
            gridTemplateColumns: "minmax(0, 1fr) 72px 36px",
            alignItems: "center",
            gap: 1,
          }}
        >
          <Typography sx={{ fontSize: "13px" }} noWrap>
            {kindLabel(t, kind)}
          </Typography>
          <Box
            sx={{
              height: 6,
              borderRadius: 3,
              bgcolor: theme.palette.ui.borderLight,
              overflow: "hidden",
            }}
          >
            <Box
              sx={{
                height: "100%",
                width: `${(counts[kind] / max) * 100}%`,
                bgcolor: kindColor(theme, kind),
              }}
            />
          </Box>
          <Typography
            sx={{
              fontSize: "13px",
              textAlign: "right",
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {counts[kind]}
          </Typography>
        </Box>
      ))}
    </Box>
  );
}

export default function DocumentRightBar({ outline, onJump }) {
  const { t } = useTranslation(["datasets"]);
  const theme = useTheme();
  return (
    <SideBar>
      <Box
        sx={{ display: "flex", flexDirection: "column", minHeight: 0, flex: 1 }}
      >
        <Box
          sx={{
            p: 4,
            borderBottom: `1px solid ${theme.palette.ui.border}`,
            flexShrink: 0,
            height: 64,
            display: "flex",
            alignItems: "center",
          }}
        >
          <Typography variant="h6" color="text.primary">
            {t("datasets:document.details")}
          </Typography>
        </Box>
        {outline && outline.length > 0 && (
          <Box sx={{ overflowY: "auto", flex: 1 }}>
            <Section title={t("datasets:document.outline")}>
              <OutlineList outline={outline} onJump={onJump} />
            </Section>
            <Section
              title={t("datasets:document.readingOrder")}
              hint={t("datasets:document.readingOrderHint")}
            >
              <ReadingOrderStrip outline={outline} onJump={onJump} />
            </Section>
            <Section title={t("datasets:document.composition")}>
              <Composition outline={outline} />
            </Section>
          </Box>
        )}
      </Box>
    </SideBar>
  );
}

const outlineShape = PropTypes.arrayOf(
  PropTypes.shape({
    position: PropTypes.number.isRequired,
    type: PropTypes.string,
    kind: PropTypes.string.isRequired,
    page: PropTypes.number,
    level: PropTypes.number,
    label: PropTypes.string,
  }),
);

Section.propTypes = {
  title: PropTypes.string.isRequired,
  hint: PropTypes.string,
  children: PropTypes.node,
};
ReadingOrderStrip.propTypes = {
  outline: outlineShape.isRequired,
  onJump: PropTypes.func.isRequired,
};
OutlineList.propTypes = {
  outline: outlineShape.isRequired,
  onJump: PropTypes.func.isRequired,
};
Composition.propTypes = { outline: outlineShape.isRequired };
DocumentRightBar.propTypes = {
  outline: outlineShape,
  onJump: PropTypes.func,
};
