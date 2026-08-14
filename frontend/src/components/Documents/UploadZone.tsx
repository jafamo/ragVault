import { useRef, useState } from "react";
import { useThemeStore } from "../../stores/themeStore";
import { getDocumentStatus, uploadDocument } from "../../services/api";

const ACCEPTED_EXTENSIONS =
  ".pdf,.docx,.odt,.xlsx,.ods,.csv,.md,.txt,.pptx,.ppt";

const STAGE_LABELS: Record<string, string> = {
  loading: "Leyendo",
  chunking: "Troceando",
  embedding: "Generando embeddings",
  indexing: "Indexando",
};

const POLL_INTERVAL_MS = 1000;

type UploadState =
  | { status: "idle" }
  | { status: "uploading"; uploadPercent: number }
  | { status: "parsing"; stage: string; parsePercent: number }
  | { status: "done"; filename: string; chunkCount: number }
  | { status: "error"; message: string };

export default function UploadZone() {
  const skin = useThemeStore((s) => s.skin);
  const [state, setState] = useState<UploadState>({ status: "idle" });
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function pollStatus(documentId: string, filename: string) {
    const interval = setInterval(async () => {
      try {
        const docStatus = await getDocumentStatus(documentId);
        if (docStatus.status === "done") {
          clearInterval(interval);
          setState({
            status: "done",
            filename,
            chunkCount: docStatus.chunk_count,
          });
        } else if (docStatus.status === "error") {
          clearInterval(interval);
          setState({
            status: "error",
            message: docStatus.error_message ?? "Error al procesar el documento",
          });
        } else {
          setState({
            status: "parsing",
            stage: docStatus.stage ?? "loading",
            parsePercent: docStatus.percent ?? 0,
          });
        }
      } catch (err) {
        clearInterval(interval);
        setState({
          status: "error",
          message: err instanceof Error ? err.message : "Error al consultar el progreso",
        });
      }
    }, POLL_INTERVAL_MS);
  }

  async function handleFile(file: File | undefined) {
    if (!file) return;
    setState({ status: "uploading", uploadPercent: 0 });
    try {
      const doc = await uploadDocument(file, (percent) => {
        setState({ status: "uploading", uploadPercent: percent });
      });
      setState({ status: "parsing", stage: "loading", parsePercent: 0 });
      pollStatus(doc.id, doc.filename);
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
        ? `$ uploading… ${state.uploadPercent}%`
        : `Subiendo… ${state.uploadPercent}%`
      : state.status === "parsing"
        ? skin === "terminal"
          ? `$ parsing (${state.stage})… ${state.parsePercent}%`
          : `${STAGE_LABELS[state.stage] ?? "Procesando"}… ${state.parsePercent}%`
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
        accept={ACCEPTED_EXTENSIONS}
        hidden
        onChange={(e) => handleFile(e.target.files?.[0])}
      />
      <div className="deposit-label">{label}</div>
      {state.status === "idle" && (
        <div className="deposit-sub">
          {skin === "terminal"
            ? "pdf · docx · odt · xlsx · ods · csv · md · txt · pptx · ppt"
            : "PDF · DOCX · ODT · XLSX · ODS · CSV · MD · TXT · PPTX · PPT"}
        </div>
      )}
    </div>
  );
}
