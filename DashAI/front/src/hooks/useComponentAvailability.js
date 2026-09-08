/**
 * Compute availability of a component from its credential requirements.
 *
 * @param {object} component - Component dict with credential fields.
 * @param {Object<string, boolean>} credentialStatuses - name -> authenticated.
 * @returns {{available: boolean, missingRequired: string[], missingOptional: string[]}}
 */
export function getComponentAvailability(component, credentialStatuses = {}) {
  const required = component?.required_credentials ?? [];
  const optional = component?.optional_credentials ?? [];

  const missingRequired = required.filter((name) => !credentialStatuses[name]);
  const missingOptional = optional.filter((name) => !credentialStatuses[name]);

  const available =
    typeof component?.credentials_satisfied === "boolean"
      ? component.credentials_satisfied
      : missingRequired.length === 0;

  return { available, missingRequired, missingOptional };
}
