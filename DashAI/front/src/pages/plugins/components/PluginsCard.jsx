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

function PluginsCard({ plugin, cardView }) {
  const navigate = useNavigate();
  const { category } = useParams();

  const handlePluginClick = () => {
    navigate(`/app/plugins/${category}/details/${plugin.id}`, {
      state: { plugin },
    });
  };

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
                  {plugin.name}
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
              {plugin.description}
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

      {!plugin.installed && (
        <CardActions
          sx={{
            justifyContent: cardView ? "flex-end" : "center",
          }}
        >
          <Button size="medium" variant="outlined">
            Install
          </Button>
        </CardActions>
      )}
    </Card>
  );
}

PluginsCard.propTypes = {
  plugin: PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    description: PropTypes.string.isRequired,
    tags: PropTypes.arrayOf(PropTypes.string).isRequired,
    installed: PropTypes.bool.isRequired,
  }),
  cardView: PropTypes.bool,
};

export default PluginsCard;
