import React, { useState } from "react";
import { getDummy as getDummyRequest } from "../api/dummy";
import { useSnackbar } from "notistack";
import { Button, Typography } from "@mui/material";

function Dummy() {
  const [dummy, setDummy] = useState({});
  const { enqueueSnackbar } = useSnackbar();

  async function getDummy() {
    try {
      const dummy = await getDummyRequest();
      setDummy(dummy);
    } catch (error) {
      console.error(error);
      enqueueSnackbar("Error while trying to obtain dummy.", {
        variant: "error",
        anchorOrigin: {
          vertical: "top",
          horizontal: "right",
        },
      });
    }
  }

  return (
    <React.Fragment>
      <div>
        <Button variant="dark" onClick={getDummy}>
          Get Dummy
        </Button>
        <Typography variant="p">Add your custom React code here</Typography>
        {JSON.stringify(dummy)}
      </div>
    </React.Fragment>
  );
}

export default Dummy;
