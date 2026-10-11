# Risk-adjusted cost of East Mediterranean energy corridors

Model code and data for:

> Pappas, K., Ashkanani, Z. (2026). *Electricity corridors do not escape geopolitics: a risk-adjusted cost comparison of gas and power routes from the Eastern Mediterranean to the EU.* Submitted to *Energy Policy*.

The model compares the expected cost of a megawatt-hour of firm electricity delivered to the Greek grid (real EUR 2025) across the EastMed pipeline, Levant gas liquefied in Egypt, the Great Sea Interconnector, the GREGY and EuroAfrica cables, and Greek renewables. Risk enters through financing premia, delay and abandonment probabilities, route kilometres inside overlapping maritime claims, and observed Israeli field shutdowns and Egyptian export diversions, propagated through 20,000 Monte Carlo draws with a Sobol sensitivity analysis.

## Options and risk layers

| Model ID | Option |
|---|---|
| `O1_EastMed` | EastMed gas pipeline |
| `O2_LNG_Egypt` | Levant gas liquefied in Egypt |
| `O3_GSI` | Great Sea Interconnector (HVDC cable) |
| `O4a_GREGY` | GREGY cable (Egypt–Greece) |
| `O4b_EuroAfrica` | EuroAfrica cable |
| `O5_Greek_RE` | Greek renewables (benchmark) |

Each option's expected cost is reported at five cumulative layers:

- **L0 base:** planned cost and schedule, every asset financed as a Greek domestic asset.
- **L1 cost of capital:** partner-country risk premia and default spreads, weighted by the jurisdictions a route crosses; generation financed at the source country's WACC.
- **L2 execution:** reference-class cost overrun, delay, post-FID abandonment and technical outages.
- **L3 conflict:** war shutdowns of Israeli supply, Israeli export curtailment, and Egyptian diversion of gas and power exports.
- **L4 maritime:** contested-waters WACC premium, contested delay and abandonment, and interference outages.

The value of resolving the maritime disputes is L4 − L3.

## Repository layout

| Path | Contents |
|---|---|
| `config/parameters.csv` | Parameter register: all 151 parameters with value, range, distribution, source ID and status (`sourced`, `judgement`, `design`, `unused`) |
| `config/corridors.yaml` | Route length, capacity, converter count, jurisdiction weights and contested-route share per corridor |
| `src/emcorr/` | Model package: `constants` (unit conversions), `finance` (WACC, levelised cost, risk adjustments), `options` (cost chains and risk layers), `egypt` (gas balance and export diversion), `geo` (route exposure), `mc` (sampling, Sobol) |
| `scripts/` | Numbered pipeline (see below); figure style in `figlib.py` |
| `tests/` | Unit tests |
| `data/raw/` | Primary data as downloaded, with `MANIFEST.csv` (source, URL, access date, size, SHA-256) |
| `data/processed/` | Processed inputs read by the model, including the contested-zone and route geometry |
| `data/legacy/` | Damodaran country risk premia, 2022 and 2024 editions, for the premium panel |
| `docs/source_register.csv` | Bibliographic record for every `WEB:` and data source ID used in the register |
| `docs/research/` | Source tables behind the register: corridor parameters (`A_`), route and claim coordinates (`B_`), risk reference classes (`C_`) and country series for Israel, Egypt, Cyprus and EU demand (`R1`–`R4`), each row with source title, URL, access date, page or table locator, confidence and verification notes |
| `outputs/tables/` | Model results (deterministic costs by layer, Monte Carlo summary, risk decomposition, Sobol indices, scenarios, break-even sweep, cost-of-capital penalty, route exposure) |
| `outputs/data/mc_draws.npz` | Monte Carlo draws by option and layer |
| `outputs/figures/` | Main figures (Fig. 1–8) and supplementary figures (Fig. S1–S19) as PNG; the scripts also write EPS versions |

Source IDs in `config/parameters.csv` resolve as follows: `A:<id>` is a row of `docs/research/A_corridor_parameters.csv`, `C:<id>` of `docs/research/C_risk_parameters.csv`, `IL:`, `EG:`, `CY:` and `EU:` of `docs/research/R1_israel.csv`, `R2_egypt.csv`, `R3_cyprus.csv` and `R4_eu_demand.csv`, and every other ID is an entry of `docs/source_register.csv`.

## Requirements

Python 3.13 with the packages in `requirements.txt` (the versions used for the published results):

```bash
pip install -r requirements.txt
```

## Reproducing the results

The processed inputs and the parameter register are included, so the results can be reproduced directly from the repository root:

```bash
python -m unittest discover -s tests
python scripts/10_run_model.py --n 20000 --sobol 1024
python scripts/11_scenarios.py --n 20000
python scripts/30_cost_of_capital.py
python scripts/20_figures.py
python scripts/21_si_figures.py
```

Sampling is seeded (Latin hypercube and Sobol, seed 2026), so the tables in `outputs/tables/` are reproduced exactly. `10_run_model.py` writes the deterministic and Monte Carlo results, risk decomposition, break-even sweep and Sobol indices; `11_scenarios.py` the scenarios; `30_cost_of_capital.py` the cost-of-capital penalty; `20_figures.py` and `21_si_figures.py` the main and supplementary figures.

The parameter register is rebuilt from the processed data and the source tables with:

```bash
python scripts/05_update_parameters.py
python scripts/06_apply_research_params.py
```

### Rebuilding the processed data

| Script | Step |
|---|---|
| `02_download_data.py`, `02b_pvgis.py` | Download the open raw data (current releases may differ from the archived files; `MANIFEST.csv` gives the hashes of the files used) |
| `03_route_exposure.py`, `03b_routes.py` | Contested zones and route exposure from the claim and route coordinates; updates `config/corridors.yaml` |
| `04_process_raw.py` | Exchange rates, deflator, Damodaran premia and tax rates, Ember capacity factors, IMF fiscal data, gas prices |
| `04b_extract_ei.py`, `04c_process_gem.py`, `04d_extract_irena_wacc.py` | Energy Institute gas balance, Global Energy Monitor reference class and EastMed route, IRENA WACC benchmarks (need the manual downloads below) |
| `01_init_parameter_register.py` | Initial register (provisional values, replaced by `05` and `06`) |
| `smoke_test.py` | Quick check of the model chain |

Three inputs are cited rather than redistributed, under their providers' terms. To rebuild from them, place the files in `data/raw/manual/` under the names below:

| File | Source |
|---|---|
| `GEM-GGIT-Gas-Pipelines-2025-11.xlsx` and `GEM-GGIT-Gas-Pipelines-2025-11.zip` (unzip into `data/raw/manual/GEM-GGIT-Gas-Pipelines-2025-11/`) | Global Energy Monitor, Global Gas Infrastructure Tracker, pipelines, November 2025 release (https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker/) |
| `GEM-GGIT-LNG-Teminals-2025-09.xlsx` | Global Energy Monitor, Global Gas Infrastructure Tracker, LNG terminals, September 2025 release |
| `Statistical Review of World Energy.pdf` | Energy Institute, Statistical Review of World Energy 2026 (https://www.energyinst.org/statistical-review) |
| `IRENA_TEC_RPGC_in_2025_data_file_2026.xlsx` | IRENA (2026), Renewable power generation costs in 2025, data file, Table A2 (https://www.irena.org/Publications) |

Their processed extracts, which the model reads, are included in `data/processed/`.

## Data sources and licences

Third-party files in `data/raw/` keep their original licences and should be cited to their providers: Ember Yearly Electricity Data (CC BY 4.0), Marine Regions Maritime Boundaries v12 (CC BY 4.0), PVGIS (European Commission Joint Research Centre), Damodaran country risk premium datasets, World Bank Commodity Price Data (Pink Sheet, CC BY 4.0), IMF DataMapper, ECB exchange rates, Eurostat HICP, and Natural Earth (public domain). Source, URL and access date of each file are in `data/raw/MANIFEST.csv`. The CBAM default values of Implementing Regulation (EU) 2025/2621 derive from International Energy Agency data under a non-commercial licence and are cited, not redistributed.

## Licence

The code is released under the MIT licence (`LICENSE`). The parameter register, source tables, processed data, results and figures produced by the authors are released under CC BY 4.0.

## Citation

Please cite the article above and this repository (see `CITATION.cff`).
