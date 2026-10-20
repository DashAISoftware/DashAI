import { useState, useEffect, useCallback, useRef } from "react";
import { Box, Typography, IconButton, Tooltip } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import RemoveCircleOutlineIcon from "@mui/icons-material/RemoveCircleOutline";
import SchemaIcon from "@mui/icons-material/Schema";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
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
import { resolveLocalizedText } from "../../../../utils/localize";
import { resolveRetrieverRepresentation } from "../../../../components/generative/RAG/retrieverRepresentation";
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
 * Returns the child refs of a serialised retriever ref at any nesting level.
 * A top-level `children` array is authoritative whenever it exists, even when
 * empty: canonical backend refs never carry that key, so its presence
 * identifies the legacy shape written by the previous builder, where children
 * were stored as `ref.children`. Otherwise canonical `params.children` is used
 * (e.g. `{ component: "ParallelRetriever", params: { children: [...] } }`).
 * An older payload which removed every child may still carry stale
 * `params.children` with no top-level key; the next edit rewrites it
 * canonically.
 * @param {object} ref - Serialised retriever ref to inspect.
 * @returns {object[]} The child refs, or an empty array.
 */
function getChildRefs(ref) {
  if (Array.isArray(ref?.children)) return ref.children;
  if (Array.isArray(ref?.params?.children)) return ref.params.children;
  return [];
}

/**
 * Recursively maps a serialised retriever ref into an editable tree node.
 * Composite refs resolve their children through `getChildRefs`, so nested
 * children come from canonical `params.children` or the legacy top-level
 * `children`. Refs whose component cannot be resolved are dropped (null) and
 * filtered out by callers, keeping unknown components out of the tree.
 * @param {object} ref - Serialised retriever ref to map.
 * @param {function} findComponent - Lookup for component definitions by name.
 * @returns {object|null} The tree node, or null when the component is unknown.
 */
function buildNodeFromRef(ref, findComponent) {
  if (!findComponent(ref.component)) return null;
  const node = {
    nodeId: nextId(),
    component: ref.component,
    params: ref.params || {},
    children: [],
  };
  if (isCompositeKind(ref.component)) {
    node.children = getChildRefs(ref)
      .map((child) => buildNodeFromRef(child, findComponent))
      .filter(Boolean);
  }
  return node;
}

/**
 * Resolves a display string from a value that may be a plain string or a
 * multilingual object, using the active UI language.
 * @param {*} val - The value to resolve.
 * @param {object} i18n - i18next instance with a `language` property.
 * @returns {string|null} The resolved string, or null.
 */
function getString(val, i18n) {
  if (!val) return null;
  if (typeof val === "string") return val;
  return resolveLocalizedText(val, i18n);
}

/**
 * Interactive tree builder for composite retriever types (Sequential, Parallel, MMR Reranker).
 * Allows adding/removing child nodes and configuring each node's component and parameters.
 *
 * @param {object} props
 * @param {string} props.rootComponent - Name of the root composite retriever component.
 * @param {object} [props.rootParams] - Initial parameters for the root node, including children under `children`.
 * @param {function} props.onChange - Callback with the serialised tree on every change.
 * @returns {JSX.Element} The tree builder UI.
 */
export default function CompositeRetrieverBuilder({
  rootComponent,
  rootParams,
  onChange,
}) {
  const theme = useTheme();
  const { t, i18n } = useTranslation(["generative"]);
  const [allComponents, setAllComponents] = useState([]);
  const [leafRegistry, setLeafRegistry] = useState({});
  const [editing, setEditing] = useState(null);
  const [tree, setTree] = useState(null);

  const [ready, setReady] = useState(false);
  const [editingParentId, setEditingParentId] = useState(null);
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
    container.querySelectorAll("[data-spine]").forEach((el) => {
      lines.push(fmt(el, "spine"));
    });
    console.log(lines.join("\n"));
  }, [tree]);

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
      setReady(true);
    })();
  }, []);

  useEffect(() => {
    if (!ready) return;

    (async () => {
      _nodeIdCounter = 0;
      const fromParams = rootParams?.children || [];

      const existingChildren = fromParams
        .map((child) => buildNodeFromRef(child, findComponent))
        .filter(Boolean);

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
   * Nested composites are serialised canonically with their children under
   * `params.children`, matching the backend ref format.
   * @param {object} t - The current tree root node.
   */
  const emit = useCallback(
    (t) => {
      const ser = (n) => {
        const params = { ...(n.params || {}) };
        if (isCompositeKind(n.component)) {
          params.children = (n.children || [])
            .map(ser)
            .filter((child) => child.component);
        }
        return { component: n.component, params };
      };
      onChange({
        component: t.component,
        params: {
          ...(t.params || {}),
          children: (t.children || [])
            .map(ser)
            .filter((child) => child.component),
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
   * When the component is changed to a composite and the node has no tree
   * children yet, the component's default children are materialised from the
   * form `params` so schema defaults are not discarded. Keeping the same
   * component preserves the existing children exactly (including an empty
   * list), so deliberately removed children are not reseeded.
   * @param {string} nodeId - The target node ID.
   * @param {string} component - The selected component name.
   * @param {object} params - The component parameters.
   */
  const handleSaveNode = (nodeId, component, params) => {
    const isComposite = isCompositeKind(component);
    setTree((prev) => {
      const updated = updateAt(prev, nodeId, (n) => {
        const hasNoChildren = !n.children || n.children.length === 0;
        const seedDefaults =
          isComposite && n.component !== component && hasNoChildren;
        let children = isComposite ? n.children : [];
        if (seedDefaults) {
          children = getChildRefs({ params })
            .map((child) => buildNodeFromRef(child, findComponent))
            .filter(Boolean);
        }
        return {
          ...n,
          component,
          params: { ...params },
          children,
        };
      });
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
          onEdit={(id) => setEditing(id)}
          onAddChild={handleAddChild}
          onRemoveChild={handleRemoveChild}
          t={t}
          i18n={i18n}
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
 * Renders a single node in the composite retriever tree, including its
 * icon, name, add/remove controls, and recursively renders children.
 *
 * @param {object} props
 * @param {object} props.node - The tree node to render.
 * @param {number} props.depth - Current depth level (used for indentation).
 * @param {boolean} props.isRoot - Whether this is the root node.
 * @param {string|null} props.parentId - The parent node ID (null for root).
 * @param {function} props.findComponent - Lookup function for component definitions.
 * @param {function} props.onEdit - Callback to open the config dialog for a node.
 * @param {function} props.onAddChild - Callback to add a child node.
 * @param {function} props.onRemoveChild - Callback to remove a child node.
 * @param {function} props.t - i18n translate function.
 * @param {object} props.i18n - i18next instance used to localise metadata.
 * @returns {JSX.Element|null} The tree node UI.
 */
function TreeNodeView({
  node,
  depth,
  isRoot,
  parentId,
  findComponent,
  onEdit,
  onAddChild,
  onRemoveChild,
  t,
  i18n,
}) {
  if (!node || !node.component) return null;

  const info = findComponent(node.component);
  const name =
    getString(info?.display_name, i18n) ||
    getString(info?.name, i18n) ||
    node.component ||
    t("generative:rag.composite.configureNode");
  const isComposite = isCompositeKind(node.component);
  const cardX = depth * INDENT;
  const representation = resolveRetrieverRepresentation(
    info,
    node.params,
    i18n,
  );
  const description = resolveLocalizedText(info?.description, i18n);
  const caption = representation || description || null;

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
            {caption && (
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{
                  maxWidth: 420,
                  overflowWrap: "anywhere",
                }}
              >
                {caption}
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
                onEdit={onEdit}
                onAddChild={onAddChild}
                onRemoveChild={onRemoveChild}
                t={t}
                i18n={i18n}
              />
            </Box>
          ))}
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
  onEdit: PropTypes.func.isRequired,
  onAddChild: PropTypes.func.isRequired,
  onRemoveChild: PropTypes.func.isRequired,
  t: PropTypes.func.isRequired,
  i18n: PropTypes.object.isRequired,
};
