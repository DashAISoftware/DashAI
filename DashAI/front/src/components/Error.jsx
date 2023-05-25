import React from "react";
import PropTypes from "prop-types";
import { Button, Card, CardContent, CardHeader } from "@mui/material";
import { P } from "../styles/globalComponents";

function Error({ message, reset }) {
  return (
    <>
      <Card style={{ minWidth: "32rem" }}>
        <CardHeader title="Error" />
        <CardContent>
          <p style={{ color: "#f16161" }}>Message:</p>
          <P>{message}</P>
        </CardContent>
      </Card>
      <Button variant="outlined" onClick={reset} sx={{ marginTop: "2vh" }}>
        Reset step
      </Button>
    </>
  );
}

Error.propTypes = {
  message: PropTypes.string.isRequired,
  reset: PropTypes.func,
};

Error.defaultProps = {
  reset: () => window.location.reload(false),
};

export default Error;
