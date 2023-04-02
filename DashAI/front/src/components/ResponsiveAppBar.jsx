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
const pages = [
  { name: "Data", to: "/data", disabled: false },
  { name: "Experiments", to: "/experiments", disabled: false },
  { name: "Results", to: "/results", disabled: false },
  { name: "Play", to: "/play", disabled: true },
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
    <AppBar
      position="static"
      enableColorOnDark
      sx={{ background: "#2e3037", text: "#fff" }}
    >
      <Container maxWidth="xl">
        <Toolbar>
          <IconButton component={RouterLink} to="/" sx={{ p: 0, mr: 3, my: 1 }}>
            <Avatar
              alt="DashAI Logo"
              src="/images/logo.png"
              variant="square"
              sx={{ width: 120 }}
            />
          </IconButton>

          {/* Render on xs screens */}
          <Box sx={{ flexGrow: 1, display: { xs: "flex", sm: "none" } }}>
            <IconButton
              size="large"
              aria-label="account of current user"
              aria-controls="menu-appbar"
              aria-haspopup="true"
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
            {pages.map((page) => (
              <Button
                component={RouterLink}
                to={page.to}
                disableElevation
                key={page.name}
                onClick={handleCloseNavMenu}
                sx={{ my: 2, display: "block" }}
                size="large"
                disabled={page.disabled}
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
