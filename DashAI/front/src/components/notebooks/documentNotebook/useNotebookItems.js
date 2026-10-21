import { useCallback, useEffect, useRef, useState } from "react";
import { getNotebookDocumentContent } from "../../../api/notebook";

const PAGE_SIZE = 100;

export default function useNotebookItems(
  notebookId,
  contentType,
  kinds,
  version,
) {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  const requestRef = useRef(0);
  const itemsRef = useRef([]);
  const kindsKey = kinds.join("|");

  const fetchFrom = useCallback(
    async (offset, request) => {
      setLoading(true);
      setFailed(false);
      try {
        const page = await getNotebookDocumentContent(
          notebookId,
          contentType,
          offset,
          PAGE_SIZE,
          kindsKey ? kindsKey.split("|") : [],
        );
        if (request !== requestRef.current) return;
        if (page.offset !== itemsRef.current.length) return;
        itemsRef.current = [...itemsRef.current, ...page.items];
        setItems(itemsRef.current);
        setTotal(page.total);
      } catch (error) {
        if (request === requestRef.current) setFailed(true);
      } finally {
        if (request === requestRef.current) setLoading(false);
      }
    },
    [notebookId, contentType, kindsKey],
  );

  useEffect(() => {
    requestRef.current += 1;
    itemsRef.current = [];
    setItems([]);
    setTotal(0);
    fetchFrom(0, requestRef.current);
  }, [fetchFrom, version]);

  const loadMore = useCallback(() => {
    if (loading || itemsRef.current.length >= total) return;
    fetchFrom(itemsRef.current.length, requestRef.current);
  }, [fetchFrom, loading, total]);

  return { items, total, loading, failed, loadMore };
}
