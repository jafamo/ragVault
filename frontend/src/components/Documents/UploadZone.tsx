import { useThemeStore } from "../../stores/themeStore";

export default function UploadZone() {
  const skin = useThemeStore((s) => s.skin);

  return (
    <div className="deposit">
      <div className="deposit-label">
        {skin === "terminal" ? "$ drop files --ingest" : "DEPOSITAR DOCUMENTOS"}
      </div>
      <div className="deposit-sub">
        {skin === "terminal" ? "pdf · docx · xlsx · md · txt" : "PDF · DOCX · XLSX · MD · TXT"}
      </div>
    </div>
  );
}
