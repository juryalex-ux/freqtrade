"""Freeze AlphaBreakout before accessing retrospective outcomes."""
import json
import shutil
import subprocess
from common import HERE, ROOT, BASELINE_SHA, PERIODS, guard, log, now, save, sha


def main():
    guard()
    assert not (HERE/'frozen-manifest.json').exists(), 'Frozen manifest exists; do not overwrite.'
    source = ROOT/'ai_lab/alpha_research/strategies/AlphaCandidates.py'
    phase4 = json.loads((ROOT/'ai_lab/alpha_research/protocol.json').read_text())
    assert sha(source) == phase4['code_hashes']['strategies/AlphaCandidates.py']
    assert phase4['candidates']['AlphaBreakout']['perturbation']['values'] == [20, 24, 28]
    for folder in ['strategies', 'data', 'raw', 'results', 'reports', 'audits']:
        (HERE/folder).mkdir(exist_ok=True)
    shutil.copyfile(source, HERE/'strategies/AlphaCandidates.py')
    shutil.copyfile(ROOT/'ai_lab/strategies/LabBaseline.py', HERE/'strategies/LabBaseline.py')
    assert sha(HERE/'strategies/AlphaCandidates.py') == sha(source)
    assert sha(HERE/'strategies/LabBaseline.py') == BASELINE_SHA
    config = json.loads((ROOT/'ai_lab/configs/backtest.json').read_text())
    assert config['dry_run'] is True and config['exchange']['pair_whitelist'] == ['BTC/USDT', 'ETH/USDT']
    config['user_data_dir'] = str(HERE)
    config['datadir'] = str(HERE/'data')
    save(HERE/'backtest.json', config)
    seal_path = ROOT/'ai_lab/regime/shadow/SEALED.json'
    seal = json.loads(seal_path.read_text())
    assert seal['start_utc'] == '2026-04-01T00:00:00Z' and seal['end_exclusive_utc'] == '2026-09-01T00:00:00Z'
    source_hashes = {
        'ai_lab/alpha_research/strategies/AlphaCandidates.py': sha(source),
        'ai_lab/alpha_research/protocol.json': sha(ROOT/'ai_lab/alpha_research/protocol.json'),
        'ai_lab/strategies/LabBaseline.py': BASELINE_SHA,
        'ai_lab/configs/backtest.json': sha(ROOT/'ai_lab/configs/backtest.json'),
        'ai_lab/regime/shadow/SEALED.json': sha(seal_path),
    }
    validation_hashes = {
        'strategies/AlphaCandidates.py': sha(HERE/'strategies/AlphaCandidates.py'),
        'strategies/LabBaseline.py': sha(HERE/'strategies/LabBaseline.py'),
        'backtest.json': sha(HERE/'backtest.json'),
    }
    manifest = {
        'freeze_utc': now(),
        'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'branch': 'ai-lab-development',
        'label_for_every_result': 'retrospective robustness evidence only',
        'frozen_strategy': 'AlphaBreakout',
        'phase4a_central_match': True,
        'parameters': {
            'breakout_lookback_hours': 24, 'breakout_atr_buffer': .1,
            'natr_condition': 'current NATR14 > prior 24h NATR14 mean (mean shifted one candle)',
            'relative_volume_min': 1.2, 'relative_volume': 'current volume / prior 24h mean volume',
            'close_location_min': .75, 'exit_prior_low_hours': 12,
            'roi': .05, 'stoploss': -.05, 'trailing_stop': False,
        },
        'entry': 'Close above prior 24h high + 0.1 ATR14, NATR expansion, relative volume >=1.2, close-location >=0.75, positive volume. Signal candle closes before engine entry on next candle.',
        'exit': 'Close below prior 12h low, plus fixed ROI / stoploss engine exits.',
        'indicator_formulas': 'EMA adjust=False; ATR true range EMA alpha=1/14; all rolling high/low and volume references shifted one candle; no centered window, forward fill, or future return.',
        'fee_each_side': .001, 'pairs': ['BTC/USDT', 'ETH/USDT'], 'timeframe': '1h',
        'execution': {'spot': True, 'dry_run': True, 'wallet_usdt': 1000, 'stake_usdt': 100, 'max_open_trades': 2,
                      'entry_order': 'limit', 'exit_order': 'limit', 'stoploss_order': 'market', 'next_candle_execution': True},
        'periods': PERIODS,
        'data_plan': 'Download 2022-12-01 through 2026-04-01 exclusive from public Binance for warmup and periods A-C; append exact existing sealed D candles. No data beyond 2026-09-01. No results selected or tuned.',
        'interpretation': 'All A-D periods were previously observed in project phases; no result is a pristine or untouched holdout. Results may not change this frozen alpha.',
        'frozen_source_hashes': source_hashes,
        'validation_source_hashes': validation_hashes,
        'forbidden_after_freeze': ['parameter changes', 'additional indicators', 'alternative models', 'ML', 'FreqAI', 'threshold selection', 'period selection'],
    }
    save(HERE/'frozen-manifest.json', manifest)
    log('alpha_breakout_frozen', manifest_sha256=sha(HERE/'frozen-manifest.json'), later_results_accessed=False)


if __name__ == '__main__':
    main()
