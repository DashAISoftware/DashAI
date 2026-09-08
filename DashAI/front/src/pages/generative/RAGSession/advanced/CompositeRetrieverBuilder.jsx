import { useState, useEffect, useCallback, useRef } from "react";
import { Box, Typography, IconButton, Tooltip } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import RemoveCircleOutlineIcon from "@mui/icons-material/RemoveCircleOutline";
import SchemaIcon from "@mui/icons-material/Schema";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import MergeIcon from "@mui/icons-material/Merge";
import SortIcon from "@mui/icons-material/Sort";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import {
  getRetrieverComponents,
  getRetrievalParadigm,
} from "../../../../api/rag";
import {
  loadRetrieverKinds,
  isComposite as isCompositeKind,
} from "../retrieverKinds";
import { resolveDefaults } from "../../../../utils/schema";
import RetrieverNodeConfig from "./RetrieverNodeConfig";

// Base horizontal unit (px) for the tree indentation. A card at depth d is
// indented d*INDENT px, and the vertical spine that connects a level is drawn
// INDENT/2 px to the left of the card at that level, so consecutive spine
// columns are always exactly INDENT px apart. All geometry is expressed as
// explicit px strings so the theme spacing multiplier does not apply.
const INDENT = 40;

let _nodeIdCounter = 0;
function nextId() {
  return `n_${++_nodeIdCounter}`;
}

/**
 * Resolves a display string from a value that may be a plain string, a
 * multilingual object, or something else.
 * @param {*} val - The value to resolve.
 * @returns {string|null} The resolved string, or null.
 */
function getString(val) {
  if (!val) return null;
  if (typeof val === "string") return val;
  if (val.en) return val.en;
  return String(val);
}

/**
 * Builds a subtitle for a DenseEmbeddingRetriever node showing the wrapped
 * embedding model and its model name, e.g.
 * "SentenceTransformer Embedding - microsoft/harrier-oss-v1-0.6b".
 *
 * The embedding_model param is stored as a subform structure:
 *   { properties: { component: parent, params: { comp: { component, params } } } }
 * It may also appear in the simpler { component, params } form.
 *
 * @param {object} node - The tree node to inspect.
 * @param {object} [denseDefaults] - Cached default params for DenseEmbeddingRetriever.
 * @param {object} embNameMap - Map of embedding component name -> display name.
 * @returns {object|null} `{ embName, modelName }` or null.
 */
function getDenseEmbeddingInfo(node, denseDefaults, embNameMap) {
  if (node.component !== "DenseEmbeddingRetriever") return null;
  let emb = node.params?.embedding_model;
  if (!emb && denseDefaults?.embedding_model) {
    emb = denseDefaults.embedding_model;
  }
  if (!emb) return null;

  // Parse subform structure: { properties: { component, params: { comp: { component, params } } } }
  let compName = emb.properties?.params?.comp?.component || emb.component;
  let modelParams = emb.properties?.params?.comp?.params || emb.params;
  if (!compName) return null;

  const embName = embNameMap?.[compName] || compName;
  const modelName = modelParams?.model_name;
  return { embName, modelName: modelName || null };
}

/**
 * Interactive tree builder for composite retriever types (Sequential, Parallel, MMR Reranker).
 * Allows adding/removing child nodes and configuring each node's component and parameters.
 *
 * @param {object} props
 * @param {string} props.rootComponent - Name of the root composite retriever component.
 * @param {object} [props.rootParams] - Initial parameters for the root node, including children.
 * @param {function} props.onChange - Callback with the serialised tree on every change.
 * @returns {JSX.Element} The tree builder UI.
 */
export default function CompositeRetrieverBuilder({
  rootComponent,
  rootParams,
  onChange,
}) {
  const theme = useTheme();
  const { t } = useTranslation(["generative"]);
  const [allComponents, setAllComponents] = useState([]);
  const [leafRegistry, setLeafRegistry] = useState({});
  const [editing, setEditing] = useState(null);
  const [tree, setTree] = useState(null);

  const [ready, setReady] = useState(false);
  const [embNameMap, setEmbNameMap] = useState({});
  const [editingParentId, setEditingParentId] = useState(null);
  const denseDefaultsRef = useRef(null);
  const treeBoxRef = useRef(null);

  useEffect(() => {
    if (!tree) return;
    const container = treeBoxRef.current;
    if (!container) return;
    const cr = container.getBoundingClientRect();
    const fmt = (el, label) => {
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      const x = (r.left - cr.left).toFixed(1);
      const y = (r.top - cr.top).toFixed(1);
      const w = r.width.toFixed(1);
      const h = r.height.toFixed(1);
      return (
        `${label.padEnd(10)} ${el.getAttribute("data-node")?.padEnd(30)}` +
        ` x=${x.padStart(6)} y=${y.padStart(6)} w=${w.padStart(
          6,
        )} h=${h.padStart(6)}` +
        ` | pos=${cs.position} L=${cs.left} T=${cs.top} W=${cs.width} B=${cs.boxSizing}`
      );
    };
    const lines = ["[CompositeRetrieverBuilder DOM layout]"];
    container.querySelectorAll("[data-card]").forEach((el) => {
      lines.push(fmt(el, "card"));
    });
    container.querySelectorAll("[data-conn]").forEach((el) => {
      lines.push(fmt(el, "connector"));
    });
    container.querySelectorAll("[data-op]").forEach((el) => {
      lines.push(fmt(el, "opcard"));
    });
    container.querySelectorAll("[data-spine]").forEach((el) => {
      lines.push(fmt(el, "spine"));
    });
    console.log(lines.join("\n"));
  }, [tree]);

  useEffect(() => {
    resolveDefaults("DenseEmbeddingRetriever")
      .then((d) => {
        denseDefaultsRef.current = d;
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    (async () => {
      await loadRetrieverKinds();
      const paradigms = await getRetrievalParadigm();
      const leaves = paradigms.filter((p) => !isCompositeKind(p.name));
      const leafMap = {};
      for (const leaf of leaves) {
        const children = await getRetrieverComponents(leaf.name);
        leafMap[leaf.name] = (children || []).filter(
          (c) => c.configurable_object !== false,
        );
      }
      setAllComponents(paradigms);
      setLeafRegistry(leafMap);

      // Build a display-name map for DenseEmbedding components (e.g.
      // SentenceTransformerEmbedding -> "SentenceTransformer Embedding").
      try {
        const embeddingComponents =
          await getRetrieverComponents("DenseEmbedding");
        const nameMap = {};
        for (const comp of embeddingComponents || []) {
          nameMap[comp.name] =
            getString(comp.display_name) || getString(comp.name) || comp.name;
        }
        setEmbNameMap(nameMap);
      } catch {
        // ignore — fall back to raw component names
      }

      setReady(true);
    })();
  }, []);

  useEffect(() => {
    if (!ready) return;

    (async () => {
      _nodeIdCounter = 0;
      const fromParams = rootParams?.children || [];

      const buildFromParams = (child) => {
        const id = nextId();
        const comp = findComponent(child.component);
        const node = {
          nodeId: id,
          component: child.component,
          params: child.params || {},
          children: [],
        };
        if (isCompositeKind(child.component) && child.children?.length) {
          node.children = child.children.map(buildFromParams).filter(Boolean);
        }
        return comp ? node : null;
      };

      const existingChildren = fromParams.map(buildFromParams).filter(Boolean);

      setTree({
        nodeId: nextId(),
        component: rootComponent,
        params: rootParams || {},
        children: existingChildren,
      });
    })();
  }, [ready, rootComponent]);

  /**
   * Finds a component definition by name across all paradigms and leaf registries.
   * @param {string} name - Component name to look up.
   * @returns {object|undefined} The component definition object, or undefined.
   */
  const findComponent = (name) => {
    const direct = allComponents.find((c) => c.name === name);
    if (direct) return direct;
    for (const key of Object.keys(leafRegistry)) {
      const found = (leafRegistry[key] || []).find((c) => c.name === name);
      if (found) return found;
    }
    return null;
  };

  /**
   * Serialises the current tree and fires the onChange callback.
   * @param {object} t - The current tree root node.
   */
  const emit = useCallback(
    (t) => {
      const ser = (n) => {
        const s = { component: n.component, params: n.params || {} };
        if (isCompositeKind(n.component) && n.children.length > 0) {
          s.children = n.children.map(ser).filter((child) => child.component);
        }
        return s;
      };
      onChange({
        component: t.component,
        params: {
          ...t.params,
          children: t.children.map(ser).filter((child) => child.component),
        },
      });
    },
    [onChange],
  );

  /**
   * Immutably updates a tree node identified by its nodeId.
   * @param {object} root - The root of the tree to traverse.
   * @param {string} nodeId - The target node ID.
   * @param {function} fn - A mutator function receiving the matched node.
   * @returns {object} A new tree with the update applied.
   */
  const updateAt = (root, nodeId, fn) => {
    const walk = (n) => {
      if (n.nodeId === nodeId) return fn(n);
      if (n.children) return { ...n, children: n.children.map(walk) };
      return n;
    };
    return walk(root);
  };

  /**
   * Persists a node's component selection and parameters into the tree.
   * @param {string} nodeId - The target node ID.
   * @param {string} component - The selected component name.
   * @param {object} params - The component parameters.
   */
  const handleSaveNode = (nodeId, component, params) => {
    const isComposite = isCompositeKind(component);
    setTree((prev) => {
      const updated = updateAt(prev, nodeId, (n) => ({
        ...n,
        component,
        params: { ...params },
        children: isComposite ? n.children : [],
      }));
      emit(updated);
      return updated;
    });
    setEditing(null);
    setEditingParentId(null);
  };

  /**
   * Adds an empty child node under the specified parent.
   * Cleans up any previously-added children that were never configured.
   * @param {string} parentId - The parent node ID to add a child under.
   */
  const handleAddChild = (parentId) => {
    const id = nextId();
    setEditingParentId(parentId);
    setTree((prev) => {
      const updated = updateAt(prev, parentId, (n) => ({
        ...n,
        children: [
          ...(n.children || []).filter((c) => c.component !== ""),
          { nodeId: id, component: "", params: {}, children: [] },
        ],
      }));
      emit(updated);
      return updated;
    });
    setEditing(id);
  };

  /**
   * Removes a child node from the specified parent.
   * @param {string} parentId - The parent node ID.
   * @param {string} childId - The child node ID to remove.
   */
  const handleRemoveChild = (parentId, childId) => {
    setTree((prev) => {
      const updated = updateAt(prev, parentId, (n) => ({
        ...n,
        children: (n.children || []).filter((c) => c.nodeId !== childId),
      }));
      emit(updated);
      return updated;
    });
  };

  if (!tree) {
    return (
      <Box sx={{ py: 4, textAlign: "center" }}>
        <Typography variant="body2" color="text.secondary">
          {t("generative:rag.common.loading")}
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "row",
        gap: 2,
        alignItems: "flex-start",
      }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 0.5,
          mt: 1,
          minWidth: 90,
          flexShrink: 0,
        }}
      >
        <Typography
          variant="caption"
          sx={{
            color: "text.secondary",
            textAlign: "center",
            lineHeight: 1.2,
          }}
        >
          {t("generative:rag.composite.allChunks")}
        </Typography>

        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            my: 1,
          }}
        >
          <Box
            sx={{
              width: 0,
              height: 0,
              borderLeft: "14px solid transparent",
              borderRight: "14px solid transparent",
              borderTop: `20px solid ${theme.palette.divider}`,
            }}
          />
          <Box sx={{ width: 2, height: 24, bgcolor: "divider" }} />
          <Box
            sx={{
              width: 0,
              height: 0,
              borderLeft: "14px solid transparent",
              borderRight: "14px solid transparent",
              borderTop: `20px solid ${theme.palette.divider}`,
            }}
          />
          <Box sx={{ width: 2, height: 24, bgcolor: "divider" }} />
          <Box
            sx={{
              width: 0,
              height: 0,
              borderLeft: "14px solid transparent",
              borderRight: "14px solid transparent",
              borderTop: `20px solid ${theme.palette.divider}`,
            }}
          />
        </Box>

        <Typography
          variant="caption"
          sx={{
            color: "text.secondary",
            textAlign: "center",
            lineHeight: 1.2,
          }}
        >
          {t("generative:rag.composite.selectedChunks")}
        </Typography>
      </Box>

      <Box ref={treeBoxRef} sx={{ flex: 1, minWidth: 0 }}>
        <TreeNodeView
          node={tree}
          depth={0}
          isRoot
          parentId={null}
          findComponent={findComponent}
          embNameMap={embNameMap}
          denseDefaults={denseDefaultsRef.current}
          onEdit={(id) => setEditing(id)}
          onAddChild={handleAddChild}
          onRemoveChild={handleRemoveChild}
          theme={theme}
          t={t}
        />
      </Box>

      {editing && (
        <RetrieverNodeConfig
          open
          nodeId={editing}
          nodeData={findNodeData(tree, editing)}
          allComponents={allComponents}
          leafRegistry={leafRegistry}
          onSave={handleSaveNode}
          onClose={() => {
            // Clean up placeholder child if dialog was closed without saving
            const node = findNodeData(tree, editing);
            if (node && !node.component && editingParentId) {
              handleRemoveChild(editingParentId, editing);
            }
            setEditing(null);
            setEditingParentId(null);
          }}
        />
      )}
    </Box>
  );
}

CompositeRetrieverBuilder.propTypes = {
  rootComponent: PropTypes.string.isRequired,
  rootParams: PropTypes.object,
  onChange: PropTypes.func.isRequired,
};

/**
 * Recursively searches a tree for a node by its nodeId.
 * @param {object} tree - The tree root to search.
 * @param {string} nodeId - The node ID to find.
 * @returns {object|null} The matching node, or null.
 */
function findNodeData(tree, nodeId) {
  if (tree.nodeId === nodeId) return tree;
  if (tree.children) {
    for (const c of tree.children) {
      const found = findNodeData(c, nodeId);
      if (found) return found;
    }
  }
  return null;
}

/**
 * Builds the summary for a composite retriever's own operation (reranking or
 * chunk fusion) rendered as the final node of the tree. The operation
 * description is declarative and comes from the component metadata
 * (``operation_summary``), so the frontend never hardcodes component names.
 * @param {object} node - The tree node to summarise.
 * @param {object} info - The component definition for the node.
 * @param {function} t - i18n translate function.
 * @returns {object|null} `{ label, value, icon }` or null for non-composite nodes.
 */
function getOperationSummary(node, info, t) {
  const summary = info?.metadata?.operation_summary;
  if (!summary?.kind) return null;

  const isRerank = summary.kind === "rerank";
  const label = isRerank
    ? t("generative:rag.composite.reranking")
    : t("generative:rag.composite.chunkFusion");
  const icon = isRerank ? "rerank" : "fusion";

  const params = node.params || {};
  const fields = summary.fields || [];
  const parts = fields.map((field) => {
    const value = params[field.param];
    const rendered = value == null ? "—" : String(value);
    return field.label ? `${field.label}=${rendered}` : rendered;
  });

  return {
    label,
    icon,
    value: parts.length > 0 ? parts.join(", ") : null,
  };
}

/**
 * Renders a single node in the composite retriever tree, including its
 * icon, name, add/remove controls, and recursively renders children.
 *
 * @param {object} props
 * @param {object} props.node - The tree node to render.
 * @param {number} props.depth - Current depth level (used for indentation).
 * @param {boolean} props.isRoot - Whether this is the root node.
 * @param {string|null} props.parentId - The parent node ID (null for root).
 * @param {function} props.findComponent - Lookup function for component definitions.
 * @param {object} props.embNameMap - Map of embedding component name -> display name.
 * @param {object} props.denseDefaults - Cached default params for DenseEmbeddingRetriever.
 * @param {function} props.onEdit - Callback to open the config dialog for a node.
 * @param {function} props.onAddChild - Callback to add a child node.
 * @param {function} props.onRemoveChild - Callback to remove a child node.
 * @param {object} props.theme - MUI theme object.
 * @param {function} props.t - i18n translate function.
 * @returns {JSX.Element|null} The tree node UI.
 */
function TreeNodeView({
  node,
  depth,
  isRoot,
  parentId,
  findComponent,
  embNameMap,
  denseDefaults,
  onEdit,
  onAddChild,
  onRemoveChild,
  theme,
  t,
}) {
  if (!node || !node.component) return null;

  const info = findComponent(node.component);
  const name =
    getString(info?.display_name) ||
    getString(info?.name) ||
    node.component ||
    t("generative:rag.composite.configureNode");
  const isComposite = isCompositeKind(node.component);
  const cardX = depth * INDENT;
  const operation = isComposite ? getOperationSummary(node, info, t) : null;
  const denseInfo = getDenseEmbeddingInfo(node, denseDefaults, embNameMap);

  return (
    <Box>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 1,
          ml: `${cardX}px`,
          position: "relative",
        }}
      >
        {depth > 0 && (
          <Box
            data-conn
            data-node={`${node.component}@${depth}`}
            sx={{
              position: "absolute",
              left: `${-INDENT / 2}px`,
              top: "50%",
              width: `${INDENT / 2}px`,
              borderTop: "1px solid",
              borderColor: "divider",
            }}
          />
        )}
        <Box
          data-card
          data-node={`${node.component}@${depth}`}
          onClick={() => onEdit(node.nodeId)}
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
            px: 1.5,
            py: 1,
            border: "1px solid",
            borderColor: isComposite
              ? "accent.purpleBorder"
              : "accent.amberBorder",
            borderRadius: 1,
            cursor: "pointer",
            backgroundColor: "background.paper",
            "&:hover": { backgroundColor: "action.hover" },
          }}
        >
          {isComposite ? (
            <AccountTreeIcon sx={{ fontSize: 18, color: "accent.purple" }} />
          ) : (
            <SchemaIcon sx={{ fontSize: 18, color: "accent.amber" }} />
          )}
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              minWidth: "fit-content",
              maxWidth: 480,
            }}
          >
            <Typography variant="body2">{name}</Typography>
            {denseInfo && (
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{
                  maxWidth: 420,
                  overflowWrap: "anywhere",
                }}
              >
                {denseInfo.embName}
                {denseInfo.modelName ? ` - ${denseInfo.modelName}` : ""}
              </Typography>
            )}
          </Box>
        </Box>

        {isComposite && (
          <Tooltip title={t("generative:rag.composite.addChild")}>
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onAddChild(node.nodeId);
              }}
              sx={{ color: "primary.main" }}
            >
              <AddCircleOutlineIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}

        {!isRoot && (
          <Tooltip title={t("generative:rag.composite.removeNode")}>
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onRemoveChild(parentId, node.nodeId);
              }}
              sx={{ color: "error.main" }}
            >
              <RemoveCircleOutlineIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
      </Box>

      {node.children?.length > 0 && (
        <Box sx={{ position: "relative" }}>
          {node.children.filter(Boolean).map((child) => (
            <Box key={child.nodeId} sx={{ position: "relative" }}>
              <Box
                data-spine
                data-node={`${node.component}@${depth}`}
                sx={{
                  position: "absolute",
                  left: `${cardX + INDENT / 2}px`,
                  top: 0,
                  bottom: 0,
                  width: "1px",
                  borderLeft: "1px solid",
                  borderColor: "divider",
                }}
              />
              <TreeNodeView
                node={child}
                depth={depth + 1}
                isRoot={false}
                parentId={node.nodeId}
                findComponent={findComponent}
                embNameMap={embNameMap}
                denseDefaults={denseDefaults}
                onEdit={onEdit}
                onAddChild={onAddChild}
                onRemoveChild={onRemoveChild}
                theme={theme}
                t={t}
              />
            </Box>
          ))}
        </Box>
      )}

      {operation && (
        <Box sx={{ position: "relative" }}>
          {depth > 0 && (
            <Box
              data-op
              data-node={`${node.component}@${depth}::conn`}
              sx={{
                position: "absolute",
                left: `${cardX - INDENT / 2}px`,
                top: "50%",
                width: `${INDENT / 2}px`,
                borderTop: "1px solid",
                borderColor: "divider",
              }}
            />
          )}
          <Box
            data-op
            data-node={`${node.component}@${depth}::card`}
            onClick={() => onEdit(node.nodeId)}
            title={t("generative:rag.composite.configureNode")}
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1,
              ml: `${cardX}px`,
              my: 0.5,
              px: 1.25,
              py: 0.5,
              width: "fit-content",
              maxWidth: "100%",
              border: "1px dashed",
              borderColor: "accent.purpleBorder",
              borderRadius: 1,
              cursor: "pointer",
              backgroundColor: "background.paper",
              "&:hover": { backgroundColor: "action.hover" },
            }}
          >
            {operation.icon === "fusion" ? (
              <MergeIcon sx={{ fontSize: 16, color: "accent.purple" }} />
            ) : (
              <SortIcon sx={{ fontSize: 16, color: "accent.purple" }} />
            )}
            <Typography
              variant="caption"
              sx={{
                fontWeight: 600,
                color: "text.secondary",
                whiteSpace: "nowrap",
              }}
            >
              {operation.label}
            </Typography>
            {operation.value && (
              <Typography
                variant="caption"
                sx={{
                  color: "text.primary",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                  maxWidth: 280,
                }}
              >
                {operation.value}
              </Typography>
            )}
          </Box>
        </Box>
      )}
    </Box>
  );
}

TreeNodeView.propTypes = {
  node: PropTypes.object.isRequired,
  depth: PropTypes.number.isRequired,
  isRoot: PropTypes.bool.isRequired,
  parentId: PropTypes.string,
  findComponent: PropTypes.func.isRequired,
  embNameMap: PropTypes.object,
  denseDefaults: PropTypes.object,
  onEdit: PropTypes.func.isRequired,
  onAddChild: PropTypes.func.isRequired,
  onRemoveChild: PropTypes.func.isRequired,
  theme: PropTypes.object.isRequired,
  t: PropTypes.func.isRequired,
};
