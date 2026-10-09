import { artifactToCsv } from "./downloadArtifact";

test("artifactToCsv builds header and rows, quoting cells with commas", () => {
  const csv = artifactToCsv({
    columns: ["feature", "value"],
    rows: [
      ["age", 42],
      ["city, state", "NY, US"],
    ],
  });
  expect(csv).toBe('feature,value\r\nage,42\r\n"city, state","NY, US"');
});

test("artifactToCsv renders null as empty cell", () => {
  const csv = artifactToCsv({ columns: ["a", "b"], rows: [[null, 1]] });
  expect(csv).toBe("a,b\r\n,1");
});
