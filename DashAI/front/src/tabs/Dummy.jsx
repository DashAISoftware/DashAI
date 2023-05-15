import React, { useState } from "react";
import { getDummy as getDummyRequest } from "../api/dummy";
import { StyledButton, P } from "../styles/globalComponents";
import { useSnackbar } from "notistack";

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
        <StyledButton variant="dark" onClick={getDummy}>
          Get Dummy
        </StyledButton>
        <P>Add your custom React code here</P>
        {JSON.stringify(dummy)}
      </div>
    </React.Fragment>
  );
}

export default Dummy;
