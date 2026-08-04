# 📊 AEMO NEM — Comprehensive Data Tables & Datasets Reference

> **Sources verified:** NEMWeb `/Reports/CURRENT/` directory (90+ report folders), MMSDM Historical Data Archive CTL file manifest (2026-06), MMS Electricity Data Model Report, NEMOSIS Python package documentation.
> **Last verified:** 2026-07-30
>
> **Legend:**
> - ✅ **In your database** — already loaded into this app's PostgreSQL (local table name shown)
> - 🟢 **Live** — current data can be pulled any time from NEMWeb `Reports/CURRENT/` (minutes of latency)
> - 🟡 **Recent** — published daily / next-day via NEMWeb
> - ⚪ **Archive / reference** — monthly MMSDM archive or periodic publications (weeks of lag)

---

## Overview

AEMO publishes NEM data through three main channels:
1. **NEMWeb** (`nemweb.com.au/Reports/`) — real-time and near-real-time CSV/ZIP reports
2. **MMSDM Monthly Archive** (`nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/`) — full monthly historical SQLLoader archives (~235 distinct table types)
3. **Static/Registration files** — Excel workbooks published periodically (e.g., NEM Registration and Exemption List)

---

## 1. 🔄 DISPATCH — 5-Minute Real-Time (MMS)

> **Availability:** 🟢 **Live** — new CSVs every 5 min via `Reports/CURRENT/DispatchIS_Reports/` and `Dispatch_SCADA/`

Published every 5 minutes via `DispatchIS_Reports/` and in the MMSDM monthly archive.

| Table | Description | Frequency |
|-------|-------------|-----------|
| `DISPATCHPRICE` ✅ *(in your DB as `dispatch_price`)* | Regional reference prices (RRP) and FCAS prices for each 5-min dispatch interval, per region and intervention flag | 5-min |
| `DISPATCHREGIONSUM` ✅ *(in your DB as `dispatch_region_sum`)* | Regional summary: cleared demand, available generation, FCAS requirements, losses, surplus reserves, AGC status | 5-min |
| `DISPATCHLOAD` | Per-DUID dispatch solution: targets, enablement flags, FCAS enablement, bid details (most data-intensive table) | 5-min |
| `DISPATCHCONSTRAINT` | Active constraint solution: marginal value, violation degree, LHS/RHS for each binding/violated constraint | 5-min |
| `DISPATCHINTERCONNECTORRES` | Interconnector dispatch solution: MW flow, losses, reserve, marginal loss factor | 5-min |
| `DISPATCHCASESOLUTION` | Dispatch case run metadata: solution status, OCD (over-constrained dispatch) status, solver stats | 5-min |
| `DISPATCH_UNIT_SCADA` ✅ *(in your DB as `generation_fuel (aggregated by fuel type)`)* | Raw SCADA-measured output for each generating unit/load (MW) — published in `Dispatch_SCADA/` | 5-min |
| `DISPATCH_LOCAL_PRICE` | Local marginal price at connection point for units with local pricing difference from RRP | 5-min |
| `DISPATCH_INTERCONNECTION` | Flow data for each interconnector including losses and marginal loss factors | 5-min |
| `DISPATCH_MNSPBIDTRK` | Market Network Service Provider (MNSP) bid tracking per dispatch interval | 5-min |
| `DISPATCH_FCAS_REQ_CONSTRAINT` | Constraint-level FCAS requirement data from the FCAS processor (FPP enhancement) | 5-min |
| `DISPATCH_FCAS_REQ_RUN` | FCAS processor run details — parent table for `DISPATCH_FCAS_REQ_CONSTRAINT` | 5-min |
| `DISPATCHOFFERTRK` | Tracks which offer version was used in each dispatch run per DUID | 5-min |
| `DISPATCHABLEUNIT` | Reference table: list of all registered dispatchable units (DUIDs) | Static/Updated |
| `MCC_CASESOLUTION` | Market Clearing Constraint (MCC) case solution metadata | 5-min |
| `MCC_CONSTRAINTSOLUTION` | MCC constraint solution results per constraint | 5-min |
| `DISPATCH_NEGATIVE_RESIDUE` | Negative residue dispatch results (published via `DISPATCH_NEGATIVE_RESIDUE/`) | 5-min |
| `DISPATCHFCST` | Short dispatch forecast (near-term load forecasts) | 5-min |

---

## 2. ⏩ P5MIN — 5-Minute Pre-Dispatch Forecast

> **Availability:** 🟢 **Live** — new CSVs every 5 min via `Reports/CURRENT/P5_Reports/`

Published every 5 minutes via `P5_Reports/` and `P5MINFCST/`. Covers the next ~1 hour in 5-min intervals.

| Table | Description | Frequency |
|-------|-------------|-----------|
| `P5MIN_CASESOLUTION` | P5MIN case solution metadata and solver statistics | 5-min |
| `P5MIN_REGIONSOLUTION` | Regional price and demand forecast for each 5-min interval over ~1 hour | 5-min |
| `P5MIN_CONSTRAINTSOLUTION` | Constraint solution for P5MIN runs | 5-min |
| `P5MIN_INTERCONNECTORSOLN` | Interconnector solution for P5MIN runs | 5-min |
| `P5MIN_INTERSENSITIVITIES` | Interconnector sensitivity prices for demand scenarios in P5MIN | 5-min |
| `P5MIN_PRICESENSITIVITIES` | Price sensitivity analysis for demand scenarios in P5MIN | 5-min |
| `P5MIN_LOCAL_PRICE` | Local pricing adjustments in P5MIN | 5-min |
| `P5MIN_FCAS_REQ_CONSTRAINT` | FCAS requirement constraint details for P5MIN (FPP enhancement) | 5-min |
| `P5MIN_FCAS_REQ_RUN` | FCAS processor run metadata for P5MIN | 5-min |
| `P5MIN_SCENARIODEMAND` | Demand scenario inputs used in P5MIN sensitivity analysis | 5-min |
| `P5MIN_SCENARIODEMANDTRK` | Tracking table for P5MIN scenario demand versions | 5-min |

---

## 3. 📅 PRE-DISPATCH (PREDISPATCH) — 30-Minute Intervals

> **Availability:** 🟢 **Live** — every 30 min via `Reports/CURRENT/PredispatchIS_Reports/`

Published every 30 minutes via `Predispatch_Reports/`, `PredispatchIS_Reports/`, `Predispatch_Sensitivities/`. Covers ~40 hours ahead in 30-min intervals.

| Table | Description | Frequency |
|-------|-------------|-----------|
| `PREDISPATCHPRICE` ✅ *(in your DB as `predispatch_price`)* | Pre-dispatch regional prices (RRP + FCAS prices) for all future 30-min intervals | 30-min |
| `PREDISPATCHREGIONSUM` ✅ *(in your DB as `predispatch_regionsum + _part1–3`)* | Regional summary for pre-dispatch: demand forecasts, FCAS requirements, surplus, etc. | 30-min |
| `PREDISPATCHLOAD` | Pre-dispatch per-DUID solution: targets, FCAS enablement (large table) | 30-min |
| `PREDISPATCHCONSTRAINT` | Pre-dispatch constraint solution: marginal values for binding constraints | 30-min |
| `PREDISPATCHINTERCONNECTORRES` ✅ *(in your DB as `predispatch_interconnector (+ parts, loading now)`)* | Pre-dispatch interconnector solution: flow, losses, MWF | 30-min |
| `PREDISPATCHCASESOLUTION` | Pre-dispatch run metadata | 30-min |
| `PREDISPATCHPRICESENSITIVITIES` | Price sensitivities to demand changes for each pre-dispatch period | 30-min |
| `PREDISPATCH_LOCAL_PRICE` | Local pricing in pre-dispatch | 30-min |
| `PREDISPATCH_MNSPBIDTRK` | MNSP bid tracking for pre-dispatch | 30-min |
| `PREDISPATCHOFFERTRK` | Offer version tracking for pre-dispatch | 30-min |
| `PREDISPATCHSCENARIODEMAND` | Demand scenario inputs for pre-dispatch sensitivity runs | 30-min |
| `PREDISPATCHSCENARIODEMANDTRK` | Scenario demand version tracking for pre-dispatch | 30-min |
| `PD_FCAS_REQ_CONSTRAINT` | FCAS requirement constraint details for pre-dispatch (FPP enhancement) | 30-min |
| `PD_FCAS_REQ_RUN` | FCAS processor run metadata for pre-dispatch | 30-min |

---

## 4. 📆 PD7DAY — 7-Day Pre-Dispatch

> **Availability:** 🟢 **Live** — every 30 min via `Reports/CURRENT/PD7Day/`

Published every 30 minutes via `PD7Day/`. Covers 7 days ahead in 30-min intervals.

| Table | Description | Frequency |
|-------|-------------|-----------|
| `PD7DAY_CASESOLUTION` | 7-day pre-dispatch case solution metadata | 30-min |
| `PD7DAY_PRICESOLUTION` | 7-day pre-dispatch regional prices per 30-min interval | 30-min |
| `PD7DAY_CONSTRAINTSOLUTION` | 7-day constraint solution | 30-min |
| `PD7DAY_INTERCONNECTORSOLUTION` | 7-day interconnector solution | 30-min |
| `PD7DAY_MARKET_SUMMARY` | Market-level summary for 7-day pre-dispatch | 30-min |

---

## 5. 💹 TRADING — 30-Minute Settlement Intervals

> **Availability:** 🟢 **Live** — every 5 min via `Reports/CURRENT/TradingIS_Reports/`

Published every 5 minutes (updated at end of trading interval) via `TradingIS_Reports/` and `Next_Day_Trading/`.

| Table | Description | Frequency |
|-------|-------------|-----------|
| `TRADINGPRICE` | Trading interval prices: RRP and FCAS prices averaged/settled over the 30-min trading interval | 30-min |
| `TRADINGINTERCONNECT` | Interconnector MW flows and losses for the trading interval (metered/settlement values) | 30-min |
| `AVERAGEPRICE30` | Volume-weighted average price over 30-min trading intervals | 30-min |
| `TRADINGREGIONSUM`* | Trading interval regional summary (demand, generation, etc.) — published in TradingIS_Reports | 30-min |
| `Trading_Cumulative_Price` | Cumulative price tracking for market price cap events | 5-min (cumulative) |

> *`TRADINGREGIONSUM` is published within the TradingIS_Reports ZIP but may not appear separately in the MMSDM CTL archive.

---

## 6. 📊 DISPATCH UNIT SCADA (Raw Metering)

> **Availability:** 🟢 **Live** — every 5 min via `Reports/CURRENT/Dispatch_SCADA/`

| Table / Report | Description | Frequency |
|----------------|-------------|-----------|
| `DISPATCH_UNIT_SCADA` ✅ *(in your DB as `generation_fuel (aggregated by fuel type)`)* | SCADA-measured actual output (MW) per DUID — the "actuals" file | 5-min |
| `Dispatch_SCADA` (report dir) | Same data published via `nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/` | 5-min |
| `INTERMITTENT_GEN_SCADA` | SCADA output specifically for intermittent generators (wind/solar farms) | 5-min |
| `Next_Day_Intermittent_Gen_Scada` | Next-day published intermittent gen SCADA | Daily (next-day) |

---

## 7. 🌤️ INTERMITTENT GENERATION & DEMAND SENSITIVITY

> **Availability:** 🟡 **Recent** — mostly next-day via `Next_Day_Intermittent_DS/`

Published via `Next_Day_Intermittent_DS/` and in MMSDM archive.

| Table | Description | Frequency |
|-------|-------------|-----------|
| `INTERMITTENT_DS_PRED` | Intermittent generator demand side (DS) predictions | 30-min |
| `INTERMITTENT_DS_RUN` | Run metadata for intermittent demand sensitivity | 30-min |
| `INTERMITTENT_FORECAST_TRK` | Tracking table for intermittent generation forecasts | Per run |
| `INTERMITTENT_GEN_LIMIT` | Generation limits for intermittent units | Updated |
| `INTERMITTENT_GEN_LIMIT_DAY` | Daily generation limit submissions from intermittent generators | Daily |
| `INTERMITTENT_CLUSTER_AVAIL` | Cluster-level availability submissions for intermittent generators | Per period |
| `INTERMITTENT_CLUSTER_AVAIL_DAY` | Daily cluster availability | Daily |

---

## 8. ☀️ ROOFTOP SOLAR PV

> **Availability:** 🟢 **Live** — every 30 min via `Reports/CURRENT/ROOFTOP_PV/ACTUAL/` and `.../FORECAST/`

Published via `ROOFTOP_PV/` directory and in MMSDM archive.

| Table | Description | Frequency |
|-------|-------------|-----------|
| `ROOFTOP_PV_ACTUAL` | Actual estimated rooftop PV generation by region (MW, derived from meter data/models) | 30-min |
| `ROOFTOP_PV_FORECAST` | Forecast rooftop PV generation for upcoming periods by region | 30-min |

---

## 9. 📋 PDPASA — Pre-Dispatch PASA

> **Availability:** 🟢 **Live** — every 30 min via `Reports/CURRENT/PDPASA/`

Published via `PDPASA/` and `PDPASA_DUIDAvailability/`. Reliability assessment for next ~48 hours.

| Table | Description | Frequency |
|-------|-------------|-----------|
| `PDPASA_CASESOLUTION` | PDPASA run metadata | 30-min |
| `PDPASA_REGIONSOLUTION` | PDPASA regional results: reserve margins, USE (Unserved Energy), capacity | 30-min |
| `PDPASA_CONSTRAINTSOLUTION` | PDPASA constraint solution | 30-min |
| `PDPASA_INTERCONNECTORSOLN` | PDPASA interconnector solution | 30-min |
| `PDPASA_DUIDAVAILABILITY` | Per-DUID availability submitted for PDPASA | 30-min |

---

## 10. 📈 STPASA — Short-Term PASA

> **Availability:** 🟢 **Live** — roughly 2-hourly via `Reports/CURRENT/Short_Term_PASA_Reports/`

Published via `Short_Term_PASA_Reports/` and `STPASA_DUIDAvailability/`. Reliability assessment for next ~7 days.

| Table | Description | Frequency |
|-------|-------------|-----------|
| `STPASA_CASESOLUTION` | STPASA run metadata | ~30-min |
| `STPASA_REGIONSOLUTION` | STPASA regional results: reserve margins, reliability metrics, max demand forecasts | ~30-min |
| `STPASA_CONSTRAINTSOLUTION` | STPASA constraint solution | ~30-min |
| `STPASA_INTERCONNECTORSOLN` | STPASA interconnector solution | ~30-min |
| `STPASA_DUIDAVAILABILITY` | Per-DUID availability for short-term PASA | ~30-min |

---

## 11. 📉 MTPASA — Medium-Term PASA

> **Availability:** 🟡 **Recent** — weekly via `Medium_Term_PASA_Reports/`; 7-day outlook daily

Published via `Medium_Term_PASA_Reports/`, `MTPASA_DUIDAvailability/`, `MTPASA_RegionAvailability/`. Reliability assessment for 2 years ahead.

| Table | Description | Frequency |
|-------|-------------|-----------|
| `MTPASA_CASERESULT` | MTPASA case-level result metadata | Weekly |
| `MTPASA_REGIONRESULT` | MTPASA per-region results: reserve shortfall, reliability metrics, USE probability | Weekly |
| `MTPASA_REGIONSUMMARY` | MTPASA regional summary statistics | Weekly |
| `MTPASA_REGIONITERATION` | Per-iteration MTPASA results (Monte Carlo runs) | Weekly |
| `MTPASA_CONSTRAINTRESULT` | MTPASA constraint binding results | Weekly |
| `MTPASA_CONSTRAINTSUMMARY` | MTPASA constraint summary | Weekly |
| `MTPASA_INTERCONNECTORRESULT` | MTPASA interconnector flow results | Weekly |
| `MTPASA_LOLPRESULT` | Loss-of-Load Probability (LOLP) results from MTPASA | Weekly |
| `MTPASA_DUIDAVAILABILITY` | Per-DUID availability submissions for MTPASA | Weekly |
| `MTPASA_REGIONAVAILABILITY` | Regional availability aggregations for MTPASA | Weekly |
| `MTPASA_REGIONAVAIL_TRK` | Tracking for MTPASA region availability versions | Weekly |
| `MTPASA_RESERVELIMIT` | Reserve limits applied in MTPASA runs | Per run |
| `MTPASA_RESERVELIMIT_REGION` | Reserve limit per region for MTPASA | Per run |
| `MTPASA_RESERVELIMIT_SET` | Reserve limit sets for MTPASA | Per run |
| `SEVENDAYOUTLOOK_FULL` / `SEVENDAYOUTLOOK_PEAK` | 7-day supply–demand outlook (full and peak versions) | Daily |
| `PasaSnap` (report dir) | Snapshot of PASA results | Per run |

---

## 12. 💰 BIDDING & OFFERS

> **Availability:** 🟡 **Recent** — public next day ~04:00 AEST via `Next_Day_Offer_Energy/` / `Yesterdays_Bids_Reports/`

Published in `Yesterdays_Bids_Reports/`, `Next_Day_Offer_Energy/`, `Next_Day_Offer_FCAS/` (and sparse versions). Participant bidding data (confidential on day, public next day).

| Table | Description | Frequency |
|-------|-------------|-----------|
| `BIDDAYOFFER` ✅ *(in your DB as `bid_prices`)* | Day-ahead offer header for energy/FCAS: max availability, fixed load, enablement min/max | Daily (public next day) |
| `BIDDAYOFFER_D` | De-identified/public version of BIDDAYOFFER | Daily (next day) |
| `BIDOFFERPERIOD` ✅ *(in your DB as `bid_availability`)* | Per-period energy/FCAS bid: 10 price-quantity bands per DUID per trading interval | Daily (public next day) |
| `BIDPEROFFER_D` | De-identified/public version of BIDOFFERPERIOD | Daily (next day) |
| `BIDDUIDDETAILS` | Additional DUID-level details for bidding (e.g., PASAAVAILABILITY, MINIMUMLOAD) | Daily |
| `BIDDUIDDETAILSTRK` | Tracking/versioning for BIDDUIDDETAILS | Daily |
| `BIDTYPES` | Reference: bid types (ENERGY, RAISE6SEC, RAISE60SEC, RAISE5MIN, RAISEREG, LOWER6SEC, etc.) | Static |
| `BIDTYPESTRK` | Tracking for bid types versions | Static |
| `MNSP_DAYOFFER` | MNSP day-offer: available capacity per trading interval for each MNSP | Daily |
| `MNSP_BIDOFFERPERIOD` | MNSP bid per period | Daily |
| `Bidmove_Complete` (report dir) | Complete bid movement log | As submitted |
| `Bidmove_Summary` (report dir) | Summary of bid movements | As submitted |
| `Yesterdays_Bids_Reports` (dir) | Previous day's bid data (all units) | Daily |
| `Yesterdays_MNSPBids_Reports` (dir) | Previous day's MNSP bids | Daily |
| `NEXT_DAY_AVAIL_SUBMISS_CLUSTER` | Next-day availability submission at cluster level | Daily |
| `NEXT_DAY_AVAIL_SUBMISS_DAY` | Next-day daily availability submission | Daily |

---

## 13. ⚡ FCAS — Frequency Control Ancillary Services

> **Availability:** Mixed — FCAS prices/enablement are 🟢 live inside the 5-min dispatch reports; `SET_*` settlement-recovery tables are ⚪ weekly+

| Table | Description | Frequency |
|-------|-------------|-----------|
| `FCAS_REGU_USAGE_FACTORS` | Regulation FCAS usage factors per unit (actual raise/lower utilisation) | Per run |
| `FCAS_REGU_USAGE_FACTORS_TRK` | Tracking for FCAS regulation usage factors versions | Per run |
| `SET_FCAS_REGULATION_TRK` | Settlement tracking for regulation FCAS | Settlement |
| `SET_ANCILLARY_SUMMARY` | Settlement summary for ancillary services FCAS payments | Settlement |
| `SETFCASREGIONRECOVERY` | Regional recovery amounts for FCAS costs in settlement | Settlement |
| `SET_FCAS_CLAWBACK_REQ` | FCAS clawback requirements for settlement | Settlement |
| `SET_FCAS_CLAWBACK_RUN_TRK` | Tracking for FCAS clawback settlement runs | Settlement |
| `SET_NMAS_RECOVERY_RBF` | NMAS (Non-Market Ancillary Service) recovery amounts | Settlement |
| `ANCILLARY_RECOVERY_SPLIT` | How FCAS recovery costs are split between generators/loads | Settlement |
| `ANCILLARY_SERVICES_REPORTS` (dir) | Weekly ancillary services register (FCAS providers by service type) | Weekly |
| `Ancillary_Services_Payments` (dir) | Published FCAS payment summaries | Monthly |
| `Vwa_Fcas_Prices` (dir) | Volume-weighted average FCAS prices by region and service type | Daily |
| `ELEMENTS_FCAS_4_SECOND` | Static reference table: elements used in 4-second FCAS measurement | Static |
| `VARIABLES_FCAS_4_SECOND` | Static reference table: variables measured in 4-second FCAS data | Static |
| `FCAS_4_SECOND` (via NEMOSIS) | 4-second FCAS measurement data (causer pays basis) — from AEMO portal | 4-second |
| `SSM_ENABLEMENT_COSTS` | System strength service (SSM) enablement costs | Per event |
| `SSM_ENABLEMENT_PERIOD` | System strength service enablement period details | Per event |
| `GDINSTRUCT` | Generator dispatch instructions issued by AEMO (e.g., directions) | As issued |
| `INSTRUCTIONTYPE` | Reference: types of dispatch instructions | Static |
| `INSTRUCTIONSUBTYPE` | Reference: sub-types of dispatch instructions | Static |
| `VOLTAGE_INSTRUCTION` | Voltage control instructions issued to generators | As issued |
| `VOLTAGE_INSTRUCTION_TRK` | Tracking for voltage instruction versions | As issued |
| `PMS_GROUP` | Procured market service (ancillary) group definitions | Static |
| `PMS_GROUPSERVICE` | Services within each PMS group | Static |
| `Reserve_Contract_Recovery` (dir) | Reserve contract recovery data | Monthly |

---

## 14. 🔍 FREQUENCY PERFORMANCE PAYMENTS (FPP)

> **Availability:** 🟢 **Live** — 5-min / 30-min via `Reports/CURRENT/FPP/`, `FPPDAILY/`, `FPPRATES/`

New tables introduced for the FPP framework (from 2023+), published via `FPP/`, `FPPDAILY/`, `FPPRATES/`, `FPPRUN/`, `FPP_HIST_REG_PERF/`.

| Table | Description | Frequency |
|-------|-------------|-----------|
| `FPP_RUN` | FPP calculation run metadata | 5-min / 30-min |
| `FPP_PERFORMANCE` | FPP performance score per unit per interval | 5-min |
| `FPP_HIST_PERFORMANCE` | Historical FPP performance data | Per run |
| `FPP_HIST_REGION_PERFORMANCE` | Historical FPP performance aggregated by region | Per run |
| `FPP_RESIDUAL_PERFORMANCE` | Residual performance scores for FPP | Per run |
| `FPP_CONTRIBUTION_FACTOR` | Contribution factors for FPP calculation per unit | Per run |
| `FPP_RESIDUAL_CF` | Residual contribution factors | Per run |
| `FPP_FCAS_SUMMARY` | Summary of FCAS requirements used in FPP | Per run |
| `FPP_CONSTRAINT_FREQ_MEASURE` | Frequency measurement at constraint level for FPP | Per run |
| `FPP_REGION_FREQ_MEASURE` | Regional frequency measurement for FPP | Per run |
| `FPP_EST_PERF_COST_RATE` | Estimated performance cost rate for FPP | Per run |
| `FPP_EST_RESIDUAL_COST_RATE` | Estimated residual cost rate for FPP | Per run |
| `FPP_FORECAST_DEFAULT_CF` | Default contribution factors used in FPP forecast | Per run |
| `FPP_FORECAST_RESIDUAL_DCF` | Residual default contribution factors for FPP forecast | Per run |
| `FPP_P5_FWD_EST_RESIDUALRATE` | P5MIN forward estimated residual rate for FPP | 5-min |
| `FPP_PD_FWD_EST_RESIDUALRATE` | Pre-dispatch forward estimated residual rate for FPP | 30-min |
| `FPP_RCR` | FPP Regional Cost Rate | Per run |
| `FPP_USAGE` | FPP usage data | Per run |

---

## 15. 🔗 CONSTRAINTS

> **Availability:** 🟢 **Live** — binding-constraint solutions arrive in the 5-min dispatch reports; definitions (`GENCON*`) update as invoked

| Table | Description | Frequency |
|-------|-------------|-----------|
| `GENCONDATA` | Generic constraint definitions: LHS coefficients, type, limit type, description | Updated |
| `GENCONSET` | Constraint sets: collections of constraints invoked together | Updated |
| `GENCONSETINVOKE` | When each constraint set was invoked/revoked | Updated |
| `GENCONSETTRK` | Version tracking for constraint set definitions | Updated |
| `GENERICCONSTRAINTRHS` | Right-hand side (RHS) limit for generic constraints | Updated |
| `GENERICEQUATIONDESC` | Generic equation descriptions (reusable constraint building blocks) | Updated |
| `GENERICEQUATIONRHS` | RHS for generic equation terms | Updated |
| `SPDCONNECTIONPOINTCONSTRAINT` | SPD (Scheduling, Pricing, Dispatch) connection point LHS terms | Updated |
| `SPDINTERCONNECTORCONSTRAINT` | SPD interconnector LHS terms for constraints | Updated |
| `SPDREGIONCONSTRAINT` | SPD region LHS terms for constraints | Updated |
| `CONSTRAINTRELAXATION_OCD` | Over-constrained dispatch (OCD) constraint relaxation data | 5-min |
| `Weekly_Constraint_Reports` (dir) | Weekly report on constraint binding frequency | Weekly |

---

## 16. 🔌 INTERCONNECTORS

> **Availability:** 🟢 **Live** — flows every 5 min in dispatch reports; `SET*` residue tables are ⚪ settlement-lagged

| Table | Description | Frequency |
|-------|-------------|-----------|
| `INTERCONNECTOR` | Reference: interconnector definitions (e.g., VIC1-NSW1, NSW1-QLD1) | Static |
| `INTERCONNECTORCONSTRAINT` | Interconnector limit constraints: max forward/reverse capacity, loss model | Updated |
| `METERDATA_INTERCONNECTOR` | Metered (settlement) energy flows for interconnectors | 30-min |
| `MNSP_INTERCONNECTOR` | MNSP interconnector definitions and parameters | Updated |
| `MNSP_PARTICIPANT` | MNSP participant details | Updated |
| `NEGATIVE_RESIDUE` | Negative residue events for interconnectors | 5-min |
| `SETIRSURPLUS` | Interconnector Residue Surplus (IRS) settlement — energy flows × loss factor | Settlement |
| `SETINTRAREGIONRESIDUES` | Intra-region residue settlements | Settlement |
| `LOSSFACTORMODEL` | Loss factor model coefficients | Updated |
| `LOSSMODEL` | Loss model definitions | Updated |
| `Dispatch_IRSR` (dir) | Interconnector Residue Settlement Report | 5-min |
| `Trading_IRSR` (dir) | Trading interval IRS report | 30-min |
| `Predispatch_IRSR` (dir) | Pre-dispatch IRS | 30-min |

---

## 17. 🏭 GENERATION UNITS & REGISTRATION

> **Availability:** 🟡 **Recent** — NEM Registration & Exemption List (Excel) weekly; MMS reference tables via monthly archive

| Table | Description | Frequency |
|-------|-------------|-----------|
| `DUDETAIL` | Dispatachable unit detail: registered capacity, fuel type, dispatch type, connection point | Updated |
| `DUDETAILSUMMARY` | Summary version of DUDETAIL (most recent version per DUID) | Updated |
| `DUALLOC` | Allocation of DUIDs to stations | Updated |
| `DISPATCHABLEUNIT` | Master list of all DUIDs | Updated |
| `GENUNITS` | Generating unit details: MLF, station, fuel type, technology | Updated |
| `GENUNITS_UNIT` | Sub-unit details for generating units | Updated |
| `STATION` | Station (power plant) details | Updated |
| `STATIONOWNER` | Station ownership by participant | Updated |
| `STATIONOWNERTRK` | Version tracking for station ownership | Updated |
| `STADUALLOC` | Station–DUID allocation | Updated |
| `STATIONOPERATINGSTATUS` | Current operating status of each station | Updated |
| `EMSMASTER` | EMS (Energy Management System) master reference data | Updated |
| `Generators and Scheduled Loads` ✅ *(in your DB as `nem_duid_mapping`)* | NEM Registration & Exemption List — full Excel register of all registered generators/loads | Weekly |
| `TRANSMISSIONLOSSFACTOR` | Transmission loss factors (TLFs/MLFs) per connection point | Annual |
| `Marginal_Loss_Factors` (dir) | Published MLF tables | Annual |
| `ADG_DETAIL` | Aggregate Dispatch Group detail (DUIDs within each ADG) | Updated |
| `AGGREGATE_DISPATCH_GROUP` | Aggregate Dispatch Group definitions | Updated |

---

## 18. 👥 PARTICIPANTS

> **Availability:** ⚪ **Reference** — monthly MMSDM archive

| Table | Description | Frequency |
|-------|-------------|-----------|
| `PARTICIPANT` | Registered participant details (name, type, classification) | Updated |
| `PARTICIPANTCATEGORY` | Participant categories | Static |
| `PARTICIPANTCATEGORYALLOC` | Allocation of participants to categories | Updated |
| `PARTICIPANTCLASS` | Participant class definitions | Static |

---

## 19. 📉 DEMAND & OPERATIONAL DATA

> **Availability:** 🟢 **Live** — every 30 min via `Reports/CURRENT/Operational_Demand/ACTUAL_HH/`

| Table | Description | Frequency |
|-------|-------------|-----------|
| `DEMANDOPERATIONALACTUAL` | Actual operational demand by region (MW) | 30-min |
| `DEMANDOPERATIONALFORECAST` | Operational demand forecast by region | 30-min |
| `PERDEMAND` | Per-period demand data used in dispatch | 30-min |
| `RESDEMANDTRK` | Reserve demand tracking | Per run |
| `Operational_Demand` (dir) | Published operational demand report | 30-min |
| `Operational_Demand_Less_SNSG` (dir) | Operational demand less semi-scheduled non-scheduled generation | 30-min |
| `HistDemand` (dir) | Historical actual demand by region | 30-min (historical) |
| `SupplyDemand` (dir) | Supply–demand tables | Monthly |
| `Regional_Summary_Report` (dir) | Regional supply/demand summary | Daily |
| `DISPATCHFCST` (dir) | Dispatch demand forecast | 5-min |
| `PREDISPATCHFCST` (dir) | Pre-dispatch demand forecast | 30-min |

---

## 20. 🧾 SETTLEMENTS

> **Availability:** ⚪ **Archive** — settlement runs (preliminary ~1 week, final ~4 months); monthly MMSDM

| Table | Description | Frequency |
|-------|-------------|-----------|
| `SET_ENERGY_REGION_SUMMARY` | Settlement energy summary by region | Settlement run |
| `SET_ANCILLARY_SUMMARY` | Settlement ancillary services summary | Settlement run |
| `SETFCASREGIONRECOVERY` | FCAS regional recovery amounts | Settlement run |
| `SET_FCAS_REGULATION_TRK` | Regulation FCAS settlement tracking | Settlement run |
| `SET_FCAS_CLAWBACK_REQ` | FCAS clawback settlement requirements | Settlement run |
| `SET_FCAS_CLAWBACK_RUN_TRK` | FCAS clawback run tracking | Settlement run |
| `SET_NMAS_RECOVERY_RBF` | Non-Market Ancillary Service recovery (residual balancing factor) | Settlement run |
| `ANCILLARY_RECOVERY_SPLIT` | FCAS recovery cost split between generator/load | Settlement run |
| `SETCFG_PARTICIPANT_MPF` | Participant marginal participation factor for settlement | Updated |
| `SETCFG_PARTICIPANT_MPFTRK` | Tracking for participant MPF versions | Updated |
| `SETCFG_SAPS_SETT_PRICE` | SAPS (Stand-Alone Power System) settlement price configuration | Updated |
| `SETCFG_WDR_REIMBURSE_RATE` | WDR (Wholesale Demand Response) reimbursement rate configuration | Updated |
| `SETCFG_WDRRR_CALENDAR` | WDR reimbursement rate calendar | Updated |
| `SETLOCALAREAENERGY` | Local area energy settlement amounts | Settlement run |
| `SETLOCALAREATNI` | Local area TNI (Transmission Node Identifier) data | Settlement run |
| `SETIRSURPLUS` | Interconnector Residue Surplus settlement values | Settlement run |
| `SETINTRAREGIONRESIDUES` | Intra-region residue settlement | Settlement run |
| `IRFMAMOUNT` | Intra-Regional Firm Market (IRFM) settlement amounts | Settlement run |
| `IRFMEVENTS` | IRFM event definitions | Per event |
| `PRUDENTIALRUNTRK` | Prudential (credit/exposure) run tracking | Weekly |
| `SECDEPOSIT_INTEREST_RATE` | Security deposit interest rate for prudential | Monthly |
| `Settlements` (dir) | Published settlement statements | Settlement run |
| `CSC_CSP_ConstraintList` (dir) | Constraint Support Contract constraint list | Per contract |
| `CSC_CSP_Settlements` (dir) | CSC/CSP settlement data | Settlement run |
| `Directions_Reconciliation` (dir) | Directions reconciliation settlement | Per event |

---

## 21. 💵 BILLING

> **Availability:** ⚪ **Archive** — weekly billing runs; monthly MMSDM

| Table | Description | Frequency |
|-------|-------------|-----------|
| `BILLINGCALENDAR` | Billing period calendar (settlement dates) | Quarterly |
| `BILLINGDAYTRK` | Billing day tracking | Daily |
| `BILLINGRUNTRK` | Billing run tracking (preliminary, final, revision runs) | Per run |
| `BILLINGREGIONFIGURES` | Billing figures by region | Per billing run |
| `BILLINGREGIONEXPORTS` | Billing region export energy | Per billing run |
| `BILLINGREGIONIMPORTS` | Billing region import energy | Per billing run |
| `BILLING_CO2E_PUBLICATION` | CO2-equivalent emissions intensity data for billing | Per billing run |
| `BILLING_CO2E_PUBLICATION_TRK` | Tracking for CO2-e billing publications | Per billing run |
| `BILLING_DIRECTION_RECON_OTHER` | Billing reconciliation for directions/other amounts | Per billing run |
| `BILLING_NMAS_TST_RECVRY_RBF` | NMAS testing recovery residual balancing factor for billing | Per billing run |
| `BILLING_NMAS_TST_RECVRY_TRK` | Tracking for NMAS testing recovery | Per billing run |
| `DAYTRACK` | Day tracking for billing purposes | Daily |
| `MARKETFEE` | Market fee definitions | Updated |
| `MARKETFEEDATA` | Market fee rate data | Updated |
| `MARKETFEETRK` | Market fee version tracking | Updated |
| `GST_BAS_CLASS` | GST Business Activity Statement classification | Static |
| `GST_RATE` | GST rates | Static |
| `GST_TRANSACTION_CLASS` | GST transaction classifications | Static |
| `GST_TRANSACTION_TYPE` | GST transaction types | Static |
| `Billing` (dir) | Published billing statements | Per billing run |

---

## 22. 🏛️ SETTLEMENT RESIDUE AUCTIONS (SRA / IRA)

> **Availability:** ⚪ **Archive** — quarterly auctions / periodic

| Table | Description | Frequency |
|-------|-------------|-----------|
| `AUCTION` | SRA auction event details | Quarterly |
| `AUCTION_CALENDAR` | SRA auction calendar | Quarterly |
| `AUCTION_IC_ALLOCATIONS` | Interconnector allocations for SRA | Quarterly |
| `AUCTION_TRANCHE` | Auction tranche definitions | Quarterly |
| `RESIDUE_CONTRACTS` | Settlement residue contracts issued | Quarterly |
| `RESIDUE_PUBLIC_DATA` | Public residue auction result data | Quarterly |
| `RESIDUE_PRICE_FUNDS_BID` | Price/funds bids in SRA | Quarterly |
| `RESIDUE_TRK` | SRA tracking data | Quarterly |
| `SRA_FINANCIAL_RUNTRK` | SRA financial settlement run tracking | Per run |
| `SRA_PRUDENTIAL_RUN` | SRA prudential run details | Per run |
| `SRA_Bids` (dir) | SRA bid submissions | Per auction |
| `SRA_Offers` (dir) | SRA offer submissions | Per auction |
| `SRA_Results` (dir) | SRA auction results | Per auction |
| `SRA_NSR_RECONCILIATION` (dir) | SRA non-scheduled residue reconciliation | Per run |
| `Auction_Units_Reports` (dir) | Auction unit reports | Quarterly |

---

## 23. 🌐 NETWORK / OUTAGES

> **Availability:** 🟢 **Live** — outage schedules updated continuously via `Reports/CURRENT/Network/`

| Table | Description | Frequency |
|-------|-------------|-----------|
| `NETWORK_EQUIPMENTDETAIL` | Network equipment (transmission lines, transformers) details | Updated |
| `NETWORK_OUTAGEDETAIL` | Planned/unplanned outage details (start time, equipment, constraint impact) | As notified |
| `NETWORK_OUTAGECONSTRAINTSET` | Constraints associated with network outages | As notified |
| `NETWORK_OUTAGESTATUSCODE` | Reference: outage status codes | Static |
| `NETWORK_RATING` | Dynamic network equipment ratings | Updated |
| `NETWORK_STATICRATING` | Static/seasonal network ratings | Updated |
| `NETWORK_SUBSTATIONDETAIL` | Substation details | Updated |
| `HighImpactOutages` (dir) | High-impact outage notifications | As notified |
| `Network` (dir) | Published network data (alt limits, etc.) | Updated |
| `Alt_Limits` (dir) | Alternate limit definitions for constraints | Updated |
| `PublishedModelDataAccess` (dir) | Published network model data | Updated |

---

## 24. 📋 MARKET NOTICES & EVENTS

> **Availability:** 🟢 **Live** — market notices published continuously via `Reports/CURRENT/Market_Notice/`

| Table | Description | Frequency |
|-------|-------------|-----------|
| `MARKETNOTICETYPE` | Market notice type classifications | Static |
| `MARKETSUSPENSION` | Market suspension events | Per event |
| `MARKETSUSREGION` | Regions affected by market suspensions | Per event |
| `APEVENT` | Administered Price Event details (when market prices exceed thresholds) | Per event |
| `APEVENTREGION` | Regions affected by administered price events | Per event |
| `OVERRIDERRP` | Administered/override prices applied during market suspension | Per event |
| `MARKET_PRICE_THRESHOLDS` | Defined market price thresholds (CPT, MPC, etc.) | Updated |
| `MARKET_SUSPEND_REGIME_SUM` | Market suspension regime summary | Per suspension |
| `MARKET_SUSPEND_REGION_SUM` | Market suspension regional summary | Per suspension |
| `MARKET_SUSPEND_SCHEDULE` | Administered market suspension pricing schedule | Per suspension |
| `MARKET_SUSPEND_SCHEDULE_TRK` | Tracking for market suspension schedules | Per suspension |
| `Market_Notice` (dir) | Published market notices | As issued |
| `Mktsusp_Pricing` (dir) | Market suspension pricing data | Per suspension |
| `DISPATCHIS_PRICE_REVISIONS` (dir) | Dispatch price revision records | Per revision |
| `Adjusted_Prices_Reports` (dir) | Adjusted/revised historical prices (post-review) | Per revision |
| `Dispatchprices_PRE_AP` (dir) | Dispatch prices prior to administered price application | 5-min |

---

## 25. 📰 CAUSER PAYS (FCAS 4-Second Data)

> **Availability:** 🟡 **Recent** — 4-second causer-pays files published in daily batches

Published via `Causer_Pays/`, `Causer_Pays_Elements/`, `Causer_Pays_Scada/`, `Causer_Pays_Rslcpf/`.

| Dataset | Description | Frequency |
|---------|-------------|-----------|
| `CAUSER_PAYS` (via NEMOSIS: `ELEMENTS_FCAS_4_SECOND`, `VARIABLES_FCAS_4_SECOND`) | 4-second frequency deviation measurements used to calculate causer pays FCAS cost allocation | 4-second |
| `Causer_Pays_Elements` (dir) | Element-level 4-second frequency measurements | 4-second → monthly |
| `Causer_Pays_Scada` (dir) | SCADA data used in causer pays calculations | 4-second → monthly |
| `Causer_Pays_Rslcpf` (dir) | Residual system load causer pays factor (RSLCPF) results | Monthly |
| `Causer_Pays` (dir) | Main causer pays results | Monthly |

---

## 26. 📊 PUBLIC PRICES & DEMAND FORECASTS

> **Availability:** 🟢 **Live** — `Public_Prices/` daily files; demand forecasts every 30 min

| Report / Table | Description | Frequency |
|----------------|-------------|-----------|
| `Public_Prices` (dir) | Daily summary of all regional prices | Daily |
| `AVERAGEPRICE30` | 30-min volume-weighted average prices by region | 30-min |
| `Vwa_Fcas_Prices` (dir) | Volume-weighted average FCAS prices by region and service | Daily |
| `DISPATCHFCST` (dir) | Dispatch demand forecast | 5-min |
| `PREDISPATCHFCST` (dir) | Pre-dispatch demand forecast | 30-min |
| `ECGS` (dir) | Energy Constrained Generation Schedule data | ~30-min |
| `NEXT_DAY_MCCDISPATCH` (dir) | Next-day MCC dispatch results | Daily |
| `MCCDispatch` (dir) | Real-time MCC dispatch results | 5-min |
| `Daily_Reports` (dir) | Comprehensive daily report ZIP (contains all dispatch/trading/settlement data for a day) | Daily |
| `DAILYOCD` (dir) | Daily over-constrained dispatch report | Daily |
| `Next_Day_Dispatch` (dir) | Next-day published dispatch data | Daily |
| `Next_Day_Actual_Gen` (dir) | Next-day actual generation by DUID | Daily |
| `Next_Day_PreDispatch` (dir) | Next-day pre-dispatch results | Daily |
| `Next_Day_PreDispatchD` (dir) | Next-day pre-dispatch D (deterministic) | Daily |
| `Next_Day_Trading` (dir) | Next-day trading interval data | Daily |

---

## 27. 🌞 DEMAND RESPONSE & WDR

> **Availability:** 🟡 **Recent** — daily / next-day publications

| Table / Report | Description | Frequency |
|----------------|-------------|-----------|
| `SETCFG_WDR_REIMBURSE_RATE` | WDR reimbursement rate configuration | Updated |
| `SETCFG_WDRRR_CALENDAR` | WDR reimbursement rate calendar | Updated |
| `WDR_CAPACITY_NO_SCADA` (dir) | WDR (Wholesale Demand Response) capacity for units without SCADA | 5-min |

---

## 28. 🔧 MARKET CONFIGURATION & REFERENCE

> **Availability:** ⚪ **Reference** — updated as changed; monthly MMSDM archive

| Table | Description | Frequency |
|-------|-------------|-----------|
| `REGION` | NEM regions reference (NSW1, VIC1, SA1, QLD1, TAS1) | Static |
| `REGIONSTANDINGDATA` | Standing data for each region (loss factors, reference nodes) | Updated |
| `REGIONAPC` | Administered Price Cap settings by region | Per event |
| `REGIONAPCINTERVALS` | APC application intervals per region | Per event |
| `Trading_Cumulative_Price` (dir) | Cumulative price (for Market Price Cap tracking) | 5-min |
| `CDEII` (dir) | Cumulative Dispatch Error/Interval Index data | Per period |
| `IBEI` (dir) | Intra-Regional Balancing Energy Index | Per period |

---

## 29. 🧩 AGGREGATE DISPATCH GROUPS (ADG)

> **Availability:** ⚪ **Reference** — updated as changed

| Table | Description | Frequency |
|-------|-------------|-----------|
| `AGGREGATE_DISPATCH_GROUP` | ADG definitions (groups of DUIDs dispatched as one) | Updated |
| `ADG_DETAIL` | DUID membership within each ADG | Updated |

---

## 30. 📜 MARKET NOTICES (Reference)

> **Availability:** 🟢 **Live** — continuous

| Table | Description | Frequency |
|-------|-------------|-----------|
| `Market_Notice` (dir) | Published AEMO market notices (text announcements) | As issued |
| `MARKETNOTICETYPE` | Types of market notices | Static |
| `Weekly_Bulletin` (dir) | AEMO weekly market bulletin | Weekly |

---

## 31. 📋 COMPLETE MMSDM TABLE MASTER LIST

> **Availability:** Mixed — every table below is in the ⚪ monthly MMSDM archive; those also covered by sections 1–30 marked 🟢/🟡 can be pulled live

The following is the full verified list of distinct tables present in the **MMSDM 2026-06 Historical Data Archive** (from CTL file manifest):

<details>
<summary><strong>Click to expand — 235 MMSDM Table Names (alphabetical)</strong></summary>

```
ADG_DETAIL
AGGREGATE_DISPATCH_GROUP
ANCILLARY_RECOVERY_SPLIT
APEVENT
APEVENTREGION
AUCTION
AUCTION_CALENDAR
AUCTION_IC_ALLOCATIONS
AUCTION_TRANCHE
AVERAGEPRICE30
BIDDAYOFFER
BIDDAYOFFER_D
BIDDUIDDETAILS
BIDDUIDDETAILSTRK
BIDOFFERPERIOD
BIDPEROFFER_D
BIDTYPES
BIDTYPESTRK
BILLING_CO2E_PUBLICATION
BILLING_CO2E_PUBLICATION_TRK
BILLING_DIRECTION_RECON_OTHER
BILLING_NMAS_TST_RECVRY_RBF
BILLING_NMAS_TST_RECVRY_TRK
BILLINGCALENDAR
BILLINGDAYTRK
BILLINGREGIONEXPORTS
BILLINGREGIONFIGURES
BILLINGREGIONIMPORTS
BILLINGRUNTRK
CONSTRAINTRELAXATION_OCD
DAYTRACK
DEMANDOPERATIONALACTUAL
DEMANDOPERATIONALFORECAST
DISPATCH_FCAS_REQ_CONSTRAINT
DISPATCH_FCAS_REQ_RUN
DISPATCH_INTERCONNECTION
DISPATCH_LOCAL_PRICE
DISPATCH_MNSPBIDTRK
DISPATCH_UNIT_SCADA
DISPATCHABLEUNIT
DISPATCHCASESOLUTION
DISPATCHCONSTRAINT
DISPATCHINTERCONNECTORRES
DISPATCHLOAD
DISPATCHOFFERTRK
DISPATCHPRICE
DISPATCHREGIONSUM
DUALLOC
DUDETAIL
DUDETAILSUMMARY
EMSMASTER
FCAS_REGU_USAGE_FACTORS
FCAS_REGU_USAGE_FACTORS_TRK
FPP_CONSTRAINT_FREQ_MEASURE
FPP_CONTRIBUTION_FACTOR
FPP_EST_PERF_COST_RATE
FPP_EST_RESIDUAL_COST_RATE
FPP_FCAS_SUMMARY
FPP_FORECAST_DEFAULT_CF
FPP_FORECAST_RESIDUAL_DCF
FPP_HIST_PERFORMANCE
FPP_HIST_REGION_PERFORMANCE
FPP_P5_FWD_EST_RESIDUALRATE
FPP_PD_FWD_EST_RESIDUALRATE
FPP_PERFORMANCE
FPP_RCR
FPP_REGION_FREQ_MEASURE
FPP_RESIDUAL_CF
FPP_RESIDUAL_PERFORMANCE
FPP_RUN
FPP_USAGE
GDINSTRUCT
GENCONDATA
GENCONSET
GENCONSETINVOKE
GENCONSETTRK
GENERICCONSTRAINTRHS
GENERICEQUATIONDESC
GENERICEQUATIONRHS
GENUNITS
GENUNITS_UNIT
GST_BAS_CLASS
GST_RATE
GST_TRANSACTION_CLASS
GST_TRANSACTION_TYPE
INSTRUCTIONSUBTYPE
INSTRUCTIONTYPE
INTERCONNECTOR
INTERCONNECTORCONSTRAINT
INTERMITTENT_CLUSTER_AVAIL
INTERMITTENT_CLUSTER_AVAIL_DAY
INTERMITTENT_DS_PRED
INTERMITTENT_DS_RUN
INTERMITTENT_FORECAST_TRK
INTERMITTENT_GEN_LIMIT
INTERMITTENT_GEN_LIMIT_DAY
INTERMITTENT_GEN_SCADA
IRFMAMOUNT
IRFMEVENTS
LOSSFACTORMODEL
LOSSMODEL
MARKET_PRICE_THRESHOLDS
MARKET_SUSPEND_REGIME_SUM
MARKET_SUSPEND_REGION_SUM
MARKET_SUSPEND_SCHEDULE
MARKET_SUSPEND_SCHEDULE_TRK
MARKETFEE
MARKETFEEDATA
MARKETFEETRK
MARKETNOTICETYPE
MARKETSUSPENSION
MARKETSUSREGION
MCC_CASESOLUTION
MCC_CONSTRAINTSOLUTION
METERDATA_INTERCONNECTOR
MNSP_BIDOFFERPERIOD
MNSP_DAYOFFER
MNSP_INTERCONNECTOR
MNSP_PARTICIPANT
MTPASA_CASERESULT
MTPASA_CONSTRAINTRESULT
MTPASA_CONSTRAINTSUMMARY
MTPASA_DUIDAVAILABILITY
MTPASA_INTERCONNECTORRESULT
MTPASA_LOLPRESULT
MTPASA_REGIONAVAIL_TRK
MTPASA_REGIONAVAILABILITY
MTPASA_REGIONITERATION
MTPASA_REGIONRESULT
MTPASA_REGIONSUMMARY
MTPASA_RESERVELIMIT
MTPASA_RESERVELIMIT_REGION
MTPASA_RESERVELIMIT_SET
NEGATIVE_RESIDUE
NETWORK_EQUIPMENTDETAIL
NETWORK_OUTAGECONSTRAINTSET
NETWORK_OUTAGEDETAIL
NETWORK_OUTAGESTATUSCODE
NETWORK_RATING
NETWORK_STATICRATING
NETWORK_SUBSTATIONDETAIL
OVERRIDERRP
P5MIN_CASESOLUTION
P5MIN_CONSTRAINTSOLUTION
P5MIN_FCAS_REQ_CONSTRAINT
P5MIN_FCAS_REQ_RUN
P5MIN_INTERCONNECTORSOLN
P5MIN_INTERSENSITIVITIES
P5MIN_LOCAL_PRICE
P5MIN_PRICESENSITIVITIES
P5MIN_REGIONSOLUTION
P5MIN_SCENARIODEMAND
P5MIN_SCENARIODEMANDTRK
PARTICIPANT
PARTICIPANTCATEGORY
PARTICIPANTCATEGORYALLOC
PARTICIPANTCLASS
PD_FCAS_REQ_CONSTRAINT
PD_FCAS_REQ_RUN
PD7DAY_CASESOLUTION
PD7DAY_CONSTRAINTSOLUTION
PD7DAY_INTERCONNECTORSOLUTION
PD7DAY_MARKET_SUMMARY
PD7DAY_PRICESOLUTION
PDPASA_CASESOLUTION
PDPASA_CONSTRAINTSOLUTION
PDPASA_DUIDAVAILABILITY
PDPASA_INTERCONNECTORSOLN
PDPASA_REGIONSOLUTION
PERDEMAND
PMS_GROUP
PMS_GROUPSERVICE
PREDISPATCH_LOCAL_PRICE
PREDISPATCH_MNSPBIDTRK
PREDISPATCHCASESOLUTION
PREDISPATCHCONSTRAINT
PREDISPATCHINTERCONNECTORRES
PREDISPATCHLOAD
PREDISPATCHOFFERTRK
PREDISPATCHPRICE
PREDISPATCHPRICESENSITIVITIES
PREDISPATCHREGIONSUM
PREDISPATCHSCENARIODEMAND
PREDISPATCHSCENARIODEMANDTRK
PRUDENTIALRUNTRK
REGION
REGIONAPC
REGIONAPCINTERVALS
REGIONSTANDINGDATA
RESDEMANDTRK
RESIDUE_CONTRACTS
RESIDUE_PRICE_FUNDS_BID
RESIDUE_PUBLIC_DATA
RESIDUE_TRK
ROOFTOP_PV_ACTUAL
ROOFTOP_PV_FORECAST
SECDEPOSIT_INTEREST_RATE
SET_ANCILLARY_SUMMARY
SET_ENERGY_REGION_SUMMARY
SET_FCAS_CLAWBACK_REQ
SET_FCAS_CLAWBACK_RUN_TRK
SET_FCAS_REGULATION_TRK
SET_NMAS_RECOVERY_RBF
SETCFG_PARTICIPANT_MPF
SETCFG_PARTICIPANT_MPFTRK
SETCFG_SAPS_SETT_PRICE
SETCFG_WDR_REIMBURSE_RATE
SETCFG_WDRRR_CALENDAR
SETFCASREGIONRECOVERY
SETINTRAREGIONRESIDUES
SETIRSURPLUS
SETLOCALAREAENERGY
SETLOCALAREATNI
SPDCONNECTIONPOINTCONSTRAINT
SPDINTERCONNECTORCONSTRAINT
SPDREGIONCONSTRAINT
SRA_FINANCIAL_RUNTRK
SRA_PRUDENTIAL_RUN
SSM_ENABLEMENT_COSTS
SSM_ENABLEMENT_PERIOD
STADUALLOC
STATION
STATIONOPERATINGSTATUS
STATIONOWNER
STATIONOWNERTRK
STPASA_CASESOLUTION
STPASA_CONSTRAINTSOLUTION
STPASA_DUIDAVAILABILITY
STPASA_INTERCONNECTORSOLN
STPASA_REGIONSOLUTION
TRADINGINTERCONNECT
TRADINGPRICE
TRANSMISSIONLOSSFACTOR
VOLTAGE_INSTRUCTION
VOLTAGE_INSTRUCTION_TRK
```

</details>

---

## 32. 📁 NEMWeb `/Reports/CURRENT/` — All Report Directories

> **Availability:** 🟢 **Live** — by definition: everything under `Reports/CURRENT/` is real-time or near-real-time

The following directories are verified active as of 2026-07-30:

| Directory | Category | Frequency |
|-----------|----------|-----------|
| `Adjusted_Prices_Reports` | Prices / Market Events | Per revision |
| `Alt_Limits` | Network / Constraints | Updated |
| `Ancillary_Services_Payments` | FCAS / Billing | Monthly |
| `ANCILLARY_SERVICES_REPORTS` | FCAS Registration | Weekly |
| `Auction_Units_Reports` | SRA | Quarterly |
| `Bidmove_Complete` | Bidding | As submitted |
| `Bidmove_Summary` | Bidding | As submitted |
| `Billing` | Billing | Per billing run |
| `Causer_Pays` | FCAS / Causer Pays | Monthly |
| `Causer_Pays_Elements` | FCAS / Causer Pays 4-sec | Monthly |
| `Causer_Pays_Rslcpf` | FCAS / Causer Pays | Monthly |
| `Causer_Pays_Scada` | FCAS / Causer Pays 4-sec | Monthly |
| `CDEII` | Market Operations | Per period |
| `CSC_CSP_ConstraintList` | Settlements / Constraints | Per contract |
| `CSC_CSP_Settlements` | Settlements | Settlement run |
| `Daily_Reports` | Dispatch / Trading (combined) | Daily |
| `DAILYOCD` | Dispatch / OCD | Daily |
| `Directions_Reconciliation` | Settlements | Per event |
| `Dispatch_IRSR` | Interconnectors / Settlement | 5-min |
| `DISPATCH_NEGATIVE_RESIDUE` | Interconnectors | 5-min |
| `Dispatch_Reports` | Dispatch | 5-min |
| `Dispatch_SCADA` | Generation / SCADA | 5-min |
| `DISPATCHFCST` | Demand Forecasts | 5-min |
| `DISPATCHIS_PRICE_REVISIONS` | Prices / Revisions | Per revision |
| `DispatchIS_Reports` | Dispatch (full MMS) | 5-min |
| `Dispatchprices_PRE_AP` | Prices | 5-min |
| `ECGS` | Generation Constraints | ~30-min |
| `FPP_HIST_REG_PERF` | FCAS / FPP | Per run |
| `FPP` | FCAS / FPP | 5-min |
| `FPPDAILY` | FCAS / FPP | Daily |
| `FPPRATES` | FCAS / FPP | Per run |
| `FPPRUN` | FCAS / FPP | Per run |
| `Gas_Supply_Guarantee` | Gas | Per event |
| `GBB` | Gas Bulletin Board | Varies |
| `GSH` | Gas Supply Hub | Varies |
| `HighImpactOutages` | Network / Outages | As notified |
| `HistDemand` | Demand (Historical) | 30-min |
| `IBEI` | Market Operations | Per period |
| `Marginal_Loss_Factors` | Loss Factors | Annual |
| `Market_Notice` | Market Notices | As issued |
| `MCCDispatch` | Constraints / Dispatch | 5-min |
| `Medium_Term_PASA_Reports` | MTPASA | Weekly |
| `Mktsusp_Pricing` | Market Suspension | Per suspension |
| `MMSDataModelReport` | Documentation | Updated |
| `MTPASA_DUIDAvailability` | MTPASA | Weekly |
| `MTPASA_RegionAvailability` | MTPASA | Weekly |
| `Network` | Network | Updated |
| `Next_Day_Actual_Gen` | Generation / Actuals | Daily |
| `NEXT_DAY_AVAIL_SUBMISS_CLUSTER` | Bidding / Availability | Daily |
| `NEXT_DAY_AVAIL_SUBMISS_DAY` | Bidding / Availability | Daily |
| `Next_Day_Dispatch` | Dispatch | Daily |
| `Next_Day_Intermittent_DS` | Intermittent Gen | Daily |
| `Next_Day_Intermittent_Gen_Scada` | Intermittent Gen / SCADA | Daily |
| `NEXT_DAY_MCCDISPATCH` | Constraints / Dispatch | Daily |
| `Next_Day_Offer_Energy` | Bidding (Energy) | Daily |
| `Next_Day_Offer_Energy_SPARSE` | Bidding (Energy, sparse) | Daily |
| `Next_Day_Offer_FCAS` | Bidding (FCAS) | Daily |
| `Next_Day_Offer_FCAS_SPARSE` | Bidding (FCAS, sparse) | Daily |
| `Next_Day_PreDispatch` | Pre-Dispatch | Daily |
| `Next_Day_PreDispatchD` | Pre-Dispatch | Daily |
| `Next_Day_Trading` | Trading | Daily |
| `Operational_Demand` | Demand | 30-min |
| `Operational_Demand_Less_SNSG` | Demand | 30-min |
| `P5_Reports` | P5MIN Pre-Dispatch | 5-min |
| `P5MINFCST` | P5MIN Forecast | 5-min |
| `PasaSnap` | PASA Snapshot | Per run |
| `PD7Day` | 7-Day Pre-Dispatch | 30-min |
| `PDPASA` | PDPASA | 30-min |
| `PDPASA_DUIDAvailability` | PDPASA | 30-min |
| `Predispatch_IRSR` | Interconnectors | 30-min |
| `Predispatch_Reports` | Pre-Dispatch | 30-min |
| `Predispatch_Sensitivities` | Pre-Dispatch | 30-min |
| `PREDISPATCHFCST` | Demand Forecasts | 30-min |
| `PredispatchIS_Reports` | Pre-Dispatch (full MMS) | 30-min |
| `Public_Prices` | Prices | Daily |
| `PublishedModelDataAccess` | Network Model | Updated |
| `Regional_Summary_Report` | Demand / Generation | Daily |
| `Reserve_Contract_Recovery` | FCAS / Ancillary | Monthly |
| `ROOFTOP_PV` | Solar / Demand | 30-min |
| `Settlements` | Settlements | Per settlement run |
| `SEVENDAYOUTLOOK_FULL` | PASA / Demand Outlook | Daily |
| `SEVENDAYOUTLOOK_PEAK` | PASA / Demand Outlook | Daily |
| `Short_Term_PASA_Reports` | STPASA | ~30-min |
| `SRA_Bids` | SRA | Quarterly |
| `SRA_NSR_RECONCILIATION` | SRA | Per run |
| `SRA_Offers` | SRA | Quarterly |
| `SRA_Results` | SRA | Quarterly |
| `SSM_ENABLEMENT_COSTS` | System Strength / FCAS | Per event |
| `SSM_ENABLEMENT_PERIOD` | System Strength / FCAS | Per event |
| `STPASA_DUIDAvailability` | STPASA | ~30-min |
| `STTM` | Gas (Short Term Trading Market) | Gas market |
| `SupplyDemand` | Demand | Monthly |
| `Trading_Cumulative_Price` | Prices / Market Cap | 5-min |
| `Trading_IRSR` | Interconnectors / Settlement | 30-min |
| `TradingIS_Reports` | Trading (full MMS) | 5-min |
| `DWGM` | Gas (Declared Wholesale Gas Market — VIC) | Gas market |
| `VicGas` | Gas (Victorian gas market data) | Gas market |
| `Vwa_Fcas_Prices` | FCAS Prices | Daily |
| `WDR_CAPACITY_NO_SCADA` | Demand Response | 5-min |
| `Weekly_Bulletin` | Market Notices | Weekly |
| `Weekly_Constraint_Reports` | Constraints | Weekly |
| `Yesterdays_Bids_Reports` | Bidding | Daily |
| `Yesterdays_MNSPBids_Reports` | Bidding | Daily |

---

## 33. 🐍 NEMOSIS Python Package — Supported Tables

> **Availability:** Tooling note — NEMOSIS can pull both 🟢 current reports and ⚪ historical archives on demand

The [NEMOSIS package](https://github.com/UNSW-CEEM/NEMOSIS) (`pip install nemosis`) wraps the following tables for programmatic access:

**Dynamic Tables** (filterable by datetime):
```python
['DISPATCHLOAD', 'DUDETAILSUMMARY', 'DUDETAIL', 'DISPATCHCONSTRAINT',
 'GENCONDATA', 'DISPATCH_UNIT_SCADA', 'DISPATCHPRICE', 'DISPATCHREGIONSUM',
 'DISPATCHINTERCONNECTORRES', 'TRADINGPRICE', 'TRADINGINTERCONNECT',
 'PREDISPATCHPRICE', 'PREDISPATCHREGIONSUM', 'PREDISPATCHCONSTRAINT',
 'PREDISPATCHINTERCONNECTORRES', 'PREDISPATCHLOAD',
 'BIDDAYOFFER_D', 'BIDPEROFFER_D',
 'ROOFTOP_PV_ACTUAL', 'ROOFTOP_PV_FORECAST',
 'DISPATCHCASESOLUTION', 'PREDISPATCHCASESOLUTION',
 'P5MIN_REGIONSOLUTION', 'P5MIN_INTERCONNECTORSOLN',
 'P5MIN_CONSTRAINTSOLUTION', 'P5MIN_CASESOLUTION',
 'INTERMITTENT_GEN_SCADA', 'FCAS_4_SECOND',
 ... and others]
```

**Static Tables**:
```python
['ELEMENTS_FCAS_4_SECOND', 'VARIABLES_FCAS_4_SECOND',
 'Generators and Scheduled Loads']
```

---

## Summary by Category Count

| Category | Approx. Table/Dataset Count |
|----------|-----------------------------|
| Dispatch (5-min MMS) | ~18 tables |
| P5MIN (5-min pre-dispatch) | ~11 tables |
| Pre-dispatch (30-min) | ~14 tables |
| 7-Day Pre-dispatch | ~5 tables |
| Trading (30-min) | ~4 tables |
| PDPASA | ~5 tables |
| STPASA | ~5 tables |
| MTPASA | ~15 tables |
| Bidding & Offers | ~12 tables |
| FCAS & Ancillary Services | ~15 tables |
| Frequency Performance Payments (FPP) | ~18 tables |
| Constraints | ~12 tables |
| Interconnectors | ~10 tables |
| Generation / Registration | ~15 tables |
| Demand & Operational | ~8 tables |
| Intermittent Gen & Rooftop Solar | ~10 tables |
| Settlements | ~18 tables |
| Billing | ~15 tables |
| Settlement Residue Auctions (SRA) | ~12 tables |
| Network & Outages | ~8 tables |
| Market Notices & Events | ~12 tables |
| Causer Pays (4-second) | ~5 datasets |
| Market Configuration | ~10 tables |
| **Total distinct MMSDM tables** | **~235** |
| **Total NEMWeb report directories** | **~90** |

---

## Key Data Access Notes

1. **MMSDM Monthly Archive**: Available at `nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/YYYY/MMSDM_YYYY_MM/` — contains CSV/BCP files for all ~235 tables, covering 2009–present.

2. **Real-time Reports**: Available at `nemweb.com.au/Reports/CURRENT/` — rolling window of recent files (typically last few days to weeks).

3. **Historical Archive**: Available at `nemweb.com.au/Reports/ARCHIVE/` — older real-time report files.

4. **MMS Data Model Report**: Full column-level documentation at `nemweb.com.au/Reports/CURRENT/MMSDataModelReport/Electricity/` — authoritative reference for all table schemas.

5. **FCAS 4-Second Data**: Only ~2 months of recent data available online via NEMOSIS; historical 2011–2016 also available. Stored separately from the MMSDM monthly archive.

6. **Bidding Data**: `BIDDAYOFFER` and `BIDOFFERPERIOD` tables are confidential on the day of dispatch but become public at 4am the following day as `BIDDAYOFFER_D` and `BIDPEROFFER_D`.

