import React, { useState } from 'react';
import { Container } from 'react-bootstrap';

function Home() {
  const [compatibleModels] = useState(localStorage.getItem('compatibleModels'));
  return (
    <Container>
      <p style={{ color: '#fff' }}>{ compatibleModels }</p>
    </Container>
  );
}

export default Home;
