import { ChangeEvent, DragEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";

const SUBJECTS = ["physics", "chemistry", "maths", "biology", "english", "other"];

export default function Upload() {
  const [subject, setSubject] = useState("physics");
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setUploading(true);
    setError("");
    try {
      for (const file of Array.from(files)) {
        const form = new FormData();
        form.append("file", file);
        form.append("subject", subject);
        await api.post("/documents/upload", form, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      }
      navigate("/");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Upload failed — check the file is a valid PDF");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <div className="eyebrow mb-2">Upload</div>
      <h1 className="text-3xl mb-8">Bring in a chapter</h1>

      <div className="mb-6">
        <label className="text-sm text-muted block mb-2">Subject</label>
        <div className="flex gap-2 flex-wrap">
          {SUBJECTS.map((s) => (
            <button
              key={s}
              onClick={() => setSubject(s)}
              className={`px-4 py-1.5 rounded-full text-sm capitalize border transition-colors ${
                subject === s
                  ? "bg-marigold text-ink border-marigold"
                  : "border-ink-border text-muted hover:text-parchment"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div
        onDragOver={(e: DragEvent) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e: DragEvent) => {
          e.preventDefault();
          setDragOver(false);
          handleFiles(e.dataTransfer.files);
        }}
        className={`card p-14 text-center transition-colors ${
          dragOver ? "border-marigold" : ""
        }`}
      >
        <p className="mb-4 text-muted">
          Drag and drop one or more PDFs here, or
        </p>
        <label className="btn-primary cursor-pointer inline-block">
          {uploading ? "Uploading…" : "Choose files"}
          <input
            type="file"
            accept="application/pdf"
            multiple
            className="hidden"
            disabled={uploading}
            onChange={(e: ChangeEvent<HTMLInputElement>) => handleFiles(e.target.files)}
          />
        </label>
        <p className="text-xs text-muted mt-4">
          Scanned/image PDFs are OCR'd automatically.
        </p>
      </div>

      {error && <p className="text-rose text-sm mt-4">{error}</p>}
    </div>
  );
}
