const fs=require('fs'),crypto=require('crypto');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex').toUpperCase();
const reportPath='work/runtime_fix/main_dol_translation_report.json';
const patchPath='work/runtime_fix/main_dol_patch_report.json';
const report=JSON.parse(fs.readFileSync(reportPath,'utf8'));
const patch=JSON.parse(fs.readFileSync(patchPath,'utf8'));
const tm='work/runtime_fix/main_dol_translations.jsonl';
if(patch.inputs.translations_jsonl.sha256!==sha(tm))throw new Error('patch report is stale for current translations');
report.actual_custom_euc28_patch_validation={
  valid:patch.valid,
  patch_rows:patch.summary.patch_rows,
  translations_sha256:sha(tm),
  codebook_sha256:patch.inputs.codebook.sha256,
  output_main_dol_sha256:patch.output.sha256,
  file_size_preserved:patch.summary.file_size_preserved,
  all_original_raw_verified:patch.summary.all_original_raw_verified,
  all_original_terminating_nuls_preserved:patch.summary.all_original_terminating_nuls_preserved,
  changes_confined_to_allowlisted_spans:patch.summary.changes_confined_to_allowlisted_spans,
  patch_report:'work/runtime_fix/main_dol_patch_report.json'
};
report.output_sha256={
  translations:sha(tm),
  exclusions:sha('work/runtime_fix/main_dol_exclusions.jsonl'),
  patched_main_dol:sha('work/runtime_fix/main.dol.patched'),
  patch_report:sha(patchPath)
};
fs.writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n','utf8');
console.log(JSON.stringify(report.actual_custom_euc28_patch_validation,null,2));
