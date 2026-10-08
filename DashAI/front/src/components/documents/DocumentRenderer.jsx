import PropTypes from "prop-types";
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import { normalizeUrl } from "../../utils/urlUtils";
import { HIDDEN_KINDS, kindColor, kindLabel } from "./documentKinds";

const READING_WIDTH = "68ch";
const SHEET_WIDTH = 880;
const PAGE_ANCHOR_OFFSET = "88px";

const HEADING_STYLES = {
  1: { fontSize: "24px", fontWeight: 650, lineHeight: 1.3 },
  2: { fontSize: "20px", fontWeight: 600, lineHeight: 1.35 },
  3: { fontSize: "18px", fontWeight: 600, lineHeight: 1.4 },
  4: { fontSize: "16px", fontWeight: 600, lineHeight: 1.5 },
  5: { fontSize: "16px", fontWeight: 600, lineHeight: 1.5 },
  6: { fontSize: "16px", fontWeight: 600, lineHeight: 1.5 },
};

const proseSx = {
  fontSize: "16px",
  lineHeight: 1.7,
  whiteSpace: "pre-wrap",
  overflowWrap: "anywhere",
};

function TitleBlock({ item }) {
  return (
    <Typography
      component="h1"
      sx={{
        fontSize: "28px",
        fontWeight: 700,
        lineHeight: 1.25,
        letterSpacing: "-0.01em",
        mb: 3,
        whiteSpace: "pre-wrap",
      }}
    >
      {item.content}
    </Typography>
  );
}

function HeadingBlock({ item }) {
  const level = Math.min(Math.max(item.attrs?.level ?? 3, 1), 6);
  return (
    <Typography
      component={`h${level}`}
      sx={{ ...HEADING_STYLES[level], mt: 3, mb: 1, whiteSpace: "pre-wrap" }}
    >
      {item.content}
    </Typography>
  );
}

function ParagraphBlock({ item }) {
  return (
    <Typography component="p" sx={{ ...proseSx, mb: 2 }}>
      {item.content}
    </Typography>
  );
}

function QuoteBlock({ item }) {
  return (
    <Box
      component="blockquote"
      sx={{
        mx: 0,
        my: 2,
        pl: 2.5,
        borderLeft: 3,
        borderColor: "divider",
        color: "text.secondary",
      }}
    >
      <Typography sx={{ ...proseSx, fontStyle: "italic" }}>
        {item.content}
      </Typography>
    </Box>
  );
}

function CaptionBlock({ item }) {
  return (
    <Typography
      component="p"
      sx={{
        fontSize: "13px",
        lineHeight: 1.5,
        color: "text.secondary",
        textAlign: "center",
        mt: -1,
        mb: 2,
        whiteSpace: "pre-wrap",
      }}
    >
      {item.content}
    </Typography>
  );
}

function MarginalBlock({ item }) {
  return (
    <Typography
      component="p"
      sx={{
        fontSize: "12px",
        lineHeight: 1.5,
        color: "text.secondary",
        my: 1,
        whiteSpace: "pre-wrap",
      }}
    >
      {item.content}
    </Typography>
  );
}

function CodeBlock({ item }) {
  return (
    <Box
      component="pre"
      sx={{
        my: 2,
        p: 2,
        overflow: "auto",
        borderRadius: 1,
        bgcolor: "background.box",
        border: 1,
        borderColor: "divider",
        fontFamily: '"Geist Mono", monospace',
        fontSize: "13px",
        lineHeight: 1.6,
      }}
    >
      <code>{item.content}</code>
    </Box>
  );
}

function TableBlock({ item }) {
  const rows = Array.isArray(item.attrs?.rows) ? item.attrs.rows : [];
  if (rows.length === 0) return <ParagraphBlock item={item} />;
  const headRow = item.attrs?.header ? rows[0] : null;
  const bodyRows = headRow ? rows.slice(1) : rows;
  return (
    <TableContainer
      sx={{ my: 2, border: 1, borderColor: "divider", borderRadius: 1 }}
    >
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
                <TableCell key={cellIndex} sx={{ fontSize: "14px" }}>
                  {cell}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

function ImageBlock({ item, maxHeight }) {
  const { t } = useTranslation(["datasets"]);
  return (
    <Box
      component="img"
      src={normalizeUrl(item.url)}
      alt={
        item.attrs?.alt ||
        t("datasets:document.imageAlt", { position: item.position + 1 })
      }
      loading="lazy"
      sx={{
        display: "block",
        maxWidth: "100%",
        maxHeight,
        mx: "auto",
        my: 2,
        borderRadius: 1,
      }}
    />
  );
}

const BLOCKS = {
  title: TitleBlock,
  heading: HeadingBlock,
  paragraph: ParagraphBlock,
  quote: QuoteBlock,
  caption: CaptionBlock,
  code: CodeBlock,
  table: TableBlock,
  image: ImageBlock,
  page_header: MarginalBlock,
  page_footer: MarginalBlock,
};

function KindMarker({ kind, children, ...props }) {
  const { t } = useTranslation(["datasets"]);
  const theme = useTheme();
  const color = kindColor(theme, kind);
  return (
    <Box
      {...props}
      sx={{
        position: "relative",
        borderRadius: 1,
        "&::before": {
          content: '""',
          position: "absolute",
          left: -14,
          top: 2,
          bottom: 2,
          width: 3,
          borderRadius: 2,
          bgcolor: color,
        },
      }}
    >
      <Typography
        aria-hidden
        sx={{
          display: { xs: "none", lg: "block" },
          position: "absolute",
          right: "calc(100% + 24px)",
          width: 76,
          textAlign: "right",
          top: 2,
          fontSize: "11px",
          fontWeight: 600,
          lineHeight: 1.35,
          letterSpacing: "0.02em",
          color,
        }}
      >
        {kindLabel(t, kind)}
      </Typography>
      {children}
    </Box>
  );
}

function ListGroup({ items, showKinds }) {
  const ordered = Boolean(items[0].attrs?.ordered);
  const list = (
    <Box component={ordered ? "ol" : "ul"} sx={{ my: 2, pl: 3 }}>
      {items.map((item) => (
        <Box
          component="li"
          key={item.position}
          data-document-position={item.position}
          sx={{ ml: (item.attrs?.depth ?? 0) * 3, mb: 0.5 }}
        >
          <Typography component="span" sx={proseSx}>
            {item.content}
          </Typography>
        </Box>
      ))}
    </Box>
  );
  return showKinds ? <KindMarker kind="list_item">{list}</KindMarker> : list;
}

function groupIntoPages(items) {
  const pages = [];
  items.forEach((item) => {
    const page = item.page ?? null;
    const last = pages[pages.length - 1];
    if (last && last.page === page) {
      last.items.push(item);
    } else {
      pages.push({ page, items: [item] });
    }
  });
  return pages;
}

function groupLists(items, showHidden) {
  const blocks = [];
  items
    .filter((item) => showHidden || !HIDDEN_KINDS.has(item.kind))
    .forEach((item) => {
      const last = blocks[blocks.length - 1];
      if (item.kind === "list_item" && last?.list) {
        last.items.push(item);
      } else if (item.kind === "list_item") {
        blocks.push({ list: true, items: [item] });
      } else {
        blocks.push({ list: false, item });
      }
    });
  return blocks;
}

function Sheet({ page, totalPages, items, showKinds }) {
  const { t } = useTranslation(["datasets"]);
  return (
    <Box
      component="section"
      data-document-page={page ?? undefined}
      aria-label={
        page !== null ? t("datasets:document.pageLabel", { page }) : undefined
      }
      sx={{
        width: "100%",
        maxWidth: SHEET_WIDTH,
        mx: "auto",
        scrollMarginTop: PAGE_ANCHOR_OFFSET,
        bgcolor: "background.paper",
        border: 1,
        borderColor: "divider",
        borderRadius: 1,
        boxShadow: "0 1px 2px rgba(0, 0, 0, 0.08)",
        px: { xs: 3, md: 8 },
        pt: { xs: 3, md: 6 },
        pb: page !== null ? 2 : { xs: 3, md: 6 },
      }}
    >
      <Box
        sx={{
          maxWidth: READING_WIDTH,
          mx: "auto",
          pl: showKinds ? { xs: 0, lg: 13 } : 0,
        }}
      >
        {groupLists(items, showKinds).map((block) =>
          block.list ? (
            <ListGroup
              key={block.items[0].position}
              items={block.items}
              showKinds={showKinds}
            />
          ) : (
            <ReadingBlock
              key={block.item.position}
              item={block.item}
              showKinds={showKinds}
            />
          ),
        )}
      </Box>
      {page !== null && (
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{
            display: "block",
            textAlign: "right",
            mt: { xs: 2, md: 4 },
            mr: { xs: -1, md: -4 },
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {totalPages ? `${page} / ${totalPages}` : page}
        </Typography>
      )}
    </Box>
  );
}

function ReadingBlock({ item, showKinds }) {
  const Block = BLOCKS[item.kind] ?? ParagraphBlock;
  const block = <Block item={item} maxHeight={560} />;
  if (showKinds) {
    return (
      <KindMarker kind={item.kind} data-document-position={item.position}>
        {block}
      </KindMarker>
    );
  }
  return (
    <Box data-document-position={item.position} sx={{ borderRadius: 1 }}>
      {block}
    </Box>
  );
}

function StructureRow({ item }) {
  const { t } = useTranslation(["datasets"]);
  const theme = useTheme();
  const color = kindColor(theme, item.kind);
  const isImage = item.type === "Image";
  return (
    <Box
      data-document-position={item.position}
      sx={{
        display: "grid",
        gridTemplateColumns: { xs: "56px 1fr", md: "64px 168px 1fr" },
        columnGap: 2,
        rowGap: 1,
        alignItems: "start",
        py: 1.5,
        px: 1,
        borderRadius: 1,
        borderBottom: 1,
        borderColor: "divider",
      }}
    >
      <Typography
        sx={{
          fontSize: "13px",
          color: "text.secondary",
          fontVariantNumeric: "tabular-nums",
          textAlign: "right",
          pt: "2px",
        }}
      >
        {item.position + 1}
      </Typography>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, minWidth: 0 }}>
        <Box
          sx={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            bgcolor: color,
            flexShrink: 0,
          }}
        />
        <Typography sx={{ fontSize: "13px", fontWeight: 600 }} noWrap>
          {kindLabel(t, item.kind)}
          {item.kind === "heading" && item.attrs?.level
            ? ` ${item.attrs.level}`
            : ""}
        </Typography>
        <Typography sx={{ fontSize: "12px", color: "text.secondary" }} noWrap>
          {isImage
            ? t("datasets:document.typeImage")
            : t("datasets:document.typeText")}
        </Typography>
      </Box>
      <Box sx={{ gridColumn: { xs: "1 / -1", md: "auto" }, minWidth: 0 }}>
        {isImage ? (
          <ImageBlock item={item} maxHeight={140} />
        ) : (
          <Typography
            sx={{
              fontSize: "14px",
              lineHeight: 1.55,
              whiteSpace: "pre-wrap",
              overflowWrap: "anywhere",
              display: "-webkit-box",
              WebkitLineClamp: 3,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
              color: HIDDEN_KINDS.has(item.kind)
                ? "text.secondary"
                : "text.primary",
            }}
          >
            {item.content}
          </Typography>
        )}
      </Box>
    </Box>
  );
}

function StructureList({ items }) {
  const { t } = useTranslation(["datasets"]);
  return (
    <Box>
      {groupIntoPages(items).map((group) => (
        <Box key={`${group.page}-${group.items[0].position}`} sx={{ mb: 3 }}>
          {group.page !== null && (
            <Typography
              variant="caption"
              color="text.secondary"
              data-document-page={group.page}
              sx={{
                display: "block",
                mb: 0.5,
                ml: 1,
                scrollMarginTop: PAGE_ANCHOR_OFFSET,
              }}
            >
              {t("datasets:document.pageLabel", { page: group.page })}
            </Typography>
          )}
          {group.items.map((item) => (
            <StructureRow key={item.position} item={item} />
          ))}
        </Box>
      ))}
    </Box>
  );
}

export default function DocumentRenderer({
  items,
  mode = "read",
  showKinds = false,
  totalPages = null,
}) {
  if (mode === "structure") return <StructureList items={items} />;
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      {groupIntoPages(items).map((group) => (
        <Sheet
          key={`${group.page}-${group.items[0].position}`}
          page={group.page}
          totalPages={totalPages}
          items={group.items}
          showKinds={showKinds}
        />
      ))}
    </Box>
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
MarginalBlock.propTypes = { item: itemShape.isRequired };
CodeBlock.propTypes = { item: itemShape.isRequired };
TableBlock.propTypes = { item: itemShape.isRequired };
ImageBlock.propTypes = {
  item: itemShape.isRequired,
  maxHeight: PropTypes.number,
};
KindMarker.propTypes = {
  kind: PropTypes.string.isRequired,
  children: PropTypes.node,
};
ListGroup.propTypes = {
  items: PropTypes.arrayOf(itemShape).isRequired,
  showKinds: PropTypes.bool,
};
Sheet.propTypes = {
  page: PropTypes.number,
  totalPages: PropTypes.number,
  items: PropTypes.arrayOf(itemShape).isRequired,
  showKinds: PropTypes.bool,
};
ReadingBlock.propTypes = {
  item: itemShape.isRequired,
  showKinds: PropTypes.bool,
};
StructureRow.propTypes = { item: itemShape.isRequired };
StructureList.propTypes = { items: PropTypes.arrayOf(itemShape).isRequired };
DocumentRenderer.propTypes = {
  items: PropTypes.arrayOf(itemShape).isRequired,
  mode: PropTypes.oneOf(["read", "structure"]),
  showKinds: PropTypes.bool,
  totalPages: PropTypes.number,
};
