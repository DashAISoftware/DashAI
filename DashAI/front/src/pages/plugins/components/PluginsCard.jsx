import React from "react";
import {
  Button,
  Card,
  CardActionArea,
  CardActions,
  CardHeader,
  Typography,
  Grid,
} from "@mui/material";
import PropTypes from "prop-types";
import { useNavigate, useParams } from "react-router-dom";
import PluginTags from "./PluginsTags";
import usePluginsUpdate from "../hooks/usePluginsUpdate";
import { PluginStatus } from "../../../types/plugin";

/**
 * Component for plugin card modal
 * @param {object} plugin Plugin to display
 * @param {boolean} cardView boolean true if uses cardView display and false if uses list display
 * @param {boolean} refreshPluginsFlag
 * @param {function} setRefreshPluginsFlag
 * @returns
 */
function PluginsCard({
  plugin,
  cardView,
  refreshPluginsFlag,
  setRefreshPluginsFlag,
}) {
  const navigate = useNavigate();
  const { category } = useParams();

  const handlePluginClick = () => {
    navigate(`/app/plugins/${category}/details/${plugin.id}`);
  };

  const { updatePlugin } = usePluginsUpdate({
    pluginId: plugin.id,
    newStatus: PluginStatus.INSTALLED,
    onSuccess: () => {
      setRefreshPluginsFlag(true);
    },
  });

  return (
    <Card
      sx={{
        height: "100%",
        display: "flex",
        flexDirection: cardView ? "column" : "row",
        alignItems: cardView ? "stretch" : "center",
      }}
    >
      <CardActionArea
        sx={{
          height: "-webkit-fill-available",
          display: "flex",
          flexDirection: "column",
          justifyContent: "flex-start",
        }}
        onClick={handlePluginClick}
      >
        <CardHeader
          title={
            <Grid
              container
              display={"flex"}
              flexDirection={cardView ? "column" : "row"}
              alignItems={cardView ? "flex-start" : "center"}
              columnGap={1}
              spacing={1}
            >
              <Grid
                item
                sx={{
                  width: cardView ? "100%" : "auto",
                  textOverflow: "ellipsis",
                  overflow: "hidden",
                }}
              >
                <Typography noWrap variant="h6">
                  {plugin.name.replace("dashai-", "")}
                </Typography>
              </Grid>
              <Grid item>
                <Typography variant="body2">
                  Version: {plugin.version}
                </Typography>
              </Grid>
              <Grid item>
                <PluginTags tags={plugin.tags} />
              </Grid>
            </Grid>
          }
          subheader={
            <Typography
              pt={1}
              align="justify"
              variant="body2"
              sx={{
                overflow: "hidden",
                textOverflow: "ellipsis",
                display: "-webkit-box",
                WebkitLineClamp: cardView ? "3" : "1",
                WebkitBoxOrient: "vertical",
              }}
            >
              {plugin.summary}
            </Typography>
          }
          sx={{
            width: "100%",
            "& .MuiCardHeader-content": {
              overflow: "hidden",
              textOverflow: "ellipsis",
            },
          }}
        />
      </CardActionArea>

      {plugin.status === PluginStatus.REGISTERED && (
        <CardActions
          sx={{
            justifyContent: cardView ? "flex-end" : "center",
          }}
        >
          <Button
            onClick={() => updatePlugin()}
            size="medium"
            variant="outlined"
          >
            Install
          </Button>
        </CardActions>
      )}
    </Card>
  );
}

PluginsCard.propTypes = {
  plugin: PropTypes.shape({
    id: PropTypes.number.isRequired,
    name: PropTypes.string.isRequired,
    author: PropTypes.string.isRequired,
    tags: PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.number.isRequired,
        name: PropTypes.string.isRequired,
        plugin_id: PropTypes.number.isRequired,
      }),
    ),
    status: PropTypes.oneOf([0, 1, 2, 3]).isRequired,
    summary: PropTypes.string.isRequired,
    description: PropTypes.string.isRequired,
    description_content_type: PropTypes.string.isRequired,
    created: PropTypes.string.isRequired,
    last_modified: PropTypes.string.isRequired,
  }).isRequired,
  cardView: PropTypes.bool.isRequired,
  refreshPluginsFlag: PropTypes.bool.isRequired,
  setRefreshPluginsFlag: PropTypes.func.isRequired,
};

export default PluginsCard;
