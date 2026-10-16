/**
 * Hides most of the local part of an email: "juan@uni.cl" -> "ju•••@uni.cl".
 */
export function maskEmail(email) {
  const [local, domain] = email.split("@");
  const hidden = "•".repeat(Math.max(local.length - 2, 3));
  return `${local.slice(0, 2)}${hidden}@${domain}`;
}
