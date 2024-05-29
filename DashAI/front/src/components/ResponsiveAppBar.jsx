import * as React from "react";
import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Toolbar from "@mui/material/Toolbar";
import IconButton from "@mui/material/IconButton";
import Typography from "@mui/material/Typography";
import Menu from "@mui/material/Menu";
import MenuIcon from "@mui/icons-material/Menu";
import Container from "@mui/material/Container";
import Avatar from "@mui/material/Avatar";
import Button from "@mui/material/Button";
import MenuItem from "@mui/material/MenuItem";
import { Link as RouterLink, useLocation } from "react-router-dom";
import { useTheme } from "@mui/material/styles";
import HomeIcon from "@mui/icons-material/HomeOutlined";

const pages = [
  { name: "Datasets", to: "/app/data", disabled: false },
  { name: "Experiments", to: "/app/experiments", disabled: false },
  { name: "Explainability", to: "/app/explainers", disabled: false },
  { name: "Play", to: "/app/play", disabled: true },
];

function ResponsiveAppBar() {
  const theme = useTheme();
  const location = useLocation();

  const [anchorElNav, setAnchorElNav] = React.useState(null);

  const handleOpenNavMenu = (event) => {
    setAnchorElNav(event.currentTarget);
  };

  const handleCloseNavMenu = () => {
    setAnchorElNav(null);
  };

  return (
    <AppBar position="sticky" enableColorOnDark sx={{ background: "#212121" }}>
      <Container maxWidth="xl">
        <Toolbar>
          <Avatar
            alt="DashAI Logo"
            src="/images/logo.png"
            variant="square"
            sx={{ width: 120, p: 0, mr: 3, my: 1, mt: 2 }}
          />

          {/* Render on xs screens */}
          <Box sx={{ flexGrow: 1, display: { xs: "flex", sm: "none" } }}>
            <IconButton
              size="large"
              onClick={handleOpenNavMenu}
              color="inherit"
            >
              <MenuIcon />
            </IconButton>
            <Menu
              id="menu-appbar"
              anchorEl={anchorElNav}
              anchorOrigin={{
                vertical: "bottom",
                horizontal: "left",
              }}
              autoFocus
              keepMounted
              transformOrigin={{
                vertical: "top",
                horizontal: "left",
              }}
              open={Boolean(anchorElNav)}
              onClose={handleCloseNavMenu}
              sx={{
                display: { xs: "block", md: "none" },
                backgroundColor: theme.palette.background,
              }}
            >
              {pages.map((page) => (
                <MenuItem
                  key={page.name}
                  onClick={handleCloseNavMenu}
                  component={RouterLink}
                  to={page.to}
                  selected={page.to === location.pathname}
                >
                  <Typography textAlign="center">{page.name}</Typography>
                </MenuItem>
              ))}
            </Menu>
          </Box>

          {/* Render on sm to xl screens */}
          <Box sx={{ flexGrow: 1, display: { xs: "none", sm: "flex" } }}>
            <IconButton
              aria-label="delete"
              component={RouterLink}
              to="/app"
              disableRipple
              sx={{ mr: 2 }}
            >
              <HomeIcon />
            </IconButton>
            {pages.map((page) => (
              <Button
                component={RouterLink}
                to={page.to}
                key={page.name}
                onClick={handleCloseNavMenu}
                sx={{ my: 2, display: "block" }}
                size="large"
                disabled={page.disabled}
                disableRipple
                color={page.to === location.pathname ? "primary" : "inherit"}
              >
                {page.name}
              </Button>
            ))}
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}
export default ResponsiveAppBar;
