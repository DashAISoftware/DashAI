import React from "react";
import CustomLayout from "../../../components/custom/CustomLayout";
import {
  Box,
  Button,
  Card,
  Paper,
  CardHeader,
  CardContent,
  Typography,
  Tooltip,
  Grid,
} from "@mui/material";
import ArrowBackIosNewIcon from "@mui/icons-material/ArrowBackIosNew";
import VerifiedIcon from "@mui/icons-material/Verified";
import { useParams, useNavigate } from "react-router-dom";
import PluginsDetailsTab from "./PluginsDetailsTab";
import PluginTags from "./PluginsTags";
import usePluginsDetails from "../hooks/usePluginsDetails";
import { PluginStatus } from "../../../types/plugin";
import usePluginsUpdate from "../hooks/usePluginsUpdate";
import usePluginsUpgrade from "../hooks/usePluginsUpgrade";
import Markdown from "react-markdown";
import CircularProgress from "@mui/material/CircularProgress";
import { Trans, useTranslation } from "react-i18next";

/**
 * component for plugin details
 * @returns
 */
function PluginsDetails() {
  const navigate = useNavigate();
  const { category, id } = useParams();
  const [updatePluginFlag, setUpdatePluginFlag] = React.useState(true);
  const { plugin, loading, error } = usePluginsDetails({
    pluginId: id,
    updatePluginFlag,
    setUpdatePluginFlag,
  });
  const { t } = useTranslation(["plugins"]);

  const handleReturnClick = () => {
    navigate(`/app/plugins/${category}`);
  };

  const { updatePlugin, loading: installLoading } = usePluginsUpdate({
    pluginId: plugin.id,
    newStatus: [PluginStatus.INSTALLED, PluginStatus.DOWNLOADED].includes(
      plugin.status,
    )
      ? PluginStatus.REGISTERED
      : PluginStatus.INSTALLED,
    onSuccess: () => {
      setUpdatePluginFlag(true);
    },
  });

  const { upgradePlugin } = usePluginsUpgrade({
    pluginId: plugin.id,
  });

  function PluginsActions() {
    return (
      <Grid container columnGap={8}>
        {installLoading ? (
          <Button size="medium" variant="outlined" disabled>
            <CircularProgress size={24} />
          </Button>
        ) : (
          <Button
            onClick={() => updatePlugin()}
            size="medium"
            variant="outlined"
          >
            {[PluginStatus.INSTALLED, PluginStatus.DOWNLOADED].includes(
              plugin.status,
            )
              ? t("plugins:button.uninstall")
              : t("plugins:button.install")}
          </Button>
        )}
        {[PluginStatus.INSTALLED, PluginStatus.DOWNLOADED].includes(
          plugin.status,
        ) && (
          <Button
            onClick={() => upgradePlugin()}
            size="medium"
            variant="outlined"
            disabled={plugin.installed_version === plugin.lastest_version}
          >
            {t("plugins:button.upgrade")}
          </Button>
        )}
      </Grid>
    );
  }

  const tabs = [
    {
      label: t("plugins:label.details"),
      component: <Markdown>{plugin.description}</Markdown>,
    },
  ];

  return (
    <CustomLayout>
      <Button
        startIcon={<ArrowBackIosNewIcon />}
        onClick={() => {
          handleReturnClick();
        }}
      >
        {t("plugins:button.return")}
      </Button>
      {loading && (
        <Paper sx={{ p: 8, mt: 8, minHeight: "75vh" }}>
          <Grid size={{ xs: 12 }} height={"218px"}>
            <Card
              sx={{
                height: "100%",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
              }}
            >
              <CircularProgress />
            </Card>
          </Grid>
        </Paper>
      )}
      {!loading && !error && (
        <Paper sx={{ p: 8, mt: 8, minHeight: "75vh" }}>
          <Card
            sx={{
              width: "100%",

              boxShadow: "0",
              alignItems: "center",
            }}
          >
            <CardHeader
              title={
                <Box
                  component="span"
                  sx={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "8px",
                  }}
                >
                  {plugin.name.replace("dashai-", "")}
                  {plugin.verified && (
                    <Tooltip
                      title={t("plugins:label.verified")}
                      arrow
                      placement="top"
                    >
                      <VerifiedIcon color="primary" sx={{ fontSize: 22 }} />
                    </Tooltip>
                  )}
                </Box>
              }
              sx={{
                pb: 0,
                width: "100%",
              }}
              subheader={
                <Grid container direction={"column"} rowGap={8}>
                  <Grid>
                    {[PluginStatus.INSTALLED, PluginStatus.DOWNLOADED].includes(
                      plugin.status,
                    ) ? (
                      <Typography>
                        <Trans i18nKey="plugins:label.versionInstalledLatestAvailable">
                          Version installed: {plugin.installed_version} | Latest
                          version available: {plugin.lastest_version}
                        </Trans>
                      </Typography>
                    ) : (
                      <Typography>
                        {t("plugins:label.version", {
                          version: plugin.installed_version,
                        })}
                      </Typography>
                    )}
                  </Grid>
                  <Grid>
                    <PluginTags tags={plugin.tags} />
                  </Grid>
                  <Grid> {plugin.summary} </Grid>
                </Grid>
              }
              slotProps={{
                title: {
                  variant: "h4",
                  noWrap: true,
                },
              }}
            />
            <CardContent sx={{ pb: 0 }}>
              {PluginsActions(plugin.status === PluginStatus.INSTALLED)}
            </CardContent>
          </Card>
          <PluginsDetailsTab tabs={tabs}></PluginsDetailsTab>
        </Paper>
      )}
    </CustomLayout>
  );
}

export default PluginsDetails;
