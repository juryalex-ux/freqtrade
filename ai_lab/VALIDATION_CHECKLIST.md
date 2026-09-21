# Review gates before a separately authorized live phase

All items remain unchecked until supported by recorded evidence. Completing this
list does not enable or authorize live trading.

- [ ] Confirm branch, revision, dependencies and configuration are reproducible.
- [ ] Confirm only BTC/USDT and ETH/USDT spot data are used and inspect missing candles.
- [ ] Run and archive the baseline backtest with actual data coverage and fee assumptions.
- [ ] Run Freqtrade lookahead-analysis and recursive-analysis; investigate every finding.
- [ ] Evaluate separate out-of-sample periods and different market conditions.
- [ ] Compare each experiment with the unchanged baseline; document all parameter searches.
- [ ] Assess fees, spreads, slippage, liquidity and realistic order execution.
- [ ] Agree measurable limits for drawdown, exposure, position size and acceptable losses.
- [ ] Complete a reviewed dry-run period; reconcile signals, fills, fees and trade state.
- [ ] Exercise restart, network loss, rejected orders, database recovery and manual shutdown.
- [ ] Verify monitoring, alerts, incident ownership and an emergency stop procedure.
- [ ] Verify exchange availability, account eligibility and applicable requirements.
- [ ] Review future credential storage, least privilege, withdrawal restrictions and secret scanning.
- [ ] Independently review configuration precedence and ensure no unintended environment overrides.
- [ ] Obtain explicit user authorization for a separate live phase and its capital limits.

Do not change Phase 1's `dry_run: true` settings to satisfy this checklist.
