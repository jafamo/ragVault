import { useRef, useState } from "react";
import { useThemeStore } from "../../stores/themeStore";
import { uploadDocument } from "../../services/api";

type UploadState =
  | { status: "idle" }
  | { status: "uploading" }
  | { status: "done"; filename: string; chunkCount: number }
  | { status: "error"; message: string };

export default function UploadZone() {
  const skin = useThemeStore((s) => s.skin);
  const [state, setState] = useState<UploadState>({ status: "idle" });
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File | undefined) {
    if (!file) return;
    setState({ status: "uploading" });
    try {
      const doc = await uploadDocument(file);
      setState({ status: "done", filename: doc.filename, chunkCount: doc.chunk_count });
    } catch (err) {
      setState({
        status: "error",
        message: err instanceof Error ? err.message : "Error al subir el documento",
      });
    }
  }

  const label =
    state.status === "uploading"
      ? skin === "terminal"
        ? "$ ingesting…"
        : "Indexando…"
      : state.status === "done"
        ? `${state.filename} — ${state.chunkCount} chunks`
        : state.status === "error"
          ? state.message
          : skin === "terminal"
            ? "$ drop files --ingest"
            : "DEPOSITAR DOCUMENTOS";

  return (
    <div
      className="deposit"
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragOver(true);
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragOver(false);
        handleFile(e.dataTransfer.files[0]);
      }}
      style={{ cursor: "pointer", opacity: isDragOver ? 0.7 : 1 }}
      role="button"
      tabIndex={0}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        hidden
        onChange={(e) => handleFile(e.target.files?.[0])}
      />
      <div className="deposit-label">{label}</div>
      {state.status === "idle" && (
        <div className="deposit-sub">
          {skin === "terminal" ? "pdf" : "PDF"}
        </div>
      )}
    </div>
  );
}
