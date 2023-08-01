import React from "react";
import PropTypes from "prop-types";
import Container from "@mui/material/Container";

/**
 * This component renders a layout that allows you to choose whether to use the Container component or not.
 * @param {React.ReactNode} children The content to be rendered within the layout
 * @param {boolean} disableContainer If true, the Container component will be deactivated and the content will be rendered without it.
 */
function CustomLayout({ children, disableContainer }) {
  if (disableContainer) {
    return <React.Fragment>{children}</React.Fragment>;
  }
  return (
    <Container maxWidth="xl" sx={{ my: 5, mb: 4 }}>
      {children}
    </Container>
  );
}

CustomLayout.propTypes = {
  children: PropTypes.node.isRequired,
  disableContainer: PropTypes.bool,
};

CustomLayout.defaultProps = {
  disableContainer: false,
};

export default CustomLayout;
