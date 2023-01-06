import React from 'react';
import { Container } from 'react-bootstrap';
import * as S from '../styles/components/NavbarStyles';

function Navbar() {
  return (
    <S.Navbar>
      <Container>
        <S.Navbar.Brand href="#home">
          <S.Logo
            alt=""
            src="images/logo.png"
          />
        </S.Navbar.Brand>
      </Container>
    </S.Navbar>
  );
}

export default Navbar;
