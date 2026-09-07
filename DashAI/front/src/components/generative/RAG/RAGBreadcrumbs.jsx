import React from "react";
import Breadcrumbs from "@mui/material/Breadcrumbs";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import IconButton from "@mui/material/IconButton";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import Box from "@mui/material/Box";
import { useNavigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useGenerative } from "../GenerativeContext";
import { RAG_TASK_NAME } from "../../../api/rag";

/** Root of the RAG entry point, in the canonical lowercase form. */
const RAG_ROOT = "/app/generative/rag";

/**
 * Breadcrumbs component for RAG navigation.
 *
 * @param {object}  props
 * @param {string} [props.sessionName] - Optional session name to show in breadcrumbs.
 * @returns {JSX.Element} The breadcrumbs bar with back button.
 */
function RAGBreadcrumbs({ sessionName }) {
  const { t } = useTranslation(["generative"]);
  const navigate = useNavigate();
  const location = useLocation();
  const {
    setSelectedSessionId,
    setSelectedTaskName,
    setSelectedDisplayName,
    setStepIndex,
  } = useGenerative() ?? {};

  /** Navigates to the top-level generative page, clearing all selection state. */
  const navigateToGenerative = () => {
    setSelectedSessionId?.(null);
    setSelectedTaskName?.(null);
    setSelectedDisplayName?.(null);
    setStepIndex?.(0);
    navigate("/app/generative");
  };

  /**
   * Builds an ordered breadcrumb trail based on the current URL path.
   * @returns {Array<{label: string, path: string|null, current?: boolean, isSession?: boolean}>}
   */
  const getBreadcrumbs = () => {
    // Route matching is case-insensitive, so a URL may still arrive with the
    // old /RAG/ casing; compare lowercased.
    const path = location.pathname.toLowerCase();
    if (!path.startsWith(RAG_ROOT)) return [];

    const base = [
      {
        label: t("generative:rag.breadcrumbs.generative"),
        path: "/app/generative",
      },
      {
        label: t("generative:rag.breadcrumbs.rag"),
        path: RAG_ROOT,
      },
    ];

    if (path === `${RAG_ROOT}/documents`)
      return [
        ...base,
        {
          label: t("generative:rag.breadcrumbs.documents"),
          path: null,
          current: true,
        },
      ];
    if (path === `${RAG_ROOT}/prompts`)
      return [
        ...base,
        {
          label: t("generative:rag.breadcrumbs.prompts"),
          path: null,
          current: true,
        },
      ];
    if (path === `${RAG_ROOT}/new`)
      return [
        ...base,
        {
          label: t("generative:rag.create.title"),
          path: null,
          current: true,
        },
      ];

    if (sessionName)
      return [
        ...base,
        { label: sessionName, path: null, current: true, isSession: true },
      ];

    base[1] = { ...base[1], path: null, current: true };
    return base;
  };

  const breadcrumbs = getBreadcrumbs();

  /**
   * Navigates to the given breadcrumb path, resetting selection state as needed.
   * @param {string} path - The target route path.
   */
  const handleNavigate = (path) => {
    if (!path) return;
    if (path === "/app/generative") {
      navigateToGenerative();
      return;
    }
    if (path === RAG_ROOT) {
      setSelectedSessionId?.(null);
      setSelectedTaskName?.(RAG_TASK_NAME);
      setSelectedDisplayName?.(null);
      setStepIndex?.(0);
    }
    navigate(path);
  };

  /** Navigates to the parent breadcrumb, or to the generative page if already at root. */
  const handleBack = () => {
    if (breadcrumbs.length > 1) {
      const parentBreadcrumb = breadcrumbs[breadcrumbs.length - 2];
      handleNavigate(parentBreadcrumb.path);
      return;
    }
    navigateToGenerative();
  };

  const showBackButton = breadcrumbs.length > 0;

  return (
    <Box
      sx={{
        mb: 2,
        minHeight: "24px", // Ensure consistent height
        display: "flex",
        alignItems: "center",
        gap: 1,
      }}
    >
      {showBackButton && (
        <IconButton
          onClick={handleBack}
          size="small"
          sx={{
            color: "text.secondary",
            "&:hover": {
              color: "primary.main",
              backgroundColor: "action.hover",
            },
          }}
          aria-label={t("generative:rag.breadcrumbs.goBack")}
        >
          <ArrowBackIcon fontSize="small" />
        </IconButton>
      )}
      <Breadcrumbs
        aria-label="breadcrumb"
        sx={{
          minHeight: "24px", // Ensure consistent height
          display: "flex",
          alignItems: "center",
        }}
      >
        {breadcrumbs.map((breadcrumb, index) => {
          if (breadcrumb.current) {
            return (
              <Typography key={index} color="text.primary">
                {breadcrumb.isSession ? (
                  <>
                    <em>{breadcrumb.label}</em>{" "}
                    {t("generative:rag.breadcrumbs.sessionSuffix")}
                  </>
                ) : (
                  breadcrumb.label
                )}
              </Typography>
            );
          } else {
            return (
              <Link
                key={index}
                underline="hover"
                color="inherit"
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  handleNavigate(breadcrumb.path);
                }}
                sx={{ cursor: "pointer" }}
              >
                {breadcrumb.label}
              </Link>
            );
          }
        })}
      </Breadcrumbs>
    </Box>
  );
}

export default RAGBreadcrumbs;
