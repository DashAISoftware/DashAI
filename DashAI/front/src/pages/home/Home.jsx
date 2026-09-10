import React from "react";
import {
  FileUpload as FileUploadIcon,
  Science as ScienceIcon,
  Extension as ExtensionIcon,
  AutoAwesome as AutoAwesomeIcon,
  DescriptionOutlined as DocsIcon,
  SchoolOutlined as TutorialsIcon,
  GitHub as GitHubIcon,
  LanguageOutlined as WebsiteIcon,
  ChatBubbleOutlineOutlined as DiscordIcon,
  CampaignOutlined as MailingListIcon,
  MailOutlineOutlined as MailIcon,
  OpenInNew as OpenInNewIcon,
} from "@mui/icons-material";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import HomeButton from "../../components/HomeButton";
import { TourProvider } from "../../components/tour/TourProvider";
import { TOUR_KEYS } from "../../constants/tours";

const SIDEBAR_LINKS = {
  resources: [
    {
      key: "documentation",
      href: "https://docs.dash-ai.com/",
      Icon: DocsIcon,
    },
    {
      key: "tutorials",
      href: "https://docs.dash-ai.com/learn/tutorials/upload-dataset",
      Icon: TutorialsIcon,
    },
    {
      key: "github",
      href: "https://github.com/DashAISoftware/DashAI",
      Icon: GitHubIcon,
    },
    { key: "website", href: "https://www.dash-ai.com", Icon: WebsiteIcon },
  ],
  community: [
    {
      key: "discord",
      href: "https://discord.gg/n9y2hEjFng",
      Icon: DiscordIcon,
    },
    {
      key: "mailingList",
      href: "https://groups.google.com/g/dashai-updates",
      Icon: MailingListIcon,
    },
    {
      key: "directMail",
      href: "mailto:dashai.nocode@gmail.com",
      Icon: MailIcon,
    },
  ],
};

function SidebarSection({ label, links, t, theme }) {
  return (
    <Box
      sx={{ pb: 4, borderBottom: `1px solid ${theme.palette.ui.borderLight}` }}
    >
      <Typography
        variant="caption"
        sx={{
          color: theme.palette.text.disabled,
          px: 4,
          py: 2,
          pb: 1,
          display: "block",
          letterSpacing: "0.12em",
          textTransform: "uppercase",
          fontFamily: '"Geist Mono", monospace',
        }}
      >
        {label}
      </Typography>
      {links.map(({ key, href, Icon }) => (
        <Box
          key={key}
          component="a"
          href={href}
          target={href.startsWith("http") ? "_blank" : undefined}
          rel="noopener noreferrer"
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 2,
            px: 4,
            py: 2,
            borderLeft: "2px solid transparent",
            textDecoration: "none",
            color: theme.palette.text.secondary,
            ...theme.typography.navItem,
            transition: "background 0.15s, color 0.15s, border-color 0.15s",
            "&:hover": {
              background: theme.palette.ui.hover,
              color: theme.palette.text.primary,
              borderLeftColor: `${theme.palette.primary.main}38`,
            },
            "&:hover .ext-icon": { opacity: 1 },
          }}
        >
          <Icon sx={{ fontSize: 13, opacity: 0.6, flexShrink: 0 }} />
          <Box component="span" sx={{ flexGrow: 1 }}>
            {t(`home:link.${key}`)}
          </Box>
          <OpenInNewIcon
            className="ext-icon"
            sx={{
              fontSize: 11,
              color: theme.palette.text.disabled,
              opacity: 0,
              transition: "opacity 0.15s",
              flexShrink: 0,
            }}
          />
        </Box>
      ))}
    </Box>
  );
}

function Home() {
  const { t } = useTranslation(["home", "common"]);
  const theme = useTheme();

  const modules = [
    {
      title: t("common:datasets"),
      description: t("home:description.datasets"),
      to: "/app/data",
      Icon: FileUploadIcon,
      accent: theme.palette.accent.amber,
      accentDim: theme.palette.accent.amberDim,
      accentBorder: theme.palette.accent.amberBorder,
      accentGlow: theme.palette.accent.amberGlow,
      tag: t("home:tag.beginner"),
      chips: [
        t("home:chip.dataImport"),
        t("home:chip.dataCleaning"),
        t("home:chip.dataTransformation"),
        t("home:chip.exploreConvertData"),
      ],
      tourAttr: "datasets-button",
    },
    {
      title: t("common:models"),
      description: t("home:description.models"),
      to: "/app/models",
      Icon: ScienceIcon,
      accent: theme.palette.accent.teal,
      accentDim: theme.palette.accent.tealDim,
      accentBorder: theme.palette.accent.tealBorder,
      accentGlow: theme.palette.accent.tealGlow,
      tag: t("home:tag.beginner"),
      chips: [
        t("home:chip.modelComparison"),
        t("home:chip.tabularClassification"),
        t("home:chip.textClassification"),
        t("home:chip.translation"),
        t("home:chip.regression"),
      ],
      tourAttr: "models-button",
    },
    {
      title: t("common:generative"),
      description: t("home:description.generative"),
      to: "/app/generative",
      Icon: AutoAwesomeIcon,
      accent: theme.palette.accent.purple,
      accentDim: theme.palette.accent.purpleDim,
      accentBorder: theme.palette.accent.purpleBorder,
      accentGlow: theme.palette.accent.purpleGlow,
      tag: t("home:tag.advanced"),
      chips: [
        t("home:chip.inference"),
        t("home:chip.parameterConfig"),
        t("home:chip.generativeTasks"),
        t("home:chip.contentGeneration"),
      ],
      tourAttr: "generative-button",
    },
    {
      title: t("common:plugins"),
      description: t("home:description.plugins"),
      to: "/app/plugins/browse",
      Icon: ExtensionIcon,
      accent: theme.palette.accent.coral,
      accentDim: theme.palette.accent.coralDim,
      accentBorder: theme.palette.accent.coralBorder,
      accentGlow: theme.palette.accent.coralGlow,
      tag: t("home:tag.advanced"),
      chips: [
        t("home:chip.installation"),
        t("home:chip.extensions"),
        t("home:chip.customIntegrations"),
      ],
      tourAttr: "plugins-button",
    },
  ];

  return (
    <TourProvider tourKey={TOUR_KEYS.HOME}>
      <Box
        sx={{
          display: "flex",
          height: "calc(100dvh - 53px)",
          minHeight: 0,
          overflow: "hidden",
        }}
      >
        {/* Sidebar */}
        <Box
          component="aside"
          sx={{
            width: 230,
            flexShrink: 0,
            borderRight: `1px solid ${theme.palette.divider}`,
            background: theme.palette.background.box,
            flexDirection: "column",
            overflow: "hidden",
            display: { xs: "none", sm: "flex" },
          }}
        >
          <SidebarSection
            label={t("home:label.resources")}
            links={SIDEBAR_LINKS.resources}
            t={t}
            theme={theme}
          />
          <SidebarSection
            label={t("home:label.community")}
            links={SIDEBAR_LINKS.community}
            t={t}
            theme={theme}
          />
          {/* Copyright pinned to bottom */}
          <Box
            sx={{
              mt: "auto",
              px: 4,
              py: 4,
              borderTop: `1px solid ${theme.palette.divider}`,
            }}
          >
            <Typography
              variant="sectionLabel"
              sx={{
                color: theme.palette.text.disabled,
                lineHeight: 1.9,
              }}
            >
              {`© ${new Date().getFullYear()} dashAI - MIT License`}
            </Typography>
          </Box>
        </Box>

        {/* Main content */}
        <Box
          sx={{
            flex: 1,
            overflow: "auto",
            display: "flex",
            flexDirection: "column",
          }}
        >
          {/* Page header */}
          <Box
            sx={{
              px: 6,
              py: 4,
              pb: 4,
              borderBottom: `1px solid ${theme.palette.divider}`,
              background: theme.palette.background.default,
            }}
          >
            <Typography variant="h3" sx={{ color: theme.palette.text.primary }}>
              {t("home:label.welcomeDashboardAI")}
            </Typography>
            <Typography
              variant="body2"
              sx={{
                color: theme.palette.text.disabled,
                fontWeight: 300,
                lineHeight: 1.65,
                mt: 1,
              }}
            >
              {t("home:label.welcomeSubtitle")}
            </Typography>
          </Box>

          {/* 2x2 module card grid */}
          <Box
            sx={{
              p: 4,
              display: { xs: "flex", lg: "grid" },
              flexDirection: { xs: "column", lg: "row" },
              gridTemplateColumns: { lg: "1fr 1fr" },
              gridTemplateRows: { lg: "1fr 1fr" },
              gap: { xs: 2, lg: 4 },
              height: { xs: "auto", lg: "70%" },
              width: { xs: "100%", lg: "80%" },
              minHeight: 0,
            }}
          >
            {modules.map((mod) => (
              <Box
                key={mod.to}
                data-tour={mod.tourAttr || undefined}
                sx={{
                  minHeight: 0,
                  height: { xs: "auto", lg: "100%" },
                  flexShrink: { xs: 0, lg: 1 },
                }}
              >
                <HomeButton
                  title={mod.title}
                  description={mod.description}
                  to={mod.to}
                  Icon={mod.Icon}
                  accent={mod.accent}
                  accentDim={mod.accentDim}
                  accentBorder={mod.accentBorder}
                  accentGlow={mod.accentGlow}
                  tag={mod.tag}
                  chips={mod.chips}
                />
              </Box>
            ))}
          </Box>
        </Box>
      </Box>
    </TourProvider>
  );
}

export default Home;
