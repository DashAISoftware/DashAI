import PropTypes from "prop-types";
import {
  Box,
  Divider,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { normalizeUrl } from "../../utils/urlUtils";

const HIDDEN_KINDS = new Set(["page_header", "page_footer"]);

const HEADING_VARIANTS = {
  1: "h4",
  2: "h5",
  3: "h6",
  4: "subtitle1",
  5: "subtitle2",
  6: "subtitle2",
};

const textSx = { whiteSpace: "pre-wrap", overflowWrap: "anywhere" };

function TitleBlock({ item }) {
  return (
    <Typography variant="h3" component="h1" sx={textSx}>
      {item.content}
    </Typography>
  );
}

function HeadingBlock({ item }) {
  const level = item.attrs?.level ?? 3;
  return (
    <Typography
      variant={HEADING_VARIANTS[level] ?? "h6"}
      component={`h${Math.min(Math.max(level, 1), 6)}`}
      sx={{ ...textSx, fontWeight: 600 }}
    >
      {item.content}
    </Typography>
  );
}

function ParagraphBlock({ item }) {
  return (
    <Typography variant="body1" sx={textSx}>
      {item.content}
    </Typography>
  );
}

function QuoteBlock({ item }) {
  return (
    <Box
      component="blockquote"
      sx={{
        m: 0,
        pl: 2,
        borderLeft: 4,
        borderColor: "divider",
        color: "text.secondary",
        fontStyle: "italic",
      }}
    >
      <Typography variant="body1" sx={textSx}>
        {item.content}
      </Typography>
    </Box>
  );
}

function CaptionBlock({ item }) {
  return (
    <Typography variant="caption" color="text.secondary" sx={textSx}>
      {item.content}
    </Typography>
  );
}

function CodeBlock({ item }) {
  return (
    <Box
      component="pre"
      sx={{
        m: 0,
        p: 2,
        overflow: "auto",
        borderRadius: 1,
        bgcolor: "action.hover",
        fontFamily: "monospace",
        fontSize: "0.85rem",
      }}
    >
      <code>{item.content}</code>
    </Box>
  );
}

function TableBlock({ item }) {
  const rows = Array.isArray(item.attrs?.rows) ? item.attrs.rows : [];
  if (rows.length === 0) return <ParagraphBlock item={item} />;
  const hasHeader = Boolean(item.attrs?.header);
  const headRow = hasHeader ? rows[0] : null;
  const bodyRows = hasHeader ? rows.slice(1) : rows;
  return (
    <TableContainer sx={{ border: 1, borderColor: "divider", borderRadius: 1 }}>
      <Table size="small">
        {headRow && (
          <TableHead>
            <TableRow>
              {headRow.map((cell, index) => (
                <TableCell key={index} sx={{ fontWeight: 600 }}>
                  {cell}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
        )}
        <TableBody>
          {bodyRows.map((row, rowIndex) => (
            <TableRow key={rowIndex}>
              {row.map((cell, cellIndex) => (
                <TableCell key={cellIndex}>{cell}</TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

function ImageBlock({ item }) {
  const { t } = useTranslation(["datasets"]);
  return (
    <Box
      component="img"
      src={normalizeUrl(item.url)}
      alt={
        item.attrs?.alt ||
        t("datasets:document.imageAlt", { position: item.position + 1 })
      }
      sx={{ maxWidth: "100%", display: "block", mx: "auto" }}
    />
  );
}

const RENDERERS = {
  title: TitleBlock,
  heading: HeadingBlock,
  paragraph: ParagraphBlock,
  quote: QuoteBlock,
  caption: CaptionBlock,
  code: CodeBlock,
  table: TableBlock,
  image: ImageBlock,
};

function ListGroup({ items }) {
  const ordered = Boolean(items[0].attrs?.ordered);
  return (
    <Box component={ordered ? "ol" : "ul"} sx={{ m: 0, pl: 4 }}>
      {items.map((item) => (
        <Box
          component="li"
          key={item.position}
          sx={{ ml: (item.attrs?.depth ?? 0) * 3 }}
        >
          <Typography variant="body1" sx={textSx}>
            {item.content}
          </Typography>
        </Box>
      ))}
    </Box>
  );
}

function groupBlocks(items) {
  const blocks = [];
  items
    .filter((item) => !HIDDEN_KINDS.has(item.kind))
    .forEach((item) => {
      const last = blocks[blocks.length - 1];
      if (
        item.kind === "list_item" &&
        last?.kind === "list" &&
        last.page === item.page
      ) {
        last.items.push(item);
      } else if (item.kind === "list_item") {
        blocks.push({ kind: "list", page: item.page, items: [item] });
      } else {
        blocks.push({ kind: "item", page: item.page, item });
      }
    });
  return blocks;
}

export default function DocumentRenderer({ items }) {
  const { t } = useTranslation(["datasets"]);
  let previousPage = null;
  return (
    <Stack spacing={2}>
      {groupBlocks(items).map((block) => {
        const key =
          block.kind === "list" ? block.items[0].position : block.item.position;
        const showPage =
          block.page !== null &&
          block.page !== undefined &&
          block.page !== previousPage;
        previousPage = block.page ?? previousPage;
        const Renderer =
          block.kind === "item"
            ? (RENDERERS[block.item.kind] ?? ParagraphBlock)
            : null;
        return (
          <Box key={key}>
            {showPage && (
              <Divider sx={{ my: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  {t("datasets:document.pageLabel", { page: block.page })}
                </Typography>
              </Divider>
            )}
            {block.kind === "list" ? (
              <ListGroup items={block.items} />
            ) : (
              <Renderer item={block.item} />
            )}
          </Box>
        );
      })}
    </Stack>
  );
}

const itemShape = PropTypes.shape({
  type: PropTypes.string,
  kind: PropTypes.string,
  attrs: PropTypes.object,
  position: PropTypes.number,
  page: PropTypes.number,
  content: PropTypes.string,
  url: PropTypes.string,
});

TitleBlock.propTypes = { item: itemShape.isRequired };
HeadingBlock.propTypes = { item: itemShape.isRequired };
ParagraphBlock.propTypes = { item: itemShape.isRequired };
QuoteBlock.propTypes = { item: itemShape.isRequired };
CaptionBlock.propTypes = { item: itemShape.isRequired };
CodeBlock.propTypes = { item: itemShape.isRequired };
TableBlock.propTypes = { item: itemShape.isRequired };
ImageBlock.propTypes = { item: itemShape.isRequired };
ListGroup.propTypes = { items: PropTypes.arrayOf(itemShape).isRequired };
DocumentRenderer.propTypes = { items: PropTypes.arrayOf(itemShape).isRequired };
