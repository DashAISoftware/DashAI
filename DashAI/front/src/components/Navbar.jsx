import React from 'react';
import { Container } from 'react-bootstrap';
import { useActiveTab } from '../context/TabsProvider';
import * as S from '../styles/components/NavbarStyles';

function Navbar() {
  const { setActiveTab } = useActiveTab();
  return (
    <S.Navbar>
      <Container>
        <S.Navbar.Brand onClick={() => setActiveTab('home')} style={{ cursor: 'pointer' }}>
          <S.Logo
            alt=""
            src="images/logo.png"
          />
        </S.Navbar.Brand>
        <S.Navbar.Collapse>
          <S.Nav>
            <S.Nav.Link onClick={() => setActiveTab('data')}>Data</S.Nav.Link>
            <S.Nav.Link onClick={() => setActiveTab('experiment')}>Experiment</S.Nav.Link>
            <S.Nav.Link onClick={() => setActiveTab('results')}>Results</S.Nav.Link>
            <S.Nav.Link onClick={() => setActiveTab('play')}>Play</S.Nav.Link>
          </S.Nav>
        </S.Navbar.Collapse>
      </Container>
    </S.Navbar>
  );
}

export default Navbar;
