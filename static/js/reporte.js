/**
 * reporte.js — SabanaLimpia
 *
 * Responsibilities (T-17 + T-18):
 *  1. Geolocation: capture lat/lng via navigator.geolocation and inject into
 *     hidden form fields. Shows real-time status to the user.
 *  2. Photo preview: display a thumbnail before the form is submitted.
 *  3. Client-side compression (T-18): resize and re-encode the selected image
 *     via Canvas API so no upload exceeds 2 MB, without any external library.
 *
 * Design principles:
 *  - No dependencies. Pure browser APIs only.
 *  - Fails gracefully: if geolocation is denied, the server-side form
 *    validation catches the empty coordinate fields and shows an error.
 *  - All DOM queries are guarded with null checks so the script can be
 *    included in base.html without throwing on pages that lack the form.
 */

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const COMPRESSION = {
  MAX_WIDTH_PX: 1280,
  MAX_HEIGHT_PX: 1280,
  QUALITY: 0.82,        // 0–1 JPEG quality. 0.82 ≈ high visual quality, ~60–70% size reduction
  MAX_SIZE_BYTES: 2 * 1024 * 1024,  // 2 MB
  OUTPUT_MIME: "image/jpeg",
};

const GEO_OPTIONS = {
  enableHighAccuracy: true,
  timeout: 12_000,       // 12 seconds
  maximumAge: 60_000,    // Accept a cached position up to 1 minute old
};

// ---------------------------------------------------------------------------
// Geolocation
// ---------------------------------------------------------------------------

/**
 * Requests the device's current position and populates the hidden coordinate
 * fields. Updates the button label to reflect progress.
 *
 * @param {HTMLElement} btn        - The "Usar mi ubicación" button
 * @param {HTMLInputElement} latInput
 * @param {HTMLInputElement} lngInput
 * @param {HTMLElement} statusEl   - Element that shows status text to the user
 */
function requestGeolocation(btn, latInput, lngInput, statusEl) {
  if (!("geolocation" in navigator)) {
    showGeoStatus(statusEl, "error", "Tu navegador no soporta geolocalización.");
    return;
  }

  setButtonState(btn, "loading");
  showGeoStatus(statusEl, "loading", "Obteniendo ubicación…");

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const { latitude, longitude, accuracy } = position.coords;
      latInput.value = latitude.toFixed(7);
      lngInput.value = longitude.toFixed(7);

      const accuracyText =
        accuracy < 50 ? "Alta precisión" : accuracy < 150 ? "Precisión media" : "Baja precisión";

      showGeoStatus(
        statusEl,
        "success",
        `Ubicación capturada · ${accuracyText} (±${Math.round(accuracy)} m)`
      );
      setButtonState(btn, "success");
    },
    (error) => {
      const messages = {
        1: "Permiso denegado. Activa la ubicación en la configuración de tu navegador.",
        2: "No se pudo determinar la ubicación. Verifica tu señal GPS o Wi-Fi.",
        3: "La solicitud tardó demasiado. Inténtalo de nuevo.",
      };
      showGeoStatus(statusEl, "error", messages[error.code] ?? "Error desconocido de geolocalización.");
      setButtonState(btn, "idle");
    },
    GEO_OPTIONS
  );
}

/** @param {'idle'|'loading'|'success'} state */
function setButtonState(btn, state) {
  const labels = {
    idle: "📍 Usar mi ubicación",
    loading: "⏳ Obteniendo ubicación…",
    success: "✅ Ubicación capturada",
  };
  btn.textContent = labels[state] ?? labels.idle;
  btn.disabled = state === "loading";
  btn.dataset.state = state;
}

/** @param {'loading'|'success'|'error'} type */
function showGeoStatus(el, type, text) {
  if (!el) return;
  el.textContent = text;
  el.className = `geo-status geo-status--${type}`;
}

// ---------------------------------------------------------------------------
// Photo preview
// ---------------------------------------------------------------------------

/**
 * Reads the selected file and renders a thumbnail preview.
 * Also triggers compression and updates the hidden file input.
 *
 * @param {File} file
 * @param {HTMLElement} previewContainer
 * @param {HTMLInputElement} fileInput  - Original <input type="file">
 */
async function handlePhotoSelected(file, previewContainer, fileInput) {
  if (!file || !file.type.startsWith("image/")) return;

  // Show the original as an optimistic preview while we compress
  const objectUrl = URL.createObjectURL(file);
  renderPreview(previewContainer, objectUrl, file.name, file.size);

  try {
    const compressed = await compressImage(file);
    URL.revokeObjectURL(objectUrl);

    if (compressed !== file) {
      // Replace the file in the input with the compressed version
      replaceFileInInput(fileInput, compressed);
      // Update preview with compressed blob
      const compressedUrl = URL.createObjectURL(compressed);
      renderPreview(previewContainer, compressedUrl, file.name, compressed.size, {
        original: file.size,
      });
    }
  } catch (err) {
    console.warn("[SabanaLimpia] Photo compression failed, using original:", err);
    // Non-fatal: the server enforces a 5 MB hard cap as fallback
  }
}

/**
 * @param {HTMLElement} container
 * @param {string} src
 * @param {string} fileName
 * @param {number} sizeBytes
 * @param {{ original?: number }} [meta]
 */
function renderPreview(container, src, fileName, sizeBytes, meta = {}) {
  const sizeKb = (sizeBytes / 1024).toFixed(0);
  const originalText =
    meta.original
      ? ` (reducida de ${(meta.original / 1024).toFixed(0)} KB)`
      : "";

  container.innerHTML = `
    <div class="photo-preview">
      <img src="${src}" alt="Vista previa de ${escapeHtml(fileName)}" class="photo-preview__img" />
      <p class="photo-preview__meta">${escapeHtml(fileName)} · ${sizeKb} KB${originalText}</p>
    </div>
  `;
  container.hidden = false;
}

// ---------------------------------------------------------------------------
// Client-side image compression (T-18)
// ---------------------------------------------------------------------------

/**
 * Compresses an image File using the Canvas API.
 * Returns the original file unchanged if it is already below MAX_SIZE_BYTES
 * or if the image type is not re-encodable (e.g. GIF, BMP).
 *
 * @param {File} file
 * @returns {Promise<File>}
 */
async function compressImage(file) {
  // Skip compression if already small enough
  if (file.size <= COMPRESSION.MAX_SIZE_BYTES) return file;

  const bitmap = await createImageBitmap(file);

  const { width, height } = calculateDimensions(
    bitmap.width,
    bitmap.height,
    COMPRESSION.MAX_WIDTH_PX,
    COMPRESSION.MAX_HEIGHT_PX
  );

  const canvas = new OffscreenCanvas(width, height);
  const ctx = canvas.getContext("2d");
  ctx.drawImage(bitmap, 0, 0, width, height);
  bitmap.close();

  const blob = await canvas.convertToBlob({
    type: COMPRESSION.OUTPUT_MIME,
    quality: COMPRESSION.QUALITY,
  });

  // If compression made it larger (rare with PNG→JPEG), keep the original
  if (blob.size >= file.size) return file;

  return new File([blob], ensureJpegExtension(file.name), {
    type: COMPRESSION.OUTPUT_MIME,
    lastModified: Date.now(),
  });
}

/**
 * Calculates output dimensions preserving aspect ratio within the given bounds.
 */
function calculateDimensions(srcW, srcH, maxW, maxH) {
  if (srcW <= maxW && srcH <= maxH) return { width: srcW, height: srcH };

  const ratio = Math.min(maxW / srcW, maxH / srcH);
  return {
    width: Math.round(srcW * ratio),
    height: Math.round(srcH * ratio),
  };
}

/** Replaces the file inside an <input type="file"> via DataTransfer. */
function replaceFileInInput(input, newFile) {
  try {
    const dt = new DataTransfer();
    dt.items.add(newFile);
    input.files = dt.files;
  } catch {
    // DataTransfer is not supported in all environments (e.g. Safari < 14.1).
    // Silent fail: the server-side size limit acts as safety net.
  }
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function ensureJpegExtension(name) {
  return name.replace(/\.[^.]+$/, "") + ".jpg";
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ---------------------------------------------------------------------------
// Bootstrap — wire up DOM elements on DOMContentLoaded
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("reporte-form");
  if (!form) return; // Script included globally; exit gracefully if form absent

  const geoBtn     = form.querySelector("[data-action='get-location']");
  const latInput   = form.querySelector("[name='latitud']");
  const lngInput   = form.querySelector("[name='longitud']");
  const geoStatus  = form.querySelector("[data-geo-status]");
  const photoInput = form.querySelector("[name='foto']");
  const previewBox = form.querySelector("[data-photo-preview]");

  // Geolocation
  if (geoBtn && latInput && lngInput) {
    geoBtn.addEventListener("click", () => {
      requestGeolocation(geoBtn, latInput, lngInput, geoStatus);
    });
  }

  // Photo preview + compression
  if (photoInput && previewBox) {
    photoInput.addEventListener("change", () => {
      const file = photoInput.files[0];
      if (file) handlePhotoSelected(file, previewBox, photoInput);
    });
  }

  // Prevent double-submit
  form.addEventListener("submit", () => {
    const submitBtn = form.querySelector("[type='submit']");
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Enviando reporte…";
    }
  });
});