/**
 * Static user used by the profile views until they are connected to the
 * backend. Each view keeps its own copy in state, so edits only live while
 * the view is mounted.
 */
export const MOCK_USER = {
  legalName: "Juan Soto",
  socialName: "Juan Soto",
  nickname: "juansoto",
  bio: "Estudiante interesado en computación, desarrollo de software y aprendizaje automático.",
  email: "juan.soto@example.com",
  phone: "+56 9 1234 5678",
  github: "github.com/juan-soto-demo",
  linkedin: "linkedin.com/in/juan-soto-demo",
  organization: "Universidad de Ejemplo",
  position: "Estudiante",
  globalRole: "Administrador",
  // Set to false to see the app as a regular member (hides admin views)
  isAdmin: true,
};

/**
 * Hides most of the local part of an email: "juan@uni.cl" -> "ju•••@uni.cl".
 */
export function maskEmail(email) {
  const [local, domain] = email.split("@");
  const hidden = "•".repeat(Math.max(local.length - 2, 3));
  return `${local.slice(0, 2)}${hidden}@${domain}`;
}
