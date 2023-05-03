import React from "react";
import PropTypes from "prop-types";
import {
  Grid,
  Paper,
  Typography,
  Link,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { Link as RouterLink } from "react-router-dom";

function HomeButton({ title, description, to, Icon }) {
  const theme = useTheme();
  const matches = useMediaQuery(theme.breakpoints.up("md"));

  return (
    <Paper sx={{ p: 2, m: 1 }}>
      <Link
        to={to}
        component={RouterLink}
        underline="hover"
        color="primary.contrastText"
      >
        {matches && (
          <Grid
            container
            direction="row"
            justifyContent="center"
            alignItems="center"
            sx={{ height: 128 }}
          >
            <Grid item md={3}>
              <Icon color="primary" fontSize="large" sx={{ width: "100%" }} />
            </Grid>

            <Grid item md={9} sx={{ height: "100%" }}>
              <Grid
                container
                direction="column"
                justifyContent="space-evenly"
                alignItems="stretch"
                sx={{ height: "100%" }}
              >
                <Typography variant="h5" sx={{ mb: 1 }}>
                  {title}
                </Typography>
                <Typography sx={{ mb: 2 }} variant="caption" component="p">
                  {description}
                </Typography>
              </Grid>
            </Grid>
          </Grid>
        )}
        {!matches && (
          <Grid
            container
            direction="column"
            justifyContent="center"
            alignItems="stretch"
            spacing={2}
          >
            <Grid item xs={12}>
              <Icon color="primary" fontSize="large" sx={{ width: "100%" }} />
            </Grid>

            <Grid item xs={12} sx={{ mb: 2 }}>
              <Typography variant="h5" align="center" sx={{ mb: 1 }}>
                {title}
              </Typography>
              <Typography variant="caption" component="p" align="center">
                {description}
              </Typography>
            </Grid>
          </Grid>
        )}
      </Link>
    </Paper>
  );
}

HomeButton.propTypes = {
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  to: PropTypes.string.isRequired,
  Icon: PropTypes.elementType.isRequired,
};

export default HomeButton;
