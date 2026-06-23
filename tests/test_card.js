const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

global.HTMLElement = class {};
let Card;
let registeredCard;
global.customElements = {
  get: () => registeredCard,
  define: (_name, cardClass) => {
    Card = cardClass;
    registeredCard = cardClass;
  },
};
global.window = {};
const cardModule = require.resolve("../custom_components/bjp_label/frontend/bjp-label-card.js");
require(cardModule);
delete require.cache[cardModule];
require(cardModule);
assert.equal(window.customCards.length, 1);

const card = new Card();
Card.postcodeRows = [
  { s: "ธรรมศาลา", d: "เมืองนครปฐม", p: "นครปฐม", z: 73000 },
  { s: "พระปฐมเจดีย์", d: "เมืองนครปฐม", p: "นครปฐม", z: 73000 },
  { s: "บางเลน", d: "บางเลน", p: "นครปฐม", z: 73130 },
  { s: "คอนสาร", d: "คอนสาร", p: "ชัยภูมิ", z: 36180 },
  { s: "ดงกลาง", d: "คอนสาร", p: "ชัยภูมิ", z: 36180 },
];
card.config = {
  width: 640,
  height: 384,
  density: 3,
  rotate: 90,
  preview: false,
  printer_backend: "niimbot",
};
card.integrationSettings = {
  printer_backend: "niimbot",
  font: "NotoSansThai-Regular.ttf",
  device_id: "",
  host: "",
  port: 9100,
  label_size: "100x75",
};
card.settingsLoaded = true;

const parsed = card.parseText(
  "เทพฤทธิ์ ดีเจริญ 0817544374\n14/23 ม.4 ต.ธรรมศาลา อ.เมือง จ.นครปฐม 73000",
);
assert.equal(
  card.formatParsed(parsed),
  "เทพฤทธิ์ ดีเจริญ\n081-754-4374\n14/23 ม.4 ต.ธรรมศาลา อ.เมือง\nจ.นครปฐม\n73000",
);

const inferred = card.parseText(
  "เทพฤทธิ์ ดีเจริญ 0817544374\n14/23 ม.4 ต.ธรรมศาลา อ.เมือง จ.นครปฐม",
);
assert.equal(inferred.postalCode, "73000");
assert.match(inferred.message, /เติมรหัสไปรษณีย์ 73000/);

const ambiguous = card.parseText("สมชาย รักดี 0812345678\nจ.นครปฐม");
assert.equal(ambiguous.postalCode, "");
assert.match(ambiguous.message, /หลายค่า/);

const organizationAddress = card.parseText(
  "ส่งมนูญ เบญจพรหม โรงพยาบาลส่งเสริมสุขภาพตำบลบ้านดงกลาง อ.คอนสาร จ.ชัยภูมิ 0818719257",
);
assert.equal(organizationAddress.postalCode, "36180");

const separatedNumbers = card.parseText(
  "ที่อยู่ผู้รับ\nคุณไพรัตน์ เปรมสุขวิศรุต\n299/82 หมู่บ้านมัณฑนา-เลควัชรพล ถนนสุขาภิบาล 5 ออเงิน สายไหม กรุงเทพมหานคร 10220\n0819224340",
);
assert.equal(separatedNumbers.name, "คุณไพรัตน์ เปรมสุขวิศรุต");
assert.equal(separatedNumbers.phone, "081-922-4340");
assert.equal(separatedNumbers.postalCode, "10220");
assert.doesNotMatch(separatedNumbers.phone, /022-008-1922/);
assert.doesNotMatch(separatedNumbers.address, /10220|0819224340/);
assert.ok(separatedNumbers.address.split("\n").length <= 3);

const balancedAddress = card.parseText(
  "ปู จักรวุธ\n588/1 เสนานิคม1ซอย12\nจันทรเกษม,จตุจักร\nกทม.10900\n# 0949499796",
);
assert.equal(balancedAddress.phone, "094-949-9796");
assert.equal(balancedAddress.address, "588/1 เสนานิคม1ซอย12\nจันทรเกษม,\nจตุจักร กทม.");
assert.equal(balancedAddress.postalCode, "10900");

const shop = card.parseText(
  "ร้าน PK ตลาดอินโดจีนมุกดาหาร 24/8 ถนนสำราญชายโขงใต้ ตำบลศรีบุญเรือง อำเภอเมือง จังหวัดมุกดาหาร 49000\nโทร 087 457 5560",
);
assert.equal(shop.name, "ร้าน PK ตลาดอินโดจีนมุกดาหาร");
assert.equal(shop.phone, "087-457-5560");
assert.equal(shop.postalCode, "49000");
assert.match(shop.address, /^24\/8 ถนนสำราญชายโขงใต้/);
assert.ok(shop.address.split("\n").length <= 3);

card.formattedText = [
  "ส่ง นายสมชาย รักดี",
  "089-111-2222",
  "99/1 ถนนสุขุมวิท",
  "เขตคลองเตย กรุงเทพฯ",
  "10110",
].join("\n");
card.formatted = card.parseFormattedText(card.formattedText);
assert.equal(card.formatted.valid, true);
assert.equal(card.formatted.name, "นายสมชาย รักดี");
assert.equal(card.formatted.address, "99/1 ถนนสุขุมวิท\nเขตคลองเตย กรุงเทพฯ");

const serviceData = card.serviceData();
assert.equal(serviceData.name, "นายสมชาย รักดี");
assert.equal(serviceData.phone, "089-111-2222");
assert.equal(serviceData.postal_code, "10110");
assert.equal(serviceData.width, 640);
assert.equal(serviceData.height, 384);
assert.equal(serviceData.rotate, 90);
assert.equal(serviceData.preview, false);
assert.equal("text" in serviceData, false);

const xprinterCard = new Card();
xprinterCard.rawConfig = { printer_backend: "xprinter_tspl", host: "192.168.1.50", port: 9100, label_size: "100x75" };
xprinterCard.config = {
  ...card.config,
  printer_backend: "xprinter_tspl",
  host: "192.168.1.50",
  port: 9100,
  label_size: "100x75",
};
xprinterCard.integrationSettings = {
  printer_backend: "niimbot",
  font: "NotoSansThai-Regular.ttf",
  device_id: "",
  host: "",
  port: 9100,
  label_size: "100x75",
};
xprinterCard.settingsLoaded = true;
xprinterCard.formattedText = card.formattedText;
xprinterCard.formatted = card.formatted;
const xprinterServiceData = xprinterCard.serviceData();
assert.equal(xprinterServiceData.printer_backend, "xprinter_tspl");
assert.equal(xprinterServiceData.label_size, "100x75");
assert.equal(xprinterServiceData.host, "192.168.1.50");
assert.equal(xprinterServiceData.port, 9100);
assert.equal("rotate" in xprinterServiceData, false);

const withoutPostal = card.parseFormattedText(
  "ส่ง มนูญ เบญจพรหม\n081-871-9257\nโรงพยาบาลส่งเสริมสุขภาพตำบลบ้านดงกลาง",
);
assert.equal(withoutPostal.valid, true);
assert.equal(withoutPostal.postalCode, "");
assert.equal(
  withoutPostal.address,
  "โรงพยาบาลส่งเสริมสุขภาพตำบลบ้านดงกลาง",
);

assert.equal(
  card.parseFormattedText("ส่ง สมชาย รักดี\n123\nกรุงเทพฯ").valid,
  false,
);
assert.equal(
  card.parseFormattedText("สมชาย รักดี\n081-234-5678\nหนึ่ง\nสอง\nสาม\nสี่\n10110").valid,
  false,
);

async function testPreviewThenPrint() {
  const calls = [];
  let finishPrint;
  const printCard = new Card();
  printCard.config = { ...card.config, preview: false };
  printCard.integrationSettings = { ...card.integrationSettings };
  printCard.settingsLoaded = true;
  printCard.formatted = card.parseFormattedText(
    "ส่ง สมชาย รักดี\n081-234-5678\nกรุงเทพมหานคร\n10110",
  );
  printCard.updateForm = () => {};
  printCard._hass = {
    callService: (...args) => {
      calls.push(args);
      if (args[2].preview) return Promise.resolve({ image: "data:image/png;base64,PREVIEW" });
      return new Promise((resolve) => { finishPrint = resolve; });
    },
  };

  await printCard.handleAction("print");
  assert.equal(calls.length, 0);
  await printCard.generatePreview();
  assert.equal(calls.length, 1);
  assert.equal(calls[0][2].preview, true);
  assert.equal(calls[0][5], true);
  assert.equal(printCard.previewImage, "data:image/png;base64,PREVIEW");
  assert.equal(printCard.previewSnapshot.preview, false);

  const firstPrint = printCard.handleAction("print");
  const duplicatePrint = printCard.handleAction("print");
  assert.equal(calls.length, 2);
  assert.deepEqual(calls[1][2], printCard.previewSnapshot);
  assert.equal(calls[1][2].preview, false);
  assert.equal(printCard.isPrinting, true);
  await duplicatePrint;
  finishPrint();
  await firstPrint;
  assert.equal(printCard.status, "พิมพ์เสร็จแล้ว");
  assert.equal(printCard.printLocked, true);

  await printCard.handleAction("print");
  assert.equal(calls.length, 2);
  printCard.resetPrintState();
  assert.equal(printCard.printLocked, false);

  printCard._hass.callService = async (...args) => {
    calls.push(args);
    throw new Error("printer unavailable");
  };
  await printCard.handleAction("print");
  assert.match(printCard.status, /พิมพ์ไม่สำเร็จ/);
  assert.equal(printCard.printLocked, false);
  assert.equal(printCard.isPrinting, false);
}

async function testPreviewFailureRetryAndStaleResponse() {
  const previewCard = new Card();
  previewCard.config = { ...card.config, preview: false };
  previewCard.integrationSettings = { ...card.integrationSettings };
  previewCard.settingsLoaded = true;
  previewCard.formatted = card.parseFormattedText(
    "สมชาย รักดี\n081-234-5678\nกรุงเทพมหานคร\n10110",
  );
  previewCard.updateForm = () => {};
  previewCard._hass = { callService: async () => { throw new Error("preview unavailable"); } };

  await previewCard.generatePreview();
  assert.equal(previewCard.previewError, true);
  assert.equal(previewCard.previewSnapshot, null);

  previewCard._hass.callService = async () => ({ image: "data:image/png;base64,RETRY" });
  await previewCard.handleAction("retry-preview");
  assert.equal(previewCard.previewError, false);
  assert.equal(previewCard.previewImage, "data:image/png;base64,RETRY");

  let finishStalePreview;
  previewCard.invalidatePreview();
  previewCard._hass.callService = () => new Promise((resolve) => { finishStalePreview = resolve; });
  const stalePreview = previewCard.generatePreview();
  previewCard.invalidatePreview();
  finishStalePreview({ image: "data:image/png;base64,STALE" });
  await stalePreview;
  assert.equal(previewCard.previewImage, "");
  assert.equal(previewCard.previewSnapshot, null);
}

async function testAutomaticAndPreviewOnlyModes() {
  let calls = 0;
  const autoCard = new Card();
  autoCard.config = { ...card.config, preview: false };
  autoCard.integrationSettings = { ...card.integrationSettings };
  autoCard.settingsLoaded = true;
  autoCard.formatted = card.parseFormattedText(
    "สมชาย รักดี\n081-234-5678\nกรุงเทพมหานคร\n10110",
  );
  autoCard.updateForm = () => {};
  autoCard._hass = {
    callService: async () => {
      calls += 1;
      return { image: "data:image/png;base64,AUTO" };
    },
  };
  autoCard.schedulePreview(0);
  await new Promise((resolve) => setTimeout(resolve, 10));
  assert.equal(calls, 1);
  assert.ok(autoCard.previewSnapshot);

  autoCard.config.preview = true;
  await autoCard.handleAction("print");
  assert.equal(calls, 1);

  autoCard.invalidatePreview();
  autoCard.formatted = card.parseFormattedText("ข้อมูลไม่ครบ");
  autoCard.schedulePreview(0);
  await new Promise((resolve) => setTimeout(resolve, 10));
  assert.equal(calls, 1);
}

function testPreviewImageIsRendered() {
  const uiCard = new Card();
  uiCard.config = { ...card.config, preview: false };
  uiCard.integrationSettings = { ...card.integrationSettings };
  uiCard.settingsLoaded = true;
  uiCard.formatted = card.parseFormattedText(
    "สมชาย รักดี\n081-234-5678\nกรุงเทพมหานคร\n10110",
  );
  uiCard.parseWarning = "";
  uiCard.previewImage = "data:image/png;base64,DISPLAY";
  uiCard.previewSnapshot = { preview: false };
  uiCard.status = "";
  uiCard.statusType = "done";
  uiCard.isPreviewing = false;
  uiCard.isPrinting = false;
  uiCard.printLocked = false;
  uiCard.previewError = false;

  const nodes = new Map();
  const node = () => ({
    hidden: false,
    disabled: false,
    textContent: "",
    dataset: {},
    attributes: {},
    classes: new Set(),
    classList: {
      toggle() {},
    },
    setAttribute(name, value) { this.attributes[name] = value; },
    removeAttribute(name) { delete this[name]; },
  });
  [
    "[data-warning]",
    "#customer-text",
    "#formatted-text",
    '[data-action="print"]',
    "[data-preview]",
    "[data-preview-image]",
    "[data-preview-placeholder]",
    '[data-action="retry-preview"]',
    ".status",
  ].forEach((selector) => nodes.set(selector, node()));
  nodes.get("[data-preview]").classList.toggle = (name, force) => {
    if (force) nodes.get("[data-preview]").classes.add(name);
    else nodes.get("[data-preview]").classes.delete(name);
  };
  uiCard.querySelector = (selector) => nodes.get(selector);

  uiCard.updateForm();
  assert.equal(nodes.get("[data-preview]").classes.has("is-hidden"), false);
  assert.equal(nodes.get("[data-preview]").attributes["aria-hidden"], "false");
  assert.equal(nodes.get("[data-preview-image]").hidden, false);
  assert.equal(nodes.get("[data-preview-image]").src, uiCard.previewImage);
  assert.equal(nodes.get('[data-action="print"]').disabled, false);
}

function testPreviewBackendHelpers() {
  const niimbotCard = new Card();
  niimbotCard.rawConfig = { printer_backend: "niimbot" };
  niimbotCard.config = { ...card.config, printer_backend: "niimbot" };
  niimbotCard.integrationSettings = { ...card.integrationSettings };
  niimbotCard.settingsLoaded = true;
  assert.equal(niimbotCard.shouldRotatePreview(), true);
  assert.equal(niimbotCard.shouldShowLabelSizeSelector(), false);

  const xprinterPreviewCard = new Card();
  xprinterPreviewCard.rawConfig = {
    printer_backend: "xprinter_tspl",
    label_size: "100x150",
    show_label_size_selector: true,
  };
  xprinterPreviewCard.config = {
    ...card.config,
    printer_backend: "xprinter_tspl",
    label_size: "100x150",
    show_label_size_selector: true,
  };
  xprinterPreviewCard.integrationSettings = {
    printer_backend: "niimbot",
    font: "NotoSansThai-Regular.ttf",
    device_id: "",
    host: "",
    port: 9100,
    label_size: "100x75",
  };
  xprinterPreviewCard.settingsLoaded = true;
  xprinterPreviewCard.selectedLabelSize = "100x150";
  assert.equal(xprinterPreviewCard.shouldRotatePreview(), false);
  assert.equal(xprinterPreviewCard.shouldShowLabelSizeSelector(), true);
  assert.deepEqual(xprinterPreviewCard.currentPreviewPreset(), { width: 800, height: 1200 });
}

function testIntegrationSettingsDriveBackendWhenCardDoesNotOverride() {
  const inferredCard = new Card();
  inferredCard.rawConfig = {};
  inferredCard.config = {
    width: 640,
    height: 384,
    density: 3,
    rotate: 90,
    preview: false,
    show_label_size_selector: true,
  };
  inferredCard.integrationSettings = {
    printer_backend: "xprinter_tspl",
    font: "NotoSansThai-Regular.ttf",
    device_id: "",
    host: "192.168.1.77",
    port: 9100,
    label_size: "100x150",
  };
  inferredCard.settingsLoaded = true;
  inferredCard.selectedLabelSize = "100x150";
  inferredCard.formatted = card.formatted;
  const settings = inferredCard.effectiveSettings();
  const payload = inferredCard.serviceData(true);
  assert.equal(settings.printer_backend, "xprinter_tspl");
  assert.equal(inferredCard.shouldRotatePreview(), false);
  assert.equal(payload.printer_backend, "xprinter_tspl");
  assert.equal(payload.host, "192.168.1.77");
  assert.equal(payload.label_size, "100x150");
  assert.equal("rotate" in payload, false);
}

async function testSettingsMustLoadBeforeAutomaticPreview() {
  let calls = 0;
  const loadingCard = new Card();
  loadingCard.config = { ...card.config, preview: false };
  loadingCard.formatted = card.parseFormattedText(
    "สมชาย รักดี\n081-234-5678\nกรุงเทพมหานคร\n10110",
  );
  loadingCard.updateForm = () => {};
  loadingCard._hass = {
    callService: async () => {
      calls += 1;
      return { image: "data:image/png;base64,AUTO" };
    },
  };
  loadingCard.settingsLoaded = false;
  loadingCard.loadingSettings = true;
  loadingCard.schedulePreview(0);
  await new Promise((resolve) => setTimeout(resolve, 10));
  assert.equal(calls, 0);
}

const manifest = JSON.parse(fs.readFileSync(path.join(__dirname, "../custom_components/bjp_label/manifest.json")));
const cardSource = fs.readFileSync(path.join(__dirname, "../custom_components/bjp_label/frontend/bjp-label-card.js"), "utf8");
assert.match(cardSource, new RegExp(`BJP_LABEL_VERSION = ["']${manifest.version}["']`));
assert.doesNotMatch(cardSource, /<section class="preview"[^>]*\shidden(?:\s|>)/);
assert.match(cardSource, /shouldRotatePreview\(\)/);
assert.match(cardSource, /translate\(-50%, -50%\) rotate\(-90deg\)/);
assert.match(cardSource, /translate\(-50%, -50%\)"/);
assert.match(cardSource, /aspect-ratio:\s*\$\{previewWidth\}\s*\/\s*\$\{previewHeight\}/);

Promise.resolve()
  .then(testPreviewThenPrint)
  .then(testPreviewFailureRetryAndStaleResponse)
  .then(testAutomaticAndPreviewOnlyModes)
  .then(testPreviewImageIsRendered)
  .then(testPreviewBackendHelpers)
  .then(testIntegrationSettingsDriveBackendWhenCardDoesNotOverride)
  .then(testSettingsMustLoadBeforeAutomaticPreview)
  .then(() => console.log("card tests passed"));
