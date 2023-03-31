import React from 'react';
import { Container } from 'react-bootstrap';
import * as S from '../styles/components/NavbarStyles';

function Navbar() {
  return (
    <S.Navbar>
      <Container>
        <S.Navbar.Brand href="/app" style={{ cursor: 'pointer' }}>
          <S.Logo
            alt=""
            src="/images/logo.png"
          />
        </S.Navbar.Brand>
        <S.Navbar.Collapse>
          <S.Nav>
            <S.Nav.Link href="/app/data">Data</S.Nav.Link>
            <S.Nav.Link href="/app/experiment">Experiment</S.Nav.Link>
            <S.Nav.Link href="/app/results">Results</S.Nav.Link>
            <S.Nav.Link href="/app/play">Play</S.Nav.Link>
          </S.Nav>
        </S.Navbar.Collapse>
      </Container>
    </S.Navbar>
  );
}

export default Navbar;
