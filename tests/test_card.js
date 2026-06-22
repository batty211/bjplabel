const assert = require("node:assert/strict");

global.HTMLElement = class {};
let Card;
global.customElements = {
  define: (_name, cardClass) => {
    Card = cardClass;
  },
};
global.window = {};
require("../www/bjp-label-card/bjp-label-card.js");

const card = new Card();
card.config = {
  width: 640,
  height: 384,
  density: 3,
  rotate: 90,
  preview: true,
};

const parsed = card.parseText(
  "เทพฤทธิ์ ดีเจริญ 0817544374\n14/23 ม.4 ต.ธรรมศาลา อ.เมือง จ.นครปฐม 73000",
);
assert.equal(
  card.formatParsed(parsed),
  "ส่ง เทพฤทธิ์ ดีเจริญ\n081-754-4374\n14/23 ม.4 ต.ธรรมศาลา อ.เมือง จ.นครปฐม\n73000",
);

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
assert.equal("text" in serviceData, false);

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

console.log("card tests passed");
