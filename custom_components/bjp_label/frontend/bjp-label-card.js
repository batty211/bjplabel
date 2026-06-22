const BJP_LABEL_VERSION = "0.3.0";
const BJP_LABEL_POSTCODE_URL = `/bjp_label/postcodes.json?v=${BJP_LABEL_VERSION}`;

class BjpLabelCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("hui-generic-card-editor");
  }

  static getStubConfig() {
    return { title: "พิมพ์ฉลากลูกค้า" };
  }

  setConfig(config) {
    this.config = {
      title: "พิมพ์ฉลากลูกค้า",
      width: 640,
      height: 384,
      density: 3,
      rotate: 90,
      ...config,
    };
    this.text = "";
    this.formattedText = "";
    this.formattedEdited = false;
    this.status = "";
    this.statusType = "ready";
    this.isPrinting = false;
    this.printLocked = false;
    this.parsed = this.parseText("");
    this.formatted = this.parseFormattedText("");
    this.parseWarning = "";
    this.render();
    this.loadPostcodes();
  }

  set hass(hass) {
    this._hass = hass;
  }

  getCardSize() {
    return 6;
  }

  render() {
    if (!this.config) return;

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

          <div class="actions">
            <button class="primary" data-action="print">พิมพ์</button>
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
      this.parsed = this.parseText(this.text);
      this.parseWarning = this.parsed.message;
      this.formattedText = this.formatParsed(this.parsed);
      this.formattedEdited = false;
      this.formatted = this.parseFormattedText(this.formattedText);
      this.querySelector("#formatted-text").value = this.formattedText;
      this.updateForm();
    });
    this.querySelector("#formatted-text").addEventListener("input", (event) => {
      this.formattedText = event.target.value;
      this.formattedEdited = true;
      this.resetPrintState();
      this.parseWarning = "";
      this.formatted = this.parseFormattedText(this.formattedText);
      this.updateForm();
    });
    this.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => this.handleAction(button.dataset.action));
    });
    this.updateForm();
  }

  updateForm() {
    this.querySelector("[data-warning]").textContent = this.parseWarning || this.formatted.message;
    const printButton = this.querySelector('[data-action="print"]');
    printButton.disabled = !this.formatted.valid || this.isPrinting || this.printLocked;
    printButton.textContent = this.isPrinting ? "กำลังพิมพ์..." : this.printLocked ? "พิมพ์แล้ว" : "พิมพ์";
    const status = this.querySelector(".status");
    status.textContent = this.status || (this.formatted.valid ? "พร้อมพิมพ์" : "รอข้อมูล");
    status.dataset.type = this.statusType;
  }

  async handleAction(action) {
    if (action === "clear") {
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
    if (!this.formatted.valid || !this._hass || this.isPrinting || this.printLocked) return;

    this.isPrinting = true;
    this.status = "กำลังเชื่อมต่อเครื่องพิมพ์...";
    this.statusType = "printing";
    this.updateForm();
    try {
      if (typeof requestAnimationFrame === "function") {
        await new Promise((resolve) => requestAnimationFrame(resolve));
      }
      const printRequest = this._hass.callService("bjp_label", "print_label", this.serviceData());
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
        this.parsed = this.parseText(this.text);
        this.parseWarning = this.parsed.message;
        this.formattedText = this.formatParsed(this.parsed);
        this.formatted = this.parseFormattedText(this.formattedText);
        this.render();
      }
    } catch (error) {
      BjpLabelCard.postcodePromise = undefined;
      console.warn("BJP Label: โหลดข้อมูลรหัสไปรษณีย์ไม่สำเร็จ", error);
    }
  }

  serviceData() {
    const data = {
      name: this.formatted.name,
      phone: this.formatted.phone,
      address: this.formatted.address,
      postal_code: this.formatted.postalCode,
      width: Number(this.config.width),
      height: Number(this.config.height),
      density: Number(this.config.density),
      rotate: Number(this.config.rotate),
      preview: Boolean(this.config.preview),
    };
    if (this.config.device_id) data.device_id = this.config.device_id;
    if (this.config.font) data.font = this.config.font;
    return data;
  }

  formatParsed(parsed) {
    if (!parsed.valid) return "";
    return [
      `ส่ง ${parsed.name}`,
      parsed.phone,
      ...parsed.address.split("\n").filter(Boolean),
      parsed.postalCode,
    ].filter(Boolean).join("\n");
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
    return { valid: true, name, phone, address, postalCode, message: "" };
  }

  parseText(value) {
    const text = String(value || "").replace(/\r\n?/g, "\n").trim();
    if (!text) return { valid: false, name: "", phone: "", address: "", postalCode: "", message: "กรุณาวางข้อมูลลูกค้า" };

    const phoneMatches = [...text.matchAll(/(?:\+66|0)(?:[\s-]*\d){8,9}/g)];
    if (!phoneMatches.length) return { valid: false, name: "", phone: "", address: text, postalCode: "", message: "ไม่พบเบอร์โทรศัพท์ กรุณาตรวจสอบข้อความ" };
    const phoneRaw = phoneMatches[0][0].trim();
    const phone = this.formatPhone(phoneRaw);
    const withoutPhone = text.replace(phoneRaw, " ");
    const postalMatches = [...withoutPhone.matchAll(/(?<!\d)\d{5}(?!\d)/g)];
    let postalCode = postalMatches.length ? postalMatches[postalMatches.length - 1][0] : "";

    const markers = ["โรงพยาบาล", "รพ.", "บริษัท", "หจก.", "ร้าน", "เลขที่", "หมู่บ้าน", "ถนน", "ซอย", "แขวง", "เขต", "ตำบล", "อำเภอ", "จังหวัด", "ต.", "อ.", "จ.", "ม."];
    const stopWords = new Set(["ส่ง", "บ้าน", "หมู่", "ถนน", "ซอย", "ตำบล", "อำเภอ", "จังหวัด", "โรงพยาบาล", "บริษัท", "ร้าน"]);
    const candidates = [];
    const lines = text.split("\n").map((line) => line.replace(/\s+/g, " ").trim()).filter(Boolean);

    lines.forEach((original, lineIndex) => {
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
      let score = 5 + (title ? 6 : 0) + (positions.length ? 0 : 3) + (original.includes(phoneRaw) ? 2 : 0) + (words.length === 2 ? 2 : 0);
      const namePattern = title ? `${title}\\s*${first}\\s+${second}` : `${first}\\s+${second}`;
      candidates.push({ name: `${title}${first} ${second}`, namePattern, lineIndex, score });
    });

    if (!candidates.length) return { valid: false, name: "", phone, address: withoutPhone.trim(), postalCode, message: "ไม่พบชื่อและนามสกุล กรุณาตรวจสอบข้อความ" };
    candidates.sort((a, b) => b.score - a.score || a.lineIndex - b.lineIndex);
    const selected = candidates[0];
    const address = lines.map((line, index) => {
      let cleaned = line;
      if (index === selected.lineIndex) {
        cleaned = cleaned.replace(/^\s*#?\s*ส่ง\s*/, "").replace(new RegExp(selected.namePattern), " ");
      }
      cleaned = cleaned.replace(phoneRaw, " ");
      cleaned = cleaned.replace(/(?:โทร(?:ศัพท์)?|เบอร์(?:โทรศัพท์)?)\s*:?\s*$/, " ");
      if (postalCode) cleaned = cleaned.replace(new RegExp(`(?<!\\d)${postalCode}(?!\\d)`), " ");
      return cleaned.replace(/^[\s,:#-]+|[\s,:#-]+$/g, "").replace(/\s+/g, " ");
    }).filter(Boolean).join("\n");
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

  lookupPostcodes(address) {
    const rows = BjpLabelCard.postcodeRows || [];
    const text = this.normalizeLocation(address);
    if (!text || !rows.length) return [];

    const extract = (pattern) => text.match(pattern)?.[1]?.replace(/[ .]+$/g, "") || "";
    const province = extract(/(?:จังหวัด|จ\.)\s*([^\s,]+)/);
    const district = extract(/(?:อำเภอ|อ\.|เขต)\s*([^\s,]+)/);
    const subdistrict = extract(/(?:ตำบล|ต\.|แขวง)\s*([^\s,]+)/);
    let matches = rows.filter((row) =>
      (!province || this.locationMatches(province, row.p, "province")) &&
      (!district || this.locationMatches(district, row.d, "district")) &&
      (!subdistrict || this.locationMatches(subdistrict, row.s, "subdistrict"))
    );

    if (!matches.length && subdistrict && (district || province)) {
      matches = rows.filter((row) =>
        (!province || this.locationMatches(province, row.p, "province")) &&
        (!district || this.locationMatches(district, row.d, "district"))
      );
    }

    if (!province && !district && !subdistrict) {
      matches = rows.filter((row) => [
        [row.s, "subdistrict"],
        [row.d, "district"],
        [row.p, "province"],
      ].filter(([name, kind]) => {
        const plain = this.plainLocation(name, kind);
        return plain.length >= 3 && text.includes(plain);
      }).length >= 2);
    }
    return [...new Set(matches.map((row) => String(row.z)))];
  }

  normalizeLocation(value) {
    return String(value || "").replaceAll("กรุงเทพฯ", "กรุงเทพมหานคร").replace(/\s+/g, " ").trim();
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
    return plainQuery === plainActual ||
      (kind === "district" && plainQuery === "เมือง" && plainActual.startsWith("เมือง"));
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
