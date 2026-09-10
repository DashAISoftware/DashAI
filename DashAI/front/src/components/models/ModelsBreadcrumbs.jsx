import Breadcrumbs from "@mui/material/Breadcrumbs";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import IconButton from "@mui/material/IconButton";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import Box from "@mui/material/Box";
import { useNavigate, useLocation, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useModels } from "./ModelsContext";

export default function ModelsBreadcrumbs() {
  const navigate = useNavigate();
  const location = useLocation();
  const params = useParams();
  const { t } = useTranslation(["models", "common"]);
  const { datasets, sessions, tasks, runs } = useModels();

  const rootCrumb = { label: t("common:models"), path: "/app/models" };

  const taskDisplayName = (task) =>
    task?.metadata?.display_name ||
    task?.name
      ?.replace("Task", "")
      .replace(/([A-Z])/g, " $1")
      .trim() ||
    task?.name;

  const getBreadcrumbs = () => {
    const path = location.pathname;

    if (path.startsWith("/app/models/datasets/") && params.id) {
      const dataset = datasets.find((d) => d.id === Number(params.id));
      const name = dataset?.name ?? `#${params.id}`;
      return [rootCrumb, { label: name, path: null, current: true }];
    }

    if (path.startsWith("/app/models/sessions/new/") && params.taskName) {
      const task = tasks.find((tk) => tk.name === params.taskName);
      const taskLabel = taskDisplayName(task) ?? params.taskName;
      return [
        rootCrumb,
        {
          label: taskLabel,
          path: null,
          current: true,
        },
      ];
    }

    if (path.includes("/model/") && params.id && params.runId) {
      const session = sessions.find((s) => s.id === Number(params.id));
      const sessionName = session?.name ?? `#${params.id}`;
      const run = runs.find((r) => r.id === Number(params.runId));
      const runName = run?.name ?? `#${params.runId}`;
      return [
        rootCrumb,
        {
          label: sessionName,
          path: `/app/models/sessions/${params.id}`,
          current: false,
        },
        { label: runName, path: null, current: true },
      ];
    }

    if (path.startsWith("/app/models/sessions/") && params.id) {
      const session = sessions.find((s) => s.id === Number(params.id));
      const name = session?.name ?? `#${params.id}`;
      return [rootCrumb, { label: name, path: null, current: true }];
    }

    return [{ ...rootCrumb, path: null, current: true }];
  };

  const breadcrumbs = getBreadcrumbs();

  const handleNavigate = (path) => {
    if (!path) return;
    navigate(path);
  };

  const handleBack = () => {
    if (breadcrumbs.length > 1) {
      const parent = breadcrumbs[breadcrumbs.length - 2];
      handleNavigate(parent.path);
      return;
    }
    navigate("/app/models");
  };

  const showBackButton = breadcrumbs.length > 1;

  return (
    <Box
      sx={{
        mb: 4,
        minHeight: "24px",
        display: "flex",
        alignItems: "center",
        gap: 2,
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
          aria-label="Go back"
        >
          <ArrowBackIcon fontSize="small" />
        </IconButton>
      )}
      <Breadcrumbs
        aria-label="breadcrumb"
        sx={{
          minHeight: "24px",
          display: "flex",
          alignItems: "center",
        }}
      >
        {breadcrumbs.map((crumb, index) => {
          if (crumb.current) {
            return (
              <Typography key={index} color="text.primary">
                {crumb.label}
              </Typography>
            );
          }
          return (
            <Link
              key={index}
              underline="hover"
              color="inherit"
              href="#"
              onClick={(e) => {
                e.preventDefault();
                handleNavigate(crumb.path);
              }}
              sx={{ cursor: "pointer" }}
            >
              {crumb.label}
            </Link>
          );
        })}
      </Breadcrumbs>
    </Box>
  );
}
