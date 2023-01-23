import React from 'react';
import { Container } from 'react-bootstrap';
import * as S from '../styles/components/NavbarStyles';

function Navbar() {
  return (
    <S.Navbar>
      <Container>
        <S.Navbar.Brand href="/" style={{ cursor: 'pointer' }}>
          <S.Logo
            alt=""
            src="images/logo.png"
          />
        </S.Navbar.Brand>
        <S.Navbar.Collapse>
          <S.Nav>
            <S.Nav.Link href="/data">Data</S.Nav.Link>
            <S.Nav.Link href="/experiment">Experiment</S.Nav.Link>
            <S.Nav.Link href="/results">Results</S.Nav.Link>
            <S.Nav.Link href="/play">Play</S.Nav.Link>
          </S.Nav>
        </S.Navbar.Collapse>
      </Container>
    </S.Navbar>
  );
}

export default Navbar;
