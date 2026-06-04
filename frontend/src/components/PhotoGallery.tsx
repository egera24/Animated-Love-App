import { ChangeEvent, useCallback, useEffect, useState } from "react";
import {
  fetchMedia,
  MediaItem,
  uploadMedia,
} from "../api/client";
import "./photo-gallery.css";

export default function PhotoGallery() {
  const [items, setItems] = useState<MediaItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [index, setIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploaderName, setUploaderName] = useState("Edina");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (p: number, append = false) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchMedia(p, 20);
      setItems((prev) => (append ? [...prev, ...data.items] : data.items));
      setTotal(data.total);
      if (!append) setIndex(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Hiba.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(1, false);
  }, [load]);

  const current = items[index];

  async function onFileChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await uploadMedia(file, uploaderName);
      setPage(1);
      await load(1, false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Feltöltés sikertelen.");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  function prev() {
    setIndex((i) => (i > 0 ? i - 1 : items.length - 1));
  }

  function next() {
    setIndex((i) => (i < items.length - 1 ? i + 1 : 0));
  }

  return (
    <div className="photo-gallery">
      <div className="photo-gallery__upload">
        <label>
          Feltöltő neve
          <input
            value={uploaderName}
            onChange={(e) => setUploaderName(e.target.value)}
            placeholder="Edina"
          />
        </label>
        <label className="upload-btn">
          {uploading ? "Feltöltés…" : "Kép feltöltése"}
          <input
            type="file"
            accept="image/jpeg,image/png,image/gif,image/webp"
            onChange={onFileChange}
            disabled={uploading}
            hidden
          />
        </label>
      </div>

      {error && <p className="error-text">{error}</p>}
      {loading && <p className="muted">Betöltés…</p>}

      {!loading && items.length === 0 && (
        <p className="muted">Még nincs kép — tölts fel egyet!</p>
      )}

      {current && (
        <div className="photo-carousel">
          <button type="button" className="nav-btn" onClick={prev} aria-label="Előző">
            ‹
          </button>
          <figure>
            <img src={current.url} alt={current.original_name} />
            <figcaption>
              {current.original_name} · {current.uploaded_by}
            </figcaption>
          </figure>
          <button type="button" className="nav-btn" onClick={next} aria-label="Következő">
            ›
          </button>
        </div>
      )}

      {items.length > 0 && (
        <p className="photo-count">
          {index + 1} / {items.length}
          {total > items.length && ` (${total} összesen)`}
        </p>
      )}

      {total > items.length && (
        <button
          type="button"
          className="load-more"
          onClick={() => {
            const next = page + 1;
            setPage(next);
            void load(next, true);
          }}
        >
          Több betöltése ({items.length}/{total})
        </button>
      )}
    </div>
  );
}
