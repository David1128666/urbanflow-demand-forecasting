import en from "../src/locales/en.js";
import zhCN from "../src/locales/zh-CN.js";


function placeholders(value) {
  return [...value.matchAll(/\{(\w+)\}/g)]
    .map((match) => match[1])
    .sort();
}

const englishKeys = new Set(Object.keys(en));
const chineseKeys = new Set(Object.keys(zhCN));
const missingInChinese = [...englishKeys].filter(
  (key) => !chineseKeys.has(key),
);
const missingInEnglish = [...chineseKeys].filter(
  (key) => !englishKeys.has(key),
);
const placeholderMismatches = [...englishKeys].filter((key) => {
  if (!chineseKeys.has(key)) {
    return false;
  }
  return (
    JSON.stringify(placeholders(en[key])) !==
    JSON.stringify(placeholders(zhCN[key]))
  );
});

if (
  missingInChinese.length ||
  missingInEnglish.length ||
  placeholderMismatches.length
) {
  console.error({
    missingInChinese,
    missingInEnglish,
    placeholderMismatches,
  });
  process.exit(1);
}

console.log("Frontend locale check passed.");
