"""Finalize the single evaluated candidate; never trains or predicts."""
import json
import subprocess
import sys
import pandas as pd
from common import HERE, ROOT, sha, save, log, guard, now


def fmt(x, digits=4):
    return 'N/A' if x is None else f'{x:.{digits}f}'


def main():
    guard()
    frozen=json.loads((HERE/'frozen-candidate.json').read_text())
    audit=json.loads((HERE/'evaluation-audit.json').read_text())
    scores=json.loads((HERE/'classification.json').read_text())
    econ=json.loads((HERE/'economics.json').read_text())
    engine=json.loads((HERE/'backtest/metrics.json').read_text())
    # Correct a report-field name, using existing engine output only. No reevaluation.
    econ['unfiltered']['freqtrade_wallet_max_drawdown_pct']=engine['wallet_stats']['max_drawdown_account']*100
    econ['reporting_note']='Raw economics.json labeled max_drawdown_account as wallet drawdown. It is closed-trade drawdown. This finalized file uses wallet_stats for the distinct wallet statistic. No outcomes or predictions change.'
    save(HERE/'economic-comparison.json',econ)
    predictions=pd.read_parquet(HERE/'shadow-predictions.parquet')
    assert (predictions.selected==(predictions.probability>=.55)).all()
    assert predictions.row_id.is_unique and len(predictions)==78
    assert len(predictions[predictions.selected])==2
    events=[json.loads(line) for line in (HERE/'audit.jsonl').read_text().splitlines()]
    assert sum(e['event']=='single_prediction_call' for e in events)==1
    assert sum(e['event']=='baseline_backtest_start' for e in events)==1
    hashes=json.loads((HERE/'pre-unseal-hashes.json').read_text())
    for relative,digest in hashes['source_hashes'].items(): assert sha(ROOT/relative)==digest
    for name,digest in hashes['hashes'].items(): assert sha(HERE/name)==digest
    for relative,digest in json.loads((HERE/'original-seal-hashes.json').read_text()).items(): assert sha(ROOT/relative)==digest
    with (HERE/'protocol-tests.log').open('w',encoding='utf-8') as out:
        subprocess.run([sys.executable,'-B',str(HERE/'test_protocol.py')],cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,check=True)
    status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True)
    assert set(status.strip().splitlines())=={'?? ai_lab/ml_models_v2/','?? ai_lab/ml_shadow/'},status
    save(HERE/'final-audit.json',{'utc':now(),'branch':'ai-lab-development','tracked_changes':[],
        'preexisting_untracked':'ai_lab/ml_models_v2/','created_scope':'ai_lab/ml_shadow/',
        'frozen_sources_model_manifest_unchanged':True,'original_seal_and_prices_unchanged':True,
        'training_data_2019_2024_only':True,'prediction_calls':1,'baseline_backtest_runs':1,
        'technical_recoveries_before_predictions':2,'candidate_parameter_changes':0,
        'tests':'3 passed','git_status':status,
        'consumption_marker':'ai_lab/ml_shadow/CONSUMED.json',
        'reporting_corrections':['Close-time subset drawdown defined before unseal; differs from Phase 3C entry-day implementation.',
            'Final economic-comparison.json distinguishes original closed-trade vs wallet-statistics drawdown fields.']})
    unfiltered=econ['unfiltered']; filtered=econ['filtered']
    lines=['# Phase 3D single-shot shadow evaluation','',
        '**C. No evidence of reliable ML edge for this frozen candidate.**','',
        'The candidate selected two trades, both ETH losses. Net P/L was -3.5900 USDT versus +1.3002 USDT unfiltered.',
        'Overall ranking was near random, and pair ranking contradicted sharply. This does not justify paper-trading integration.',
        'It is not a claim that every possible ML approach is ineffective. This period is now consumed and must never guide retuning.',
        '', '## Frozen candidate','',
        '- LogisticRegression, Phase 3C B_reduced, 36 raw predictors (34 numeric + pair/regime).',
        '- L2: C=0.1, l1_ratio=0, lbfgs, max_iter=2000, tol=0.0001, no class weights, seed 31415.',
        '- StandardScaler and dense OneHotEncoder(handle_unknown="ignore"), fitted on development only.',
        '- Target profitable_after_fees; threshold 0.55. No calibration refit or alternative thresholds.',
        '- 1,271 training trades: 2019-01-01 through 2024-12-31. All labels used for fitting end in 2024.',
        '- Shadow 2026-04-01 inclusive through 2026-09-01 exclusive. March 2026 is feature warmup only.',
        '- Fee 0.1% each side; fixed 100 USDT stake; 1,000 USDT wallet; two open trades maximum.',
        f"- Freeze UTC: {frozen['freeze_utc']}; Git commit: {frozen['git_commit']}.",
        f"- Manifest SHA256: {sha(HERE/'frozen-candidate.json')}",
        f"- Fitted model SHA256: {sha(HERE/'candidate.joblib')}",
        '', 'Exact feature list:','', ', '.join(frozen['features']),
        '', '## Classification at frozen threshold 0.55','',
        '| Metric | All | BTC | ETH |','| --- | ---: | ---: | ---: |']
    for key in ['n','prevalence','roc_auc','pr_auc_ap','balanced_accuracy','precision','recall','f1','brier','ece_5_bins','mean_probability']:
        lines.append('| '+key+' | '+' | '.join(fmt(scores[p][key]) for p in ['ALL','BTC/USDT','ETH/USDT'])+' |')
    lines+=['','Confusion matrices are [[TN, FP], [FN, TP]]:']
    for pair,s in scores.items(): lines.append(f"- {pair}: {s['confusion_matrix']}")
    lines+=['','The uninformative-ranking AP reference is target prevalence: 0.3846 overall. Observed AP 0.3960 is only 0.0114 higher.',
            'The standard Phase 3C classification cutoff 0.50 is separately retained in classification.json for compatibility, not as another economic rule.',
            '', '## Economics after fees','', '| Metric | Unfiltered LabBaseline | Frozen filter |','| --- | ---: | ---: |']
    for key in ['trades','retention_pct','wins','losses','win_rate_pct','net_usdt','return_on_1000_pct','average_trade_pct','profit_factor','expectancy_usdt','closed_trade_max_drawdown_pct','consecutive_losses','average_duration_minutes']:
        lines.append(f'| {key} | {fmt(unfiltered[key])} | {fmt(filtered[key])} |')
    lines += [f"", f"Net change versus unfiltered: {econ['net_improvement_usdt']:.4f} USDT.",
        f"Unfiltered start/end balance: 1000 / {engine['final_balance']:.4f} USDT. Filtered realized subset ending equity: {1000+filtered['net_usdt']:.4f} USDT.",
        f"Full Freqtrade unfiltered wallet-statistics drawdown is {unfiltered['freqtrade_wallet_max_drawdown_pct']:.4f}%, distinct from closed-trade drawdown.",
        'Filtered drawdown is closed-trade subset equity; no filtered intratrade wallet simulation was run.',
        '', '## Pair economics','', '| Pair | Baseline trades | Baseline net | Selected | Retention | Filter net | Filter PF |','| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for pair,v in econ['pairs'].items():
        a,b=v['unfiltered'],v['filtered']
        lines.append(f"| {pair} | {a['trades']} | {a['net_usdt']:.4f} | {b['trades']} | {b['retention_pct']:.2f}% | {b['net_usdt']:.4f} | {fmt(b['profit_factor'])} |")
    lines+=['','Regime counts at entry:','',f"- Unfiltered: {unfiltered['regime_counts']}",f"- Filtered: {filtered['regime_counts']}",
        '', '## Audits and technical recovery','',
        '- Manifest, fitted model, preprocessing and all frozen source hashes were recorded before unsealing; all still match.',
        '- Model/scaler/encoder fitted once on 2019-2024 development rows before shadow access. No 2025/2026 data in fitting.',
        '- Exactly one baseline backtest and one predict_proba call; no setting changes or alternate evaluations.',
        '- Original seal and both price files still match their original SHA256 values.',
        '- Each pair: 3,672 shadow hours and 744 March warmup hours, no missing or duplicate candles.',
        '- Each pair: 12 real prefix checks, future mutation and no future-fill checks passed.',
        '- 78 unique trades; no NaN/infinite predictors; all feature candles completed before entry.',
        '- Three synthetic/protocol tests passed. One boundary force exit; no rejected baseline entry signals.',
        '- Two technical stops occurred before any predictions or backtests: dtype-sensitive timestamp equality, then mixed datetime concatenation. Audited recovery normalized representation while asserting unchanged timestamps. Frozen files and model parameters were preserved.',
        '- Freqtrade warns that data ends at Aug 31 23:00; this is the required last hourly candle before the end-exclusive Sep 1 boundary.',
        '- Predeclared drawdown correction uses close times. Raw economics.json also misnamed the engine closed-trade statistic as wallet drawdown; economic-comparison.json corrects that name/value from existing wallet_stats only.',
        '- Consumption is recorded in CONSUMED.json here; original SEALED.json remains historical evidence. Do not regard it as an unused seal.',
        '- All observed integrity/leakage checks pass; tests cannot prove absence of every possible defect. Small samples and common market exposure limit inference.',
        '', '## Scope','', 'No core/strategy or existing tracked files changed. Phase 3C untracked files were preserved. No integration, commit, push or merge.',
        'All new deliverables are listed in file-inventory.txt and hashed in artifact-sha256.json.',
        '', '## Git status','', '```text',status.rstrip(),'```']
    (HERE/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    log('report_and_final_checks_complete',category=audit['category'],prediction_calls=1,consumed=True)
    inventory=HERE/'file-inventory.txt'; manifest=HERE/'artifact-sha256.json'
    files=sorted(set([p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts]+[inventory,manifest]))
    inventory.write_text('\n'.join(p.relative_to(ROOT).as_posix() for p in files)+'\n',encoding='utf-8')
    save(manifest,{p.relative_to(HERE).as_posix():sha(p) for p in files if p!=manifest})
    print(f'{len(files)} created deliverable files. Category {audit["category"]}.')


if __name__=='__main__': main()
