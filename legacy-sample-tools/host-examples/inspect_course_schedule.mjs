// Same-project one-off host adapter. No original workbook or private SDK is distributed.
import fs from 'node:fs';
import path from 'node:path';
const args=process.argv.slice(2),wi=args.indexOf('--workspace'),ii=args.indexOf('--input');
if(!args.includes('--synthetic-demo')||wi<0||ii<0||!args[wi+1]||!args[ii+1]){console.error('SYNTHETIC_GUARD: optional host example requires --synthetic-demo --workspace <marked directory> --input <relative synthetic workbook.xlsx>');process.exit(2);}
const W=path.resolve(args[wi+1]),marker=path.join(W,'.wechat-synthetic-workspace.json');
if(!fs.existsSync(marker)||JSON.parse(fs.readFileSync(marker,'utf8')).synthetic!==true)throw Error('Synthetic workspace marker required.');
if(path.isAbsolute(args[ii+1]))throw Error('Input must be relative to the synthetic workspace.');
const SYNTHETIC_INPUT=path.resolve(W,args[ii+1]);
if(path.relative(W,SYNTHETIC_INPUT).startsWith('..'))throw Error('Input escapes the workspace.');
const {FileBlob,SpreadsheetFile}=await import('@oai/artifact-tool');

const sourcePath =
  SYNTHETIC_INPUT;

const input = await FileBlob.load(sourcePath);
const workbook = await SpreadsheetFile.importXlsx(input);

const overview = await workbook.inspect({
  kind: "workbook,sheet,table",
  maxChars: 20000,
  tableMaxRows: 40,
  tableMaxCols: 20,
  tableMaxCellChars: 200,
});
console.log("=== OVERVIEW ===");
console.log(overview.ndjson);

const sheets = workbook.worksheets.items;
for (const sheet of sheets) {
  const used = sheet.getUsedRange();
  console.log(`=== SHEET ${sheet.name} USED ${used.address} ===`);
  const region = await workbook.inspect({
    kind: "region",
    sheetId: sheet.name,
    range: used.address,
    include: "values,formulas",
    maxChars: 40000,
    tableMaxRows: 100,
    tableMaxCols: 30,
    tableMaxCellChars: 300,
  });
  console.log(region.ndjson);
}
