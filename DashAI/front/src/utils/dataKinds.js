export function loadsDataKind(component, kind) {
  const kinds = component?.metadata?.data_kinds;
  if (!Array.isArray(kinds) || kinds.length === 0) {
    return kind === "dataset";
  }
  return kinds.includes(kind);
}
