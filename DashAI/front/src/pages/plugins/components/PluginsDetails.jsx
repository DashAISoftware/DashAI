import React from "react";
import CustomLayout from "../../../components/custom/CustomLayout";
import {
  Button,
  Card,
  Paper,
  CardHeader,
  CardContent,
  Grid,
  Typography,
} from "@mui/material";
import ArrowBackIosNewIcon from "@mui/icons-material/ArrowBackIosNew";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import PluginsDetailsTab from "./PluginsDetailsTab";
import PluginTags from "./PluginsTags";

function PluginsActions(installed) {
  return installed ? (
    <Grid container columnGap={2}>
      <Button size="medium" variant="outlined">
        Check Updates
      </Button>
      <Button size="medium" variant="outlined">
        Uninstall
      </Button>
    </Grid>
  ) : (
    <Button size="medium" variant="outlined">
      Install
    </Button>
  );
}

function PluginsDetails() {
  const navigate = useNavigate();
  const { category } = useParams();
  const location = useLocation();
  const plugin = location.state && location.state.plugin;

  const handleReturnClick = () => {
    navigate(`/app/plugins/${category}`);
  };

  const tabs = [
    {
      label: "Details",
      component: (
        <Typography variant="body1" py={2}>
          {plugin.description}
        </Typography>
      ),
    },
    {
      label: "Dependencies",
      component: (
        <Typography variant="body1" py={2}>
          Dependencies
        </Typography>
      ),
    },
    {
      label: "Changelog",
      component: (
        <Typography variant="body1" py={2}>
          Changelog
        </Typography>
      ),
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
            subheader={<PluginTags tags={plugin.tags} />}
          />
          <CardContent>{PluginsActions(plugin.installed)}</CardContent>
        </Card>
        <PluginsDetailsTab tabs={tabs}></PluginsDetailsTab>
      </Paper>
    </CustomLayout>
  );
}

export default PluginsDetails;
