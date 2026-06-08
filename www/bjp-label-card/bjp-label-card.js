class BjpLabelCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("hui-generic-card-editor");
  }

  static getStubConfig() {
    return {
      title: "พิมพ์ฉลากลูกค้า",
      font: "NotoSansThai-Regular.ttf",
      width: 400,
      height: 240,
      density: 3,
      rotate: 0,
    };
  }

  setConfig(config) {
    this.config = {
      title: "พิมพ์ฉลากลูกค้า",
      font: "NotoSansThai-Regular.ttf",
      width: 400,
      height: 240,
      density: 3,
      rotate: 0,
      ...config,
    };
    this.form = {
      name: "",
      phone: "",
      address: "",
      note: "",
    };
    this.status = "";
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
  }

  getCardSize() {
    return 5;
  }

  render() {
    if (!this.config) return;

    this.innerHTML = `
      <ha-card>
        <div class="card">
          <h2>${this.config.title}</h2>
          <label>
            <span>ชื่อลูกค้า</span>
            <input name="name" autocomplete="name" value="${this.escape(this.form.name)}" />
          </label>
          <label>
            <span>เบอร์โทรศัพท์</span>
            <input name="phone" autocomplete="tel" inputmode="tel" value="${this.escape(this.form.phone)}" />
          </label>
          <label>
            <span>ที่อยู่</span>
            <textarea name="address" rows="3">${this.escape(this.form.address)}</textarea>
          </label>
          <label>
            <span>หมายเหตุ</span>
            <textarea name="note" rows="2">${this.escape(this.form.note)}</textarea>
          </label>
          <div class="actions">
            <button class="secondary" data-action="save">บันทึก</button>
            <button class="primary" data-action="print">พิมพ์</button>
            <button class="primary wide" data-action="save-print">บันทึกและพิมพ์</button>
            <button class="secondary" data-action="clear">ล้างข้อมูล</button>
          </div>
          <p class="status" aria-live="polite">${this.escape(this.status)}</p>
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
          font-weight: 700;
        }

        label {
          display: block;
          margin: 0 0 16px;
        }

        span {
          display: block;
          margin-bottom: 8px;
          font-size: 20px;
          font-weight: 700;
        }

        input,
        textarea {
          box-sizing: border-box;
          width: 100%;
          min-height: 56px;
          padding: 12px 14px;
          border: 2px solid var(--divider-color);
          border-radius: 8px;
          background: var(--card-background-color);
          color: var(--primary-text-color);
          font: inherit;
          font-size: 22px;
        }

        textarea {
          min-height: 104px;
          resize: vertical;
        }

        .actions {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 12px;
          margin-top: 18px;
        }

        button {
          min-height: 64px;
          border: 0;
          border-radius: 8px;
          padding: 12px 16px;
          font: inherit;
          font-size: 22px;
          font-weight: 700;
          cursor: pointer;
        }

        .primary {
          background: var(--primary-color);
          color: var(--text-primary-color);
        }

        .secondary {
          background: var(--secondary-background-color);
          color: var(--primary-text-color);
        }

        .wide {
          grid-column: span 2;
        }

        .status {
          min-height: 24px;
          margin: 14px 0 0;
          font-size: 18px;
          line-height: 1.35;
        }

        @media (max-width: 520px) {
          .card {
            padding: 16px;
          }

          .actions {
            grid-template-columns: 1fr;
          }

          .wide {
            grid-column: auto;
          }
        }
      </style>
    `;

    this.querySelectorAll("input, textarea").forEach((field) => {
      field.addEventListener("input", (event) => {
        this.form[event.target.name] = event.target.value;
      });
    });

    this.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => this.handleAction(button.dataset.action));
    });
  }

  async handleAction(action) {
    if (action === "clear") {
      this.form = { name: "", phone: "", address: "", note: "" };
      this.status = "ล้างข้อมูลแล้ว";
      this.render();
      return;
    }

    if (action === "save") {
      this.status = "การบันทึกข้อมูลจะเปิดใช้ใน Phase 2";
      this.render();
      return;
    }

    if (!this.validateForm()) {
      this.render();
      return;
    }

    try {
      await this._hass.callService("bjp_label", "print_label", this.serviceData());
      this.status = action === "save-print" ? "ส่งพิมพ์แล้ว การบันทึกข้อมูลจะเปิดใช้ใน Phase 2" : "ส่งพิมพ์แล้ว";
    } catch (error) {
      this.status = `พิมพ์ไม่สำเร็จ: ${error.message || error}`;
    }
    this.render();
  }

  validateForm() {
    if (!this.form.name.trim()) {
      this.status = "กรุณากรอกชื่อลูกค้า";
      return false;
    }
    if (!this.form.phone.trim()) {
      this.status = "กรุณากรอกเบอร์โทรศัพท์";
      return false;
    }
    if (!this.form.address.trim()) {
      this.status = "กรุณากรอกที่อยู่";
      return false;
    }
    return true;
  }

  serviceData() {
    const data = {
      name: this.form.name.trim(),
      phone: this.form.phone.trim(),
      address: this.form.address.trim(),
      note: this.form.note.trim(),
      font: this.config.font,
      width: Number(this.config.width),
      height: Number(this.config.height),
      density: Number(this.config.density),
      rotate: Number(this.config.rotate),
      preview: Boolean(this.config.preview),
    };
    if (this.config.device_id) {
      data.device_id = this.config.device_id;
    }
    return data;
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

customElements.define("bjp-label-card", BjpLabelCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "bjp-label-card",
  name: "BJP Label",
  description: "Thai customer label printing card for Niimbot through Home Assistant",
});
