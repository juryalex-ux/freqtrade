"""Freeze hypothesis definitions and rejection rules before seeing research outcomes."""
import json
import shutil
import subprocess
from common import HERE,ROOT,CENTRAL,VARIANTS,BASELINE_SHA,guard,save,sha,now,log


def main():
    guard()
    assert not (HERE/'protocol.json').exists(),'Do not overwrite frozen design'
    definitions={
        'AlphaTrend':{'entry':'EMA20>EMA50; EMA50 rising over6h; efficiency20>=0.30; prior low<=prior EMA20; current close>EMA20; 3h return>0',
                      'exit':'close below EMA50','perturbation':{'parameter':'efficiency_min','values':[.25,.30,.35]},
                      'rationale':'Buy a recovered pullback in an established efficient uptrend; 0.30 rejects very choppy paths.'},
        'AlphaBreakout':{'entry':'close above prior24h high+0.1ATR14; NATR above prior24h mean; relative volume>=1.2; close in top25% of candle',
                         'exit':'close below prior12h low','perturbation':{'parameter':'breakout_window','values':[20,24,28]},
                         'rationale':'One-day breakout with modest volatility/volume expansion and a strong close; buffered close rejects wick-only breakouts but cannot eliminate false breakouts.'},
        'AlphaReversion':{'entry':'close<EMA20-1.5ATR14; RSI14<30; close>prior close; efficiency20<0.25; abs EMA50 six-hour slope<0.005; NATR14<0.015',
                          'exit':'close>=EMA20 or RSI14>=50','perturbation':{'parameter':'stretch_atr','values':[1.35,1.5,1.65]},
                          'rationale':'Volatility-scaled oversold rebound restricted to weak-trend, non-extreme-volatility conditions; cautious entry can yield few trades.'},
        'AlphaSqueeze':{'entry':'At least one of prior6 candles had BB20 total width(4 population std) < Keltner total width(3ATR14); close breaks prior20h high; NATR rising; relative volume>=1.2',
                        'exit':'close below EMA20','perturbation':{'parameter':'keltner_multiplier','values':[1.35,1.5,1.65]},
                        'rationale':'Prior compression followed by directional expansion. Prior-only squeeze test avoids calling the breakout itself compression.'},
        'AlphaMomentum':{'entry':'24h and72h returns positive; up-close fraction24>=0.60; relative volume>=1.2; bullish candle; close in top30%; close above prior6h high',
                         'exit':'24h return<=0 or close below EMA20','perturbation':{'parameter':'persistence_min','values':[.55,.60,.65]},
                         'rationale':'Require persistent buying across short/medium horizons, participation and strong candle structure.'}}
    for folder in ['raw','data','results','reports','audits']:(HERE/folder).mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'ai_lab/strategies/LabBaseline.py',HERE/'strategies/LabBaseline.py')
    assert sha(HERE/'strategies/LabBaseline.py')==BASELINE_SHA
    config=json.loads((ROOT/'ai_lab/configs/backtest.json').read_text())
    assert config['dry_run'] is True and config['exchange']['pair_whitelist']==['BTC/USDT','ETH/USDT']
    config['user_data_dir']=str(HERE); config['datadir']=str(HERE/'data')
    save(HERE/'backtest.json',config)
    protocol={'frozen_utc':now(),'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'candidates':definitions,'central_candidates':CENTRAL,'variants':VARIANTS,'permanent_reference':'LabBaseline',
        'baseline_sha256':BASELINE_SHA,'config_sha256':sha(HERE/'backtest.json'),
        'data_start':'2018-12-01','scoring_start':'2019-01-01','data_end_exclusive':'2023-01-01',
        'periods':{'initial_design':['2019-01-01','2021-01-01'],'internal_refinement':['2021-01-01','2022-01-01'],'internal_evaluation':['2022-01-01','2023-01-01']},
        'walk_forward':[{'past':'2019-2020','evaluate':2021},{'past':'2019-2021','evaluate':2022}],
        'walk_forward_method':'Deterministic rules frozen before any result; no fitting/refitting. Past periods provide context only; no rules change after2021. Annual portfolio resets with past-only240h warmup and boundary force closes.',
        'execution':{'pairs':['BTC/USDT','ETH/USDT'],'timeframe':'1h','spot':True,'wallet':1000,'stake':100,'max_open_trades':2,'fee_each_side':.001,
            'roi':.05,'stoploss':-.05,'entry':'First candle of true condition, positive volume; Freqtrade executes next-candle entry; family exit wins same-candle collision per engine',
            'exit':'Family structural exit plus fixed baseline-like ROI5% / stoploss5%; no trailing, ML, custom fitting, or exit tuning'},
        'indicators':'EMA adjust=False; ATR EMA alpha1/14; RSI EMA gains/losses alpha1/14; efficiency abs20h change/sum abs1h changes; relative volume current / prior24 mean; rolling breakout high/low always shifted1. No centered windows/future fills.',
        'perturbation_policy':'One named parameter per family, three declared values. Report all; never select best value or replace central candidate.',
        'acceptance':{'positive_expectancy_years_min':3,'pf_above_one_years_min':3,'aggregate_net_positive':True,
            'minimum_total_trades':100,'minimum_trades_each_year':15,'max_yearly_wallet_drawdown_pct':10,
            'largest_positive_year_share_max':.65,'both_pairs_aggregate_positive':True,
            'internal_2022_net_positive':True,'both_perturbations_total_positive':True,'each_perturbation_positive_years_min':2},
        'acceptance_note':'Research continuation only, not paper/live approval. Criteria account for 100USDT fixed stake and1000wallet; no pristine holdout claim for2019-2022 which were used in earlier research.',
        'consumed_periods':'No 2023+ data or result files read by these scripts. Past conversational knowledge cannot be erased; all definitions fixed without a feedback loop from those outcomes.',
        'code_hashes':{p.relative_to(HERE).as_posix():sha(p) for p in HERE.rglob('*.py')}}
    save(HERE/'protocol.json',protocol)
    log('design_frozen',protocol_sha256=sha(HERE/'protocol.json'),candidate_count=5,variants_per_family=3,consumed_period_results_read=False)


if __name__=='__main__': main()
