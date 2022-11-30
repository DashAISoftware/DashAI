import React from 'react';
import PropTypes from 'prop-types';
import { Card } from 'react-bootstrap';
import {
  P,
  StyledCard,
  StyledButton,
} from '../styles/globalComponents';

function Error({ message, reset }) {
  return (
    <>
      <StyledCard style={{ width: '32rem' }}>
        <Card.Header>
          <Card.Title>
            Error
          </Card.Title>
        </Card.Header>
        <Card.Body>
          <p style={{ color: '#f16161' }}>
            Message:
          </p>
          <P>
            {message}
          </P>
        </Card.Body>
      </StyledCard>
      <br />
      <StyledButton
        type="button"
        onClick={reset}
        style={{ marginRight: '35rem' }}
      >
        Reset step
      </StyledButton>
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
