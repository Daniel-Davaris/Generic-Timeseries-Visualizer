# Generic Timeseries Visualiser

A Flask web app for interactive timeseries visualisation. Upload any CSV with a date column and explore the data with configurable period grouping (Weekly / Monthly / Yearly), normalisation, and per-column selection — all rendered with Plotly.

## Quick start

```bash
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** in your browser, upload a CSV, and start exploring.

## Features

- **CSV upload** — drag-and-drop or click to upload
- **Auto date detection** — finds the first date-parseable column
- **Period grouping** — Weekly, Monthly, or Yearly sub-plots
- **Normalisation toggle** — compare differently-scaled series
- **Column groups** — organised by prefix with select-all / clear
- **Event columns** — optionally mark columns as vertical event lines