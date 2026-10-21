import Breadcrumbs from "@mui/material/Breadcrumbs";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import IconButton from "@mui/material/IconButton";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import Box from "@mui/material/Box";
import { useNavigate, useLocation, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useDatasetsAndNotebooks } from "../custom/contexts/DatasetsAndNotebooksContext";

export default function DataBreadcrumbs() {
  const navigate = useNavigate();
  const location = useLocation();
  const params = useParams();
  const { t } = useTranslation(["datasets", "common"]);
  const { datasets, notebooks, documents, uploadDataloader } =
    useDatasetsAndNotebooks();

  const rootCrumb = { label: t("common:data"), path: "/app/data" };

  const getBreadcrumbs = () => {
    const path = location.pathname;

    if (path.startsWith("/app/data/new/") && params.dataloaderName) {
      const dataloaderLabel = uploadDataloader
        ? uploadDataloader.display_name || uploadDataloader.name
        : params.dataloaderName;
      return [
        rootCrumb,
        {
          label: t("datasets:label.selectDataloader"),
          path: "/app/data/new",
        },
        {
          label: dataloaderLabel,
          path: null,
          current: true,
        },
      ];
    }

    if (path.startsWith("/app/data/new")) {
      return [
        rootCrumb,
        {
          label: t("datasets:label.selectDataloader"),
          path: null,
          current: true,
        },
      ];
    }

    if (path.startsWith("/app/data/documents/") && params.id) {
      const item = documents.find((d) => d.id === Number(params.id));
      const name = item?.name ?? `#${params.id}`;
      return [rootCrumb, { label: name, path: null, current: true }];
    }

    if (path.startsWith("/app/data/notebooks/new")) {
      return [
        rootCrumb,
        {
          label: t("datasets:label.createNewNotebook"),
          path: null,
          current: true,
        },
      ];
    }

    if (path.startsWith("/app/data/datasets/") && params.id) {
      const dataset = datasets.find((d) => d.id === Number(params.id));
      const name = dataset?.name ?? `#${params.id}`;
      return [rootCrumb, { label: name, path: null, current: true }];
    }

    if (path.startsWith("/app/data/notebooks/") && params.id) {
      const notebook = notebooks.find((n) => n.id === Number(params.id));
      const name = notebook?.name ?? `#${params.id}`;
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
    navigate("/app/data");
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
