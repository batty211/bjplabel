const BJP_LABEL_VERSION = "0.4.8";
const BJP_LABEL_POSTCODE_URL = `/bjp_label/postcodes.json?v=${BJP_LABEL_VERSION}`;
const BJP_LABEL_PREVIEW_DELAY = 800;
const BJP_LABEL_SIZE_PRESETS = {
  "100x75": { width: 800, height: 600 },
  "100x150": { width: 800, height: 1200 },
};
const BJP_LABEL_INTEGRATION_DEFAULTS = {
  printer_backend: "niimbot",
  font: "NotoSansThai-Regular.ttf",
  device_id: "",
  host: "",
  port: 9100,
  label_size: "100x75",
};

// Lovelace card that parses pasted Thai address text, loads integration settings,
// requests preview images, and sends print jobs through the BJP Label services.
class BjpLabelCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("hui-generic-card-editor");
  }

  static getStubConfig() {
    return { title: "พิมพ์ฉลากลูกค้า" };
  }

  // Accept Lovelace card overrides and initialize local UI state for one card instance.
  setConfig(config) {
    this.rawConfig = { ...config };
    this.config = {
      title: "พิมพ์ฉลากลูกค้า",
      width: 640,
      height: 384,
      density: 3,
      rotate: 90,
      label_size: "100x75",
      port: 9100,
      show_label_size_selector: false,
      ...config,
    };
    this.integrationSettings = null;
    this.loadingSettings = false;
    this.settingsLoaded = false;
    this.settingsFailed = false;
    this.selectedLabelSize = this.config.label_size || "100x75";
    this.text = "";
    this.formattedText = "";
    this.formattedEdited = false;
    this.status = "";
    this.statusType = "ready";
    this.isPrinting = false;
    this.printLocked = false;
    this.isPreviewing = false;
    this.previewImage = "";
    this.previewSnapshot = null;
    this.previewError = false;
    this.previewRevision = 0;
    this.previewTimer = undefined;
    this.parsed = this.parseText("");
    this.formatted = this.parseFormattedText("");
    this.parseWarning = "";
    this.render();
    this.loadPostcodes();
  }

  // Home Assistant injects hass here; use it to fetch real integration settings
  // before we start generating previews. We wait here so preview orientation
  // uses the resolved printer backend instead of guessing Niimbot.
  set hass(hass) {
    this._hass = hass;
    this.loadIntegrationSettings();
    if (this.formatted?.valid && this.settingsLoaded && !this.previewImage && !this.isPreviewing && !this.previewError && this.previewTimer === undefined) {
      this.schedulePreview();
    }
  }

  getCardSize() {
    return 6;
  }

  render() {
    if (!this.config) return;

    const preset = this.currentPreviewPreset();
    const previewWidth = preset.width;
    const previewHeight = preset.height;
    const rotatePreview = this.shouldRotatePreview();
    const previewImageWidth = rotatePreview ? (previewHeight / previewWidth) * 100 : 100;
    const previewImageHeight = rotatePreview ? (previewWidth / previewHeight) * 100 : 100;
    const previewTransform = rotatePreview ? "translate(-50%, -50%) rotate(-90deg)" : "translate(-50%, -50%)";

    this.innerHTML = `
      <ha-card>
        <div class="card">
          <h2>${this.escape(this.config.title)}</h2>
          <label for="customer-text">วางข้อมูลลูกค้า</label>
          <textarea id="customer-text" rows="8" placeholder="วางชื่อ เบอร์โทร และที่อยู่ที่นี่">${this.escape(this.text)}</textarea>

          <div class="formatted">
            <label for="formatted-text">ตรวจสอบและแก้ไขก่อนพิมพ์</label>
            <div class="hint">บรรทัดแรกเป็นชื่อ บรรทัดที่สองเป็นเบอร์โทร และบรรทัดสุดท้ายเป็นรหัสไปรษณีย์</div>
            <textarea id="formatted-text" rows="7" placeholder="ข้อความที่จัดรูปแบบแล้วจะแสดงที่นี่">${this.escape(this.formattedText)}</textarea>
            <div class="warning" data-warning aria-live="polite"></div>
          </div>

          ${
            this.shouldShowLabelSizeSelector()
              ? `
            <div class="field">
              <label for="label-size">ขนาดฉลาก</label>
              <select id="label-size">
                <option value="100x75" ${this.selectedLabelSize === "100x75" ? "selected" : ""}>100 x 75 มม.</option>
                <option value="100x150" ${this.selectedLabelSize === "100x150" ? "selected" : ""}>100 x 150 มม.</option>
              </select>
            </div>
          `
              : ""
          }

          <section class="preview is-hidden" data-preview aria-hidden="true">
            <h3>ตัวอย่างฉลากก่อนพิมพ์</h3>
            <div class="preview-frame" style="aspect-ratio: ${previewWidth} / ${previewHeight}; --preview-image-width: ${previewImageWidth}%; --preview-image-height: ${previewImageHeight}%">
              <img data-preview-image alt="ตัวอย่างฉลากที่จะพิมพ์" hidden>
              <p data-preview-placeholder></p>
            </div>
            <button class="secondary retry" data-action="retry-preview" hidden>ลองสร้างตัวอย่างอีกครั้ง</button>
          </section>

          <div class="actions">
            <button class="primary" data-action="print">พิมพ์ฉลาก</button>
            <button class="secondary" data-action="clear">ล้างข้อมูล</button>
          </div>
          <p class="status" aria-live="polite"></p>
          <p class="version">BJP Label v${BJP_LABEL_VERSION}</p>
        </div>
      </ha-card>
      <style>
        .card {
          box-sizing: border-box;
          padding: 20px;
          color: var(--primary-text-color);
        }
        h2 {
          margin: 0 0 18px;
          font-size: 28px;
          line-height: 1.25;
        }
        label {
          display: block;
          margin-bottom: 8px;
          font-size: 21px;
          font-weight: 700;
        }
        textarea {
          box-sizing: border-box;
          width: 100%;
          min-height: 190px;
          padding: 14px;
          border: 2px solid var(--divider-color);
          border-radius: 10px;
          background: var(--card-background-color);
          color: var(--primary-text-color);
          font: inherit;
          font-size: 21px;
          line-height: 1.5;
          resize: vertical;
        }
        .formatted {
          margin-top: 18px;
        }
        .hint {
          margin: -2px 0 8px;
          font-size: 17px;
          color: var(--secondary-text-color);
          line-height: 1.4;
        }
        .warning {
          margin-top: 10px;
          color: var(--error-color);
          font-size: 18px;
          font-weight: 700;
          line-height: 1.4;
        }
        .field {
          margin-top: 18px;
        }
        select {
          box-sizing: border-box;
          width: 100%;
          min-height: 62px;
          padding: 12px 14px;
          border: 2px solid var(--divider-color);
          border-radius: 10px;
          background: var(--card-background-color);
          color: var(--primary-text-color);
          font: inherit;
          font-size: 21px;
        }
        .preview {
          margin-top: 18px;
        }
        .preview.is-hidden {
          display: none;
        }
        .preview h3 {
          margin: 0 0 10px;
          font-size: 21px;
        }
        .preview-frame {
          position: relative;
          display: flex;
          width: 100%;
          max-width: ${previewWidth}px;
          align-items: center;
          justify-content: center;
          overflow: hidden;
          border: 2px solid var(--divider-color);
          border-radius: 10px;
          background: #fff;
          margin: 0 auto;
        }
        .preview-frame img {
          position: absolute;
          inset: 50% auto auto 50%;
          display: block;
          width: var(--preview-image-width);
          height: var(--preview-image-height);
          max-width: none;
          max-height: none;
          object-fit: fill;
          transform: ${previewTransform};
          transform-origin: center;
        }
        .preview-frame img[hidden] {
          display: none;
        }
        .preview-frame p {
          margin: 20px;
          color: var(--secondary-text-color);
          font-size: 18px;
          text-align: center;
        }
        .retry {
          width: 100%;
          margin-top: 12px;
        }
        .retry[hidden] {
          display: none;
        }
        .actions {
          display: grid;
          grid-template-columns: 2fr 1fr;
          gap: 12px;
          margin-top: 18px;
        }
        button {
          min-height: 66px;
          border: 0;
          border-radius: 10px;
          padding: 12px 16px;
          font: inherit;
          font-size: 23px;
          font-weight: 800;
          cursor: pointer;
        }
        button:disabled {
          cursor: not-allowed;
          opacity: 0.45;
        }
        .primary {
          background: var(--primary-color);
          color: var(--text-primary-color);
        }
        .secondary {
          background: var(--secondary-background-color);
          color: var(--primary-text-color);
        }
        .status {
          min-height: 25px;
          margin: 14px 0 0;
          font-size: 18px;
          line-height: 1.4;
        }
        .status[data-type="printing"] { color: var(--primary-color); font-weight: 700; }
        .status[data-type="done"] { color: var(--success-color, #2e7d32); font-weight: 700; }
        .status[data-type="error"] { color: var(--error-color); font-weight: 700; }
        .version {
          margin: 8px 0 0;
          color: var(--secondary-text-color);
          font-size: 14px;
          text-align: right;
        }
        @media (max-width: 520px) {
          .card { padding: 16px; }
          .actions { grid-template-columns: 1fr; }
        }
      </style>
    `;

    this.querySelector("#customer-text").addEventListener("input", (event) => {
      this.text = event.target.value;
      this.resetPrintState();
      this.invalidatePreview();
      this.parsed = this.parseText(this.text);
      this.parseWarning = this.parsed.message;
      this.formattedText = this.formatParsed(this.parsed);
      this.formattedEdited = false;
      this.formatted = this.parseFormattedText(this.formattedText);
      this.querySelector("#formatted-text").value = this.formattedText;
      this.updateForm();
      this.schedulePreview();
    });
    this.querySelector("#formatted-text").addEventListener("input", (event) => {
      this.formattedText = event.target.value;
      this.formattedEdited = true;
      this.resetPrintState();
      this.invalidatePreview();
      this.parseWarning = "";
      this.formatted = this.parseFormattedText(this.formattedText);
      this.updateForm();
      this.schedulePreview();
    });
    const labelSize = this.querySelector("#label-size");
    if (labelSize) {
      labelSize.addEventListener("change", (event) => {
        this.selectedLabelSize = event.target.value;
        this.resetPrintState();
        this.invalidatePreview();
        this.render();
        this.schedulePreview();
      });
    }
    this.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => this.handleAction(button.dataset.action));
    });
    this.updateForm();
  }

  updateForm() {
    this.querySelector("[data-warning]").textContent = this.parseWarning || this.formatted.message;
    this.querySelector("#customer-text").disabled = this.isPrinting;
    this.querySelector("#formatted-text").disabled = this.isPrinting;
    const printButton = this.querySelector('[data-action="print"]');
    printButton.disabled = !this.previewSnapshot || this.isPreviewing || this.isPrinting || this.printLocked || Boolean(this.config.preview);
    printButton.textContent = this.isPrinting ? "กำลังพิมพ์..." : this.printLocked ? "พิมพ์แล้ว" : this.config.preview ? "โหมดดูตัวอย่างเท่านั้น" : "พิมพ์ฉลาก";
    const preview = this.querySelector("[data-preview]");
    const previewImage = this.querySelector("[data-preview-image]");
    const placeholder = this.querySelector("[data-preview-placeholder]");
    const retryButton = this.querySelector('[data-action="retry-preview"]');
    const hidePreview = !this.formatted.valid && !this.isPreviewing && !this.previewError;
    preview.classList.toggle("is-hidden", hidePreview);
    preview.setAttribute("aria-hidden", String(hidePreview));
    previewImage.hidden = !this.previewImage;
    if (this.previewImage) previewImage.src = this.previewImage;
    else previewImage.removeAttribute("src");
    placeholder.hidden = Boolean(this.previewImage);
    placeholder.textContent = this.loadingSettings
      ? "กำลังโหลดค่าการพิมพ์..."
      : this.settingsFailed
        ? "ยังโหลดค่าพรินเตอร์ไม่สำเร็จ"
        : this.isPreviewing
          ? "กำลังสร้างตัวอย่าง..."
          : this.previewError
            ? "ยังสร้างตัวอย่างไม่ได้ กรุณาลองอีกครั้ง"
            : "รอสร้างตัวอย่างฉลาก";
    retryButton.hidden = !this.previewError || this.isPreviewing;
    const status = this.querySelector(".status");
    status.textContent = this.status || (
      this.formatted.valid
        ? this.loadingSettings
          ? "กำลังโหลดค่าการตั้งค่าเครื่องพิมพ์"
          : this.settingsFailed
            ? "ยังโหลดค่าพรินเตอร์ไม่สำเร็จ กรุณาตรวจสอบ integration"
            : "กำลังเตรียมตัวอย่างก่อนพิมพ์"
        : "รอข้อมูล"
    );
    status.dataset.type = this.statusType;
  }

  async handleAction(action) {
    if (action === "clear") {
      this.invalidatePreview();
      this.text = "";
      this.formattedText = "";
      this.formattedEdited = false;
      this.status = "ล้างข้อมูลแล้ว";
      this.statusType = "ready";
      this.isPrinting = false;
      this.printLocked = false;
      this.parsed = this.parseText("");
      this.formatted = this.parseFormattedText("");
      this.parseWarning = "";
      this.render();
      return;
    }
    if (action === "retry-preview") {
      await this.generatePreview(this.previewRevision);
      return;
    }
    if (action !== "print" || !this.previewSnapshot || !this._hass || this.isPrinting || this.printLocked || this.config.preview) return;

    this.isPrinting = true;
    this.status = "กำลังเชื่อมต่อเครื่องพิมพ์...";
    this.statusType = "printing";
    this.updateForm();
    try {
      if (typeof requestAnimationFrame === "function") {
        await new Promise((resolve) => requestAnimationFrame(resolve));
      }
      const printRequest = this._hass.callService("bjp_label", "print_label", { ...this.previewSnapshot });
      this.status = "กำลังพิมพ์...";
      this.updateForm();
      await printRequest;
      this.status = "พิมพ์เสร็จแล้ว";
      this.statusType = "done";
      this.printLocked = true;
    } catch (error) {
      this.status = `พิมพ์ไม่สำเร็จ: ${this.friendlyError(error)}`;
      this.statusType = "error";
      this.printLocked = false;
    } finally {
      this.isPrinting = false;
    }
    this.updateForm();
  }

  resetPrintState() {
    this.status = "";
    this.statusType = "ready";
    this.printLocked = false;
  }

  invalidatePreview() {
    if (this.previewTimer !== undefined) clearTimeout(this.previewTimer);
    this.previewTimer = undefined;
    this.previewRevision = Number(this.previewRevision || 0) + 1;
    this.isPreviewing = false;
    this.previewImage = "";
    this.previewSnapshot = null;
    this.previewError = false;
  }

  schedulePreview(delay = BJP_LABEL_PREVIEW_DELAY) {
    if (this.previewTimer !== undefined) clearTimeout(this.previewTimer);
    this.previewTimer = undefined;
    // Preview must wait until the backend is resolved; otherwise Xprinter cards
    // can render with the Niimbot rotation by mistake.
    if (!this.formatted?.valid || !this._hass || !this.hasResolvedBackend() || this.loadingSettings || this.settingsFailed) return;
    const revision = this.previewRevision;
    this.previewTimer = setTimeout(() => {
      this.previewTimer = undefined;
      this.generatePreview(revision);
    }, delay);
  }

  // Preview uses the real backend selected in the integration and requests only an image response.
  async generatePreview(revision = this.previewRevision) {
    if (!this.formatted?.valid || !this._hass || !this.hasResolvedBackend() || this.settingsFailed || revision !== this.previewRevision || this.isPreviewing || this.isPrinting) return;
    const previewData = this.serviceData(true);
    this.isPreviewing = true;
    this.previewError = false;
    this.status = "กำลังสร้างตัวอย่างก่อนพิมพ์...";
    this.statusType = "printing";
    this.updateForm();
    try {
      const response = await this._hass.callService("bjp_label", "print_label", previewData, undefined, true, true);
      if (revision !== this.previewRevision) return;
      const image = response?.image || response?.response?.image;
      if (typeof image !== "string" || !image.startsWith("data:image/")) {
        throw new Error("ไม่ได้รับภาพตัวอย่างจากระบบพิมพ์");
      }
      this.previewImage = image;
      this.previewSnapshot = { ...previewData, preview: false };
      this.status = this.config.preview ? "ตัวอย่างพร้อมแล้ว (โหมดดูตัวอย่างเท่านั้น)" : "ตัวอย่างพร้อมแล้ว กรุณาตรวจสอบก่อนพิมพ์จริง";
      this.statusType = "done";
    } catch (error) {
      if (revision !== this.previewRevision) return;
      this.previewImage = "";
      this.previewSnapshot = null;
      this.previewError = true;
      this.status = `สร้างตัวอย่างไม่สำเร็จ: ${this.friendlyError(error)}`;
      this.statusType = "error";
    } finally {
      if (revision === this.previewRevision) {
        this.isPreviewing = false;
        this.updateForm();
      }
    }
  }

  async loadPostcodes() {
    if (BjpLabelCard.postcodeRows) return;
    try {
      if (!BjpLabelCard.postcodePromise) {
        BjpLabelCard.postcodePromise = fetch(BJP_LABEL_POSTCODE_URL).then((response) => {
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          return response.json();
        });
      }
      BjpLabelCard.postcodeRows = await BjpLabelCard.postcodePromise;
      if (this.text && !this.formattedEdited) {
        this.invalidatePreview();
        this.parsed = this.parseText(this.text);
        this.parseWarning = this.parsed.message;
        this.formattedText = this.formatParsed(this.parsed);
        this.formatted = this.parseFormattedText(this.formattedText);
        this.render();
        this.schedulePreview();
      }
    } catch (error) {
      BjpLabelCard.postcodePromise = undefined;
      console.warn("BJP Label: โหลดข้อมูลรหัสไปรษณีย์ไม่สำเร็จ", error);
    }
  }

  async loadIntegrationSettings() {
    if (!this._hass || this.loadingSettings || this.settingsLoaded) return;
    this.loadingSettings = true;
    this.settingsFailed = false;
    this.updateForm?.();
    try {
      const response = await this._hass.callService("bjp_label", "get_settings", {}, undefined, true, true);
      this.integrationSettings = {
        ...BJP_LABEL_INTEGRATION_DEFAULTS,
        ...(response?.response || response || {}),
      };
      if (!Object.prototype.hasOwnProperty.call(this.rawConfig || {}, "label_size")) {
        this.selectedLabelSize = this.integrationSettings.label_size || this.selectedLabelSize;
      }
      this.settingsLoaded = true;
      this.settingsFailed = false;
    } catch (error) {
      console.warn("BJP Label: โหลดค่าการตั้งค่าเครื่องพิมพ์ไม่สำเร็จ", error);
      this.integrationSettings = null;
      this.settingsLoaded = false;
      this.settingsFailed = true;
      this.status = "ยังโหลดค่าพรินเตอร์ไม่สำเร็จ กรุณาตรวจสอบ integration";
      this.statusType = "error";
    } finally {
      this.loadingSettings = false;
      this.updateForm?.();
      if (this.formatted?.valid && !this.settingsFailed && !this.previewImage && !this.isPreviewing && !this.previewError && this.previewTimer === undefined) {
        this.schedulePreview();
      }
    }
  }

  // Resolve the effective printer settings with this precedence:
  // card override -> integration config -> deterministic integration defaults.
  effectiveSettings() {
    const rawConfig = this.rawConfig || {};
    const integrationSettings = this.settingsLoaded
      ? (this.integrationSettings || BJP_LABEL_INTEGRATION_DEFAULTS)
      : BJP_LABEL_INTEGRATION_DEFAULTS;
    return {
      printer_backend: Object.prototype.hasOwnProperty.call(rawConfig, "printer_backend") ? this.config.printer_backend : integrationSettings.printer_backend,
      font: Object.prototype.hasOwnProperty.call(rawConfig, "font") ? this.config.font : integrationSettings.font,
      device_id: Object.prototype.hasOwnProperty.call(rawConfig, "device_id") ? this.config.device_id : integrationSettings.device_id,
      host: Object.prototype.hasOwnProperty.call(rawConfig, "host") ? this.config.host : integrationSettings.host,
      port: Object.prototype.hasOwnProperty.call(rawConfig, "port") ? Number(this.config.port) : Number(integrationSettings.port),
      label_size: Object.prototype.hasOwnProperty.call(rawConfig, "label_size") ? this.selectedLabelSize || this.config.label_size || "100x75" : this.selectedLabelSize || integrationSettings.label_size || "100x75",
    };
  }

  hasResolvedBackend() {
    const rawConfig = this.rawConfig || {};
    return Object.prototype.hasOwnProperty.call(rawConfig, "printer_backend") || this.settingsLoaded;
  }

  // Build the print/preview payload using the active backend's real settings.
  serviceData(preview = false) {
    const rawConfig = this.rawConfig || {};
    const settings = this.effectiveSettings();
    const data = {
      name: this.formatted.name,
      phone: this.formatted.phone,
      address: this.formatted.address,
      postal_code: this.formatted.postalCode,
      width: Number(this.config.width),
      height: Number(this.config.height),
      density: Number(this.config.density),
      preview: Boolean(preview),
    };
    data.printer_backend = settings.printer_backend;
    data.font = settings.font;
    if (this.isNiimbotBackend()) {
      data.rotate = Number(this.config.rotate);
      if (settings.device_id) data.device_id = settings.device_id;
    }
    if (this.isXprinterBackend()) {
      data.label_size = settings.label_size;
      data.host = settings.host;
      data.port = settings.port;
    }
    return data;
  }

  currentPreviewPreset() {
    if (this.isXprinterBackend()) {
      return BJP_LABEL_SIZE_PRESETS[this.effectiveSettings().label_size] || BJP_LABEL_SIZE_PRESETS["100x75"];
    }
    return {
      width: this.positiveNumber(this.config.width, 640),
      height: this.positiveNumber(this.config.height, 384),
    };
  }

  isXprinterBackend() {
    return this.hasResolvedBackend() && this.effectiveSettings().printer_backend === "xprinter_tspl";
  }

  isNiimbotBackend() {
    return this.hasResolvedBackend() && this.effectiveSettings().printer_backend === "niimbot";
  }

  shouldRotatePreview() {
    // Unresolved backend must not default to Niimbot; waiting is safer than rotating wrong.
    if (!this.hasResolvedBackend()) return false;
    return this.isNiimbotBackend();
  }

  shouldShowLabelSizeSelector() {
    return Boolean(this.config.show_label_size_selector) && this.isXprinterBackend();
  }

  positiveNumber(value, fallback) {
    const number = Number(value);
    return Number.isFinite(number) && number > 0 ? number : fallback;
  }

  formatParsed(parsed) {
    if (!parsed.valid) return "";
    return [parsed.name, parsed.phone, ...parsed.address.split("\n").filter(Boolean), parsed.postalCode].filter(Boolean).join("\n");
  }

  parseFormattedText(value) {
    const lines = String(value || "")
      .replace(/\r\n?/g, "\n")
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
    if (!lines.length) {
      return { valid: false, name: "", phone: "", address: "", postalCode: "", message: "กรุณาตรวจสอบข้อความก่อนพิมพ์" };
    }

    const name = (lines[0] || "").replace(/^#?\s*ส่ง\s*/, "").trim();
    const phone = lines[1] || "";
    const phoneDigits = phone.replace(/\D/g, "");
    let postalCode = "";
    let addressEnd = lines.length;
    if (lines.length > 2 && /^\d{5}$/.test(lines[lines.length - 1])) {
      postalCode = lines[lines.length - 1];
      addressEnd -= 1;
    }
    const address = lines.slice(2, addressEnd).join("\n");

    if (!name) {
      return { valid: false, name, phone, address, postalCode, message: "กรุณากรอกชื่อในบรรทัดแรก" };
    }
    if (phoneDigits.length < 9 || phoneDigits.length > 10) {
      return { valid: false, name, phone, address, postalCode, message: "กรุณาตรวจสอบเบอร์โทรในบรรทัดที่สอง" };
    }
    if (address.split("\n").filter(Boolean).length > 3) {
      return { valid: false, name, phone, address, postalCode, message: "ที่อยู่ต้องไม่เกิน 3 บรรทัด กรุณาจัดบรรทัดใหม่" };
    }
    return { valid: true, name, phone, address, postalCode, message: "" };
  }

  parseText(value) {
    const text = String(value || "")
      .replace(/\r\n?/g, "\n")
      .trim();
    if (!text) return { valid: false, name: "", phone: "", address: "", postalCode: "", message: "กรุณาวางข้อมูลลูกค้า" };

    const lines = text
      .split("\n")
      .map((line) => line.replace(/[ \t]+/g, " ").trim())
      .filter(Boolean);
    const phonePattern = /(?<!\d)(?:\+66|0)(?:[ \t-]*\d){8,9}(?!\d)/g;
    const phoneMatches = [];
    lines.forEach((line, lineIndex) => {
      for (const match of line.matchAll(phonePattern)) {
        phoneMatches.push({ raw: match[0].trim(), lineIndex, index: match.index });
      }
    });
    if (!phoneMatches.length) return { valid: false, name: "", phone: "", address: text, postalCode: "", message: "ไม่พบเบอร์โทรศัพท์ กรุณาตรวจสอบข้อความ" };
    const selectedPhone = phoneMatches[0];
    const phoneRaw = selectedPhone.raw;
    const phone = this.formatPhone(phoneRaw);
    const postalMatches = [];
    lines.forEach((line, lineIndex) => {
      for (const match of line.matchAll(/(?<!\d)\d{5}(?!\d)/g)) {
        const overlapsPhone = lineIndex === selectedPhone.lineIndex && match.index < selectedPhone.index + phoneRaw.length && selectedPhone.index < match.index + match[0].length;
        if (!overlapsPhone) postalMatches.push({ raw: match[0], lineIndex });
      }
    });
    const selectedPostal = postalMatches[postalMatches.length - 1];
    let postalCode = selectedPostal?.raw || "";

    const markers = ["โรงพยาบาล", "รพ.", "บริษัท", "หจก.", "ร้าน", "เลขที่", "หมู่บ้าน", "ถนน", "ซอย", "แขวง", "เขต", "ตำบล", "อำเภอ", "จังหวัด", "ต.", "อ.", "จ.", "ม."];
    const stopWords = new Set(["ส่ง", "บ้าน", "หมู่", "ถนน", "ซอย", "ตำบล", "อำเภอ", "จังหวัด", "โรงพยาบาล", "บริษัท", "ร้าน"]);
    const candidates = [];
    lines.forEach((original, lineIndex) => {
      if (/^(?:ที่อยู่ผู้รับ|ข้อมูลผู้รับ)\s*:?$/.test(original)) return;
      let line = original.replace(/^\s*#?\s*ส่ง\s*/, "");
      const positions = markers.map((marker) => line.indexOf(marker)).filter((position) => position >= 0);
      const boundary = positions.length ? Math.min(...positions) : line.length;
      let segment = line.slice(0, boundary).replace(/^[ ,:-]+|[ ,:-]+$/g, "");
      if (/\d/.test(segment)) {
        const localPhone = segment.search(/(?:\+66|0)(?:[\s-]*\d){8,9}/);
        if (localPhone < 0) return;
        segment = segment.slice(0, localPhone).trim();
      }
      const titleMatch = segment.match(/^(นางสาว|นาย|นาง|คุณ)\s*/);
      const title = titleMatch ? titleMatch[1] : "";
      const namePart = titleMatch ? segment.slice(titleMatch[0].length) : segment;
      const words = [...namePart.matchAll(/[ก-๙]+/g)];
      if (words.length < 2) return;
      const first = words[0][0];
      const second = words[1][0];
      if (first.length < 2 || second.length < 2 || stopWords.has(first) || stopWords.has(second)) return;
      let score = 5 + (title ? 6 : 0) + (positions.length ? 0 : 3) + (lineIndex === selectedPhone.lineIndex ? 2 : 0) + (words.length === 2 ? 2 : 0);
      const namePattern = title ? `${title}\\s*${first}\\s+${second}` : `${first}\\s+${second}`;
      candidates.push({ name: `${title}${first} ${second}`, namePattern, lineIndex, score });
    });

    if (!candidates.length) {
      const addressStart = /(?<!\d)\d+(?:[/\-]\d+)*|(?:เลขที่|หมู่บ้าน|ถนน|ซอย|แขวง|เขต|ตำบล|อำเภอ|จังหวัด|ต\.|อ\.|จ\.|ม\.)/;
      lines.some((original, lineIndex) => {
        if (/^(?:ที่อยู่ผู้รับ|ข้อมูลผู้รับ)\s*:?$/.test(original)) return false;
        let cleaned = original.replace(/^\s*#?\s*ส่ง\s*/, "");
        if (lineIndex === selectedPhone.lineIndex) cleaned = cleaned.replace(phoneRaw, " ");
        if (postalCode && lineIndex === selectedPostal?.lineIndex) {
          cleaned = cleaned.replace(new RegExp(`(?<!\\d)${postalCode}(?!\\d)`), " ");
        }
        cleaned = cleaned
          .replace(/(?:^|\s)(?:โทร(?:ศัพท์)?|เบอร์(?:โทรศัพท์)?)\s*:?\s*/g, " ")
          .replace(/^[\s,:#-]+|[\s,:#-]+$/g, "")
          .replace(/\s+/g, " ");
        const boundary = cleaned.search(addressStart);
        const name = cleaned.slice(0, boundary < 0 ? cleaned.length : boundary).trim();
        if (name.length < 2 || !/[A-Za-zก-๙]/.test(name)) return false;
        candidates.push({ name, lineIndex, score: 1, fallback: true });
        return true;
      });
    }
    if (!candidates.length) return { valid: false, name: "", phone, address: text, postalCode, message: "ไม่พบชื่อผู้รับ กรุณาตรวจสอบข้อความ" };
    candidates.sort((a, b) => b.score - a.score || a.lineIndex - b.lineIndex);
    const selected = candidates[0];
    const addressLines = lines
      .map((line, index) => {
        if (/^(?:ที่อยู่ผู้รับ|ข้อมูลผู้รับ)\s*:?$/.test(line)) return "";
        let cleaned = line;
        if (index === selected.lineIndex) {
          cleaned = cleaned.replace(/^\s*#?\s*ส่ง\s*/, "");
          cleaned = selected.fallback ? cleaned.replace(selected.name, " ") : cleaned.replace(new RegExp(selected.namePattern), " ");
        }
        if (index === selectedPhone.lineIndex) cleaned = cleaned.replace(phoneRaw, " ");
        cleaned = cleaned.replace(/(?:^|\s)(?:โทร(?:ศัพท์)?|เบอร์(?:โทรศัพท์)?)\s*:?\s*/g, " ");
        if (postalCode && index === selectedPostal?.lineIndex) cleaned = cleaned.replace(new RegExp(`(?<!\\d)${postalCode}(?!\\d)`), " ");
        return cleaned.replace(/^[\s,:#-]+|[\s,:#-]+$/g, "").replace(/\s+/g, " ");
      })
      .filter(Boolean);
    const address = this.wrapAddressLines(addressLines);
    const warnings = [];
    if (phoneMatches.length > 1) warnings.push("พบหลายเบอร์โทร กรุณาตรวจสอบ");
    if (candidates.length > 1 && candidates[1].score >= selected.score - 1) warnings.push("พบชื่อที่เป็นไปได้หลายรายการ กรุณาตรวจสอบ");
    if (!postalCode) {
      const possiblePostcodes = this.lookupPostcodes(address);
      if (possiblePostcodes.length === 1) {
        postalCode = possiblePostcodes[0];
        warnings.push(`เติมรหัสไปรษณีย์ ${postalCode} ให้อัตโนมัติ กรุณาตรวจสอบ`);
      } else if (possiblePostcodes.length > 1) {
        const preview = possiblePostcodes.slice(0, 4).join(", ");
        const suffix = possiblePostcodes.length > 4 ? "…" : "";
        warnings.push(`พบรหัสไปรษณีย์ได้หลายค่า: ${preview}${suffix} กรุณาเลือกและกรอกเอง`);
      } else if (BjpLabelCard.postcodeRows) {
        warnings.push("ไม่พบรหัสไปรษณีย์ กรุณากรอกเอง");
      }
    }
    return { valid: true, name: selected.name, phone, address, postalCode, message: warnings.join(" • ") };
  }

  wrapAddressLines(lines, width = 34, maxLines = 3) {
    const wrapped = [];
    for (const sourceLine of lines) {
      const chunks = sourceLine
        .split(/(?<=,)\s*/)
        .map((chunk) => chunk.trim())
        .filter(Boolean);
      for (const chunk of chunks) {
        let current = "";
        for (const word of chunk.split(/\s+/)) {
          const proposed = `${current} ${word}`.trim();
          if (current && proposed.length > width) {
            wrapped.push(current);
            current = word;
          } else {
            current = proposed;
          }
        }
        if (current) wrapped.push(current);
      }
    }
    if (wrapped.length === 1) {
      const words = wrapped[0].split(/\s+/);
      if (words.length > 1) {
        let splitAt = 1;
        let smallestDifference = Infinity;
        for (let index = 1; index < words.length; index += 1) {
          const difference = Math.abs(words.slice(0, index).join(" ").length - words.slice(index).join(" ").length);
          if (difference < smallestDifference) {
            splitAt = index;
            smallestDifference = difference;
          }
        }
        wrapped.splice(0, 1, words.slice(0, splitAt).join(" "), words.slice(splitAt).join(" "));
      }
    }
    while (wrapped.length > maxLines) {
      let mergeAt = 0;
      for (let index = 1; index < wrapped.length - 1; index += 1) {
        if (wrapped[index].length + wrapped[index + 1].length < wrapped[mergeAt].length + wrapped[mergeAt + 1].length) mergeAt = index;
      }
      wrapped.splice(mergeAt, 2, `${wrapped[mergeAt]} ${wrapped[mergeAt + 1]}`.trim());
    }
    return wrapped.join("\n");
  }

  lookupPostcodes(address) {
    const rows = BjpLabelCard.postcodeRows || [];
    const text = this.normalizeLocation(address);
    if (!text || !rows.length) return [];

    const extract = (pattern) => text.match(pattern)?.[1]?.replace(/[ .]+$/g, "") || "";
    const province = extract(/(?:จังหวัด|จ\.)\s*([^\s,]+)/);
    const district = extract(/(?:อำเภอ|อ\.|เขต)\s*([^\s,]+)/);
    const subdistrict = extract(/(?:ตำบล|ต\.|แขวง)\s*([^\s,]+)/);
    let matches = rows.filter(
      (row) => (!province || this.locationMatches(province, row.p, "province")) && (!district || this.locationMatches(district, row.d, "district")) && (!subdistrict || this.locationMatches(subdistrict, row.s, "subdistrict")),
    );

    if (!matches.length && subdistrict && (district || province)) {
      matches = rows.filter((row) => (!province || this.locationMatches(province, row.p, "province")) && (!district || this.locationMatches(district, row.d, "district")));
    }

    if (!province && !district && !subdistrict) {
      matches = rows.filter(
        (row) =>
          [
            [row.s, "subdistrict"],
            [row.d, "district"],
            [row.p, "province"],
          ].filter(([name, kind]) => {
            const plain = this.plainLocation(name, kind);
            return plain.length >= 3 && text.includes(plain);
          }).length >= 2,
      );
    }
    return [...new Set(matches.map((row) => String(row.z)))];
  }

  normalizeLocation(value) {
    return String(value || "")
      .replaceAll("กรุงเทพฯ", "กรุงเทพมหานคร")
      .replace(/\s+/g, " ")
      .trim();
  }

  plainLocation(value, kind) {
    const prefixes = {
      province: ["จังหวัด"],
      district: ["อำเภอ", "เขต"],
      subdistrict: ["ตำบล", "แขวง"],
    }[kind];
    let result = String(value || "");
    for (const prefix of prefixes) {
      if (result.startsWith(prefix)) result = result.slice(prefix.length);
    }
    return result;
  }

  locationMatches(query, actual, kind) {
    const plainQuery = this.plainLocation(query, kind);
    const plainActual = this.plainLocation(actual, kind);
    return plainQuery === plainActual || (kind === "district" && plainQuery === "เมือง" && plainActual.startsWith("เมือง"));
  }

  formatPhone(raw) {
    let digits = raw.replace(/\D/g, "");
    if (digits.startsWith("66")) digits = `0${digits.slice(2)}`;
    if (digits.length === 10) return `${digits.slice(0, 3)}-${digits.slice(3, 6)}-${digits.slice(6)}`;
    if (digits.length === 9 && digits.startsWith("02")) return `${digits.slice(0, 2)}-${digits.slice(2, 5)}-${digits.slice(5)}`;
    if (digits.length === 9) return `${digits.slice(0, 3)}-${digits.slice(3, 6)}-${digits.slice(6)}`;
    return raw;
  }

  friendlyError(error) {
    const message = error?.message || String(error || "เกิดข้อผิดพลาด");
    return message.length > 160 ? "กรุณาตรวจสอบข้อมูลและเครื่องพิมพ์" : message;
  }

  escape(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }
}

if (!customElements.get || !customElements.get("bjp-label-card")) {
  customElements.define("bjp-label-card", BjpLabelCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "bjp-label-card")) {
  window.customCards.push({
    type: "bjp-label-card",
    name: "BJP Label",
    description: "วางข้อมูลลูกค้า ตรวจสอบ และพิมพ์ฉลากภาษาไทย",
  });
}
