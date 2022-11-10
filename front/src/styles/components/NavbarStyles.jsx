import styled from 'styled-components';
import { Navbar as BootstrapNavbar } from 'react-bootstrap';

export const Navbar = styled(BootstrapNavbar)`
  height: 10.5vh;
  color: ${(props) => props.theme.navbar.background};
  box-shadow: 0px 4px 4px rgba(0, 0, 0, 0.25);
`;

export const Logo = styled.img`
  width: 116px;
  height: 116px;
  margin-left: -3rem;
  margin-top: 1rem;
`;
