import { useComponentDownloadState } from "../../models/model/ComponentDownloadControl";
import {
  useCredentialStatuses,
  getComponentCredentialState,
} from "../../credentials/credentialStatus";

/**
 * Shared download/credential gating for explorer/converter tool cards, mirroring
 * how model rows in the models side bar are gated. A tool is blocked when its
 * dataset columns don't fit it (`disabled`) OR it requires an authenticated
 * credential (`locked`) OR it requires a download that has not finished.
 *
 * Returns the gate state plus a `resolve` helper that dispatches a click to the
 * right handler: credentials dialog, download start, or the normal "use" action.
 */
export const useToolGate = (tool) => {
  const requiresDownload = Boolean(tool?.metadata?.requires_download);
  const { downloaded, downloading } = useComponentDownloadState(
    tool || { name: "" },
  );
  const { statuses, loaded } = useCredentialStatuses();
  const { locked, requiredPlatforms } = getComponentCredentialState(
    tool || {},
    statuses,
    loaded,
  );
  const ready = !locked && (!requiresDownload || (downloaded && !downloading));
  const blocked = Boolean(tool?.disabled) || !ready;
  const gated = locked || (requiresDownload && !(downloaded && !downloading));

  const resolve = ({ onUse, onDownload, onNeedsCredentials }) => {
    if (downloading) return;
    if (locked) {
      onNeedsCredentials?.();
      return;
    }
    if (requiresDownload && !(downloaded && !downloading)) {
      onDownload?.();
      return;
    }
    if (tool?.disabled) return;
    onUse?.();
  };

  return {
    requiresDownload,
    downloaded,
    downloading,
    locked,
    requiredPlatforms,
    ready,
    blocked,
    gated,
    resolve,
  };
};
