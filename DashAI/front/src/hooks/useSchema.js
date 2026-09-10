import { useEffect, useState } from "react";
import { getComponents } from "../api/component";
import { formattedModel, generateYupSchema } from "../utils/schema";
import { useTranslation } from "react-i18next";

/**
 * This hook is used to get the schema of a model, it will return the schema and the initial values of the model
 * @param {string} modelName - The name of the model to get the schema
 */

// This hook backs every configurable-object form in the app (pipelines,
// converters, explorers, dataloaders, models...), not just the dialogs that
// prompted this cache — a wizard step's own prefetch and the form it renders
// a step later both call this hook for the same model within milliseconds of
// each other, and without sharing that one fetch, the second consumer showed
// an empty form for a beat. But nothing here should keep serving a schema
// fetched minutes ago to some unrelated form (or care about a plugin
// install/uninstall changing it) — so the cache is short-lived: long enough
// to dedupe that one burst of near-simultaneous mounts, short enough that
// everything else still gets a fresh fetch per mount, same as before.
const CACHE_TTL_MS = 10_000;
const schemaCache = new Map(); // modelName -> { value, expiresAt }
// In-flight fetches, shared across near-simultaneous consumers of the same
// modelName (e.g. a wizard step's own prefetch and the form it renders a
// step later) so only one request goes out instead of one per consumer.
const pendingSchemaFetches = new Map(); // modelName -> Promise<formattedSchema>

function getCachedSchema(modelName) {
  if (!modelName) return null;
  const entry = schemaCache.get(modelName);
  if (!entry) return null;
  if (Date.now() > entry.expiresAt) {
    schemaCache.delete(modelName);
    return null;
  }
  return entry.value;
}

function setCachedSchema(modelName, value) {
  schemaCache.set(modelName, { value, expiresAt: Date.now() + CACHE_TTL_MS });
}

function fetchSchema(modelName) {
  if (pendingSchemaFetches.has(modelName)) {
    return pendingSchemaFetches.get(modelName);
  }
  const promise = getComponents({ model: modelName })
    .then((result) => formattedModel(result?.schema))
    .then((formattedSchema) => {
      setCachedSchema(modelName, formattedSchema);
      return formattedSchema;
    })
    .finally(() => {
      pendingSchemaFetches.delete(modelName);
    });
  pendingSchemaFetches.set(modelName, promise);
  return promise;
}

export default function useSchema({ modelName = null } = {}) {
  const [model, setModel] = useState(() => getCachedSchema(modelName));
  const [loading, setLoading] = useState(false);
  const { t } = useTranslation();

  useEffect(() => {
    let cancelled = false;

    const cached = getCachedSchema(modelName);
    if (cached) {
      setModel(cached);
      return undefined;
    }

    setModel(null);

    const getModel = async () => {
      try {
        setLoading(true);
        const formattedSchema = await fetchSchema(modelName);
        if (!cancelled) {
          setModel(formattedSchema);
        }
      } catch (error) {
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    if (modelName) {
      getModel();
    }

    return () => {
      cancelled = true;
    };
  }, [modelName, t]);

  const { schema, initialValues } = model
    ? generateYupSchema(model)
    : { schema: {}, initialValues: {} };

  return {
    modelSchema: model,
    defaultValues: initialValues,
    yupSchema: schema,
    loading,
  };
}
