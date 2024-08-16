import React from "react";
import CustomLayout from "../../../components/custom/CustomLayout";
import {
  Button,
  Card,
  Paper,
  CardHeader,
  CardContent,
  Typography,
  Grid,
} from "@mui/material";
import ArrowBackIosNewIcon from "@mui/icons-material/ArrowBackIosNew";
import { useParams, useNavigate } from "react-router-dom";
import PluginsDetailsTab from "./PluginsDetailsTab";
import PluginTags from "./PluginsTags";
import usePluginsDetails from "../hooks/usePluginsDetails";
import { PluginStatus } from "../../../types/plugin";
import usePluginsUpdate from "../hooks/usePluginsUpdate";
import usePluginsUpgrade from "../hooks/usePluginsUpgrade";
import Markdown from "react-markdown";

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

  const handleReturnClick = () => {
    navigate(`/app/plugins/${category}`);
  };

  const { updatePlugin } = usePluginsUpdate({
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
      <Grid container columnGap={2}>
        <Button onClick={() => updatePlugin()} size="medium" variant="outlined">
          {[PluginStatus.INSTALLED, PluginStatus.DOWNLOADED].includes(
            plugin.status,
          )
            ? "Uninstall"
            : "Install"}
        </Button>
        {[PluginStatus.INSTALLED, PluginStatus.DOWNLOADED].includes(
          plugin.status,
        ) && (
          <Button
            onClick={() => upgradePlugin()}
            size="medium"
            variant="outlined"
            disabled={plugin.version === plugin.lastest_version}
          >
            Upgrade
          </Button>
        )}
      </Grid>
    );
  }

  const tabs = [
    {
      label: "Details",
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
        Return
      </Button>
      {!loading && !error && (
        <Paper sx={{ p: 2, mt: 2, minHeight: "75vh" }}>
          <Card
            sx={{
              width: "100%",

              boxShadow: "0",
              alignItems: "center",
            }}
          >
            <CardHeader
              title={plugin.name}
              titleTypographyProps={{
                variant: "h4",
                noWrap: true,
              }}
              sx={{
                pb: 0,
                width: "100%",
              }}
              subheader={
                <Grid container direction={"column"} rowGap={1}>
                  <Grid item>
                    {[PluginStatus.INSTALLED, PluginStatus.DOWNLOADED].includes(
                      plugin.status,
                    ) ? (
                      <Typography>
                        Version installed: {plugin.version} | Latest version
                        available: {plugin.lastest_version}
                      </Typography>
                    ) : (
                      <Typography>Version: {plugin.version}</Typography>
                    )}
                  </Grid>
                  <Grid item>
                    <PluginTags tags={plugin.tags} />
                  </Grid>
                  <Grid item> {plugin.summary} </Grid>
                </Grid>
              }
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
