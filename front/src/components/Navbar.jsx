import React from 'react';
import {
  Navbar as BootstrapNavbar,
  Container,
} from 'react-bootstrap';

function Navbar() {
  return (
    <BootstrapNavbar
      style={{
        height: '10.5vh',
        color: '#2E3037',
        boxShadow: '0px 4px 4px rgba(0, 0, 0, 0.25)',
      }}
    >
      <Container>
        <BootstrapNavbar.Brand href="#home">
          <img
            alt=""
            src="images/logo.png"
            width="116"
            height="116"
            style={{ marginLeft: '-3rem', marginTop: '1rem' }}
          />
        </BootstrapNavbar.Brand>
      </Container>
    </BootstrapNavbar>
  );
}

export default Navbar;
