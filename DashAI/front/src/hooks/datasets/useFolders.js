import { useState, useCallback, useEffect } from "react";
import { useSnackbar } from "notistack";
import {
  getFolders,
  createFolder as createFolderApi,
  updateFolder as updateFolderApi,
  deleteFolder as deleteFolderApi,
} from "../../api/folders";

export function useFolders({ t }) {
  const { enqueueSnackbar } = useSnackbar();
  const [folders, setFolders] = useState([]);

  useEffect(() => {
    fetchFolders();
  }, []);

  const fetchFolders = useCallback(async () => {
    const data = await getFolders();
    setFolders(data);
    return data;
  }, []);

  const createFolder = async (name) => {
    try {
      const created = await createFolderApi(name);
      setFolders((prev) => [...prev, created]);
      enqueueSnackbar(t("datasets:message.folderCreateSuccess"), {
        variant: "success",
      });
      return created;
    } catch (error) {
      if (error.response?.status === 409) {
        enqueueSnackbar(t("datasets:error.folderNameExists"), {
          variant: "error",
        });
      } else {
        enqueueSnackbar(t("datasets:error.failedToCreateFolder"), {
          variant: "error",
        });
      }
      throw error;
    }
  };

  const renameFolder = async (id, newName) => {
    try {
      const updated = await updateFolderApi(id, newName);
      setFolders((prev) =>
        prev.map((f) => (f.id === id ? { ...f, name: updated.name } : f)),
      );
      enqueueSnackbar(t("datasets:message.folderUpdateSuccess"), {
        variant: "success",
      });
    } catch (error) {
      if (error.response?.status === 409) {
        enqueueSnackbar(t("datasets:error.folderNameExists"), {
          variant: "error",
        });
      } else {
        enqueueSnackbar(t("datasets:error.failedToUpdateFolder"), {
          variant: "error",
        });
      }
      throw error;
    }
  };

  const deleteFolderById = async (id) => {
    try {
      await deleteFolderApi(id);
      setFolders((prev) => prev.filter((f) => f.id !== id));
      enqueueSnackbar(t("datasets:message.folderDeleteSuccess"), {
        variant: "success",
      });
      return true;
    } catch (error) {
      enqueueSnackbar(t("datasets:error.failedToDeleteFolder"), {
        variant: "error",
      });
      return false;
    }
  };

  return {
    folders,
    fetchFolders,
    createFolder,
    renameFolder,
    deleteFolderById,
  };
}
