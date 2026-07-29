import os
import json

import pandas as pd
import plotly
import plotly.graph_objs as go
from flask import Flask, render_template, request, jsonify, session, Response
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

PLOTLY_COLORS = [
    "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
    "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52",
]


ALLOWED_EXTENSIONS = {".csv", ".parquet", ".parq", ".xlsx", ".xls"}


def _load_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(path)
    elif ext in (".parquet", ".parq"):
        df = pd.read_parquet(path)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    date_col = None

    # Pass 1: columns already parsed as datetime
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_col = col
            break

    # Pass 2: columns with date/time-related names
    if date_col is None:
        date_keywords = ["date", "time", "timestamp", "datetime", "period", "day", "month", "year"]
        for col in df.columns:
            col_lower = col.lower().replace("_", " ").replace("-", " ")
            if any(kw in col_lower for kw in date_keywords):
                try:
                    df[col] = pd.to_datetime(df[col], dayfirst=True, format="mixed")
                    date_col = col
                    break
                except Exception:
                    continue

    # Pass 3: try parsing any object/string column as dates
    if date_col is None:
        for col in df.columns:
            if df[col].dtype == object:
                sample = df[col].dropna().head(20)
                if len(sample) == 0:
                    continue
                try:
                    parsed = pd.to_datetime(sample, dayfirst=True, format="mixed")
                    if parsed.notna().sum() >= len(sample) * 0.8:
                        df[col] = pd.to_datetime(df[col], dayfirst=True, format="mixed")
                        date_col = col
                        break
                except Exception:
                    continue

    if date_col is None:
        raise ValueError("No date/time column found in file")
    df = df.sort_values(date_col)
    return df, date_col


def _prepare_series(df, date_col, event_cols):
    raw_series = {}
    for col in df.columns:
        if col == date_col:
            continue
        if col in event_cols:
            raw_series[col] = df[col]
        else:
            try:
                raw_series[col] = df[col].astype(float)
            except Exception:
                raw_series[col] = pd.Series(
                    pd.factorize(df[col])[0], index=df.index
                ).astype(float)
    return raw_series


def _get_group_name(col, event_cols):
    return "Window" if col in event_cols else str(col).split("_")[0]


def _column_groups(raw_series, event_cols):
    groups = {}
    for col in raw_series:
        groups.setdefault(_get_group_name(col, event_cols), []).append(col)
    return groups


def _normalise(y):
    denom = y.max() - y.min()
    return (y - y.min()) / denom if denom != 0 else y * 0


def _get_groups(df, date_col, period):
    if period == "Weekly":
        year_start = pd.to_datetime(df[date_col].dt.year.astype(str) + "-01-01")
        week_num = ((df[date_col] - year_start).dt.days // 7) + 1
        df = df.copy()
        df["_group"] = df[date_col].dt.year.astype(str) + "-W" + week_num.astype(str).str.zfill(2)
        df["_start"] = year_start + pd.to_timedelta((week_num - 1) * 7, unit="D")
        df["_end"] = df["_start"] + pd.Timedelta(days=7) - pd.Timedelta(seconds=1)
    elif period == "Monthly":
        df = df.copy()
        month_period = df[date_col].dt.to_period("M")
        df["_group"] = month_period.astype(str)
        df["_start"] = month_period.dt.start_time
        df["_end"] = month_period.dt.end_time
    else:
        df = df.copy()
        df["_group"] = df[date_col].dt.year.astype(str)
        df["_start"] = pd.to_datetime(df[date_col].dt.year.astype(str) + "-01-01")
        df["_end"] = pd.to_datetime(df[date_col].dt.year.astype(str) + "-12-31 23:59:59")

    groups = sorted(df["_group"].dropna().unique())
    return [
        (str(g), df[df["_group"] == g], df[df["_group"] == g]["_start"].iloc[0], df[df["_group"] == g]["_end"].iloc[0])
        for g in groups
    ]


def _get_total_height(n):
    if n <= 4:
        return max(600, 280 * n)
    if n <= 12:
        return max(600, 200 * n)
    return min(6000, max(600, 140 * n))


def _get_tick_settings(period):
    if period == "Monthly":
        return 24 * 60 * 60 * 1000, "%d"
    if period == "Weekly":
        return 24 * 60 * 60 * 1000, "%d %b"
    return None, "%b"


def _y_range(df_part, selected_cols, raw_series, event_cols, normalised):
    vals = []
    for col in selected_cols:
        if col in event_cols:
            continue
        y = raw_series[col].loc[df_part.index]
        vals.append(_normalise(y) if normalised else y)
    if not vals:
        return 0, 1
    all_y = pd.concat(vals).dropna()
    if all_y.empty:
        return 0, 1
    y_min, y_max = all_y.min(), all_y.max()
    if y_min == y_max:
        return y_min - 1, y_max + 1
    pad = (y_max - y_min) * 0.05
    return y_min - pad, y_max + pad


def _add_event_lines(fig, col, df_part, date_col, period_start, period_end,
                     axis_suffix, y_min, y_max, row_idx, color):
    event_df = df_part[[date_col, col]].dropna()
    if col != "input_ToU_label":
        event_df = event_df[event_df[col] != 0]
    if event_df.empty:
        return
    xs, ys = [], []
    for t in event_df[date_col]:
        if period_start <= t <= period_end:
            xs.extend([t, t, None])
            ys.extend([y_min, y_max, None])
    fig.add_trace(go.Scattergl(
        x=xs, y=ys, mode="lines", name=col,
        line=dict(color=color, width=1.5), opacity=0.35,
        xaxis=f"x{axis_suffix}", yaxis=f"y{axis_suffix}",
        legendgroup=col, showlegend=(row_idx == 1),
    ))


def build_figure(df, date_col, raw_series, event_cols, series_colors,
                 period, normalised, selected_cols, page=1, page_size=10, plot_height=200):
    fig = go.Figure()
    groups = _get_groups(df, date_col, period)
    total_groups = len(groups)
    n_pages = max(1, -(-total_groups // page_size))  # ceil division
    page = max(1, min(page, n_pages))
    start = (page - 1) * page_size
    page_groups = groups[start:start + page_size]
    n_groups = max(1, len(page_groups))
    total_height = max(400, plot_height * n_groups)
    dtick, tickformat = _get_tick_settings(period)

    fig.update_layout(
        height=total_height,
        margin=dict(l=30, r=5, t=0, b=20), autosize=True,
        font=dict(size=11),
        grid=dict(rows=n_groups, columns=1, pattern="independent", ygap=0.06),
        legend=dict(orientation="h", x=0, y=1, xanchor="left", yanchor="top",
                    font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
    )

    annotations = []

    for row_idx, (title, df_part, period_start, period_end) in enumerate(page_groups, start=1):
        axis_suffix = "" if row_idx == 1 else str(row_idx)
        y_min, y_max = _y_range(df_part, selected_cols, raw_series, event_cols, normalised)

        xaxis_settings = dict(
            anchor=f"y{axis_suffix}",
            tickfont=dict(size=10), tickangle=0, automargin=True,
            range=[period_start, period_end], tickformat=tickformat,
        )
        if dtick is not None:
            xaxis_settings["dtick"] = dtick
            xaxis_settings["tick0"] = period_start

        fig.layout[f"xaxis{axis_suffix}"] = xaxis_settings
        fig.layout[f"yaxis{axis_suffix}"] = dict(
            anchor=f"x{axis_suffix}", tickfont=dict(size=10),
            automargin=True, range=[y_min, y_max],
        )

        # Add title annotation at top-left of each subplot
        annotations.append(dict(
            text=f"<b>{title}</b>",
            xref=f"x{axis_suffix} domain", yref=f"y{axis_suffix} domain",
            x=0, y=1, xanchor="left", yanchor="bottom",
            font=dict(size=11), showarrow=False,
        ))

        for col in selected_cols:
            if col in event_cols:
                _add_event_lines(fig, col, df_part, date_col, period_start, period_end,
                                 axis_suffix, y_min, y_max, row_idx, series_colors.get(col, "#636EFA"))
            else:
                y = raw_series[col].loc[df_part.index]
                y_plot = _normalise(y) if normalised else y
                fig.add_trace(go.Scattergl(
                    x=df_part[date_col], y=y_plot, mode="lines", name=col,
                    line=dict(color=series_colors.get(col, "#636EFA"), width=1),
                    xaxis=f"x{axis_suffix}", yaxis=f"y{axis_suffix}",
                    legendgroup=col, showlegend=(row_idx == 1),
                ))

    fig.update_layout(annotations=annotations)
    return fig, total_groups, n_pages, page


# In-memory store keyed by session id
_datasets = {}
_file_cache = {}  # Cache uploaded file data to avoid re-reading


def _get_dataset(sid):
    return _datasets.get(sid)


def _set_dataset(sid, df, date_col, event_cols):
    raw_series = _prepare_series(df, date_col, event_cols)
    colors = {col: PLOTLY_COLORS[i % len(PLOTLY_COLORS)] for i, col in enumerate(raw_series)}
    groups = _column_groups(raw_series, event_cols)
    _datasets[sid] = {
        "df": df, "date_col": date_col, "event_cols": event_cols,
        "raw_series": raw_series, "colors": colors, "groups": groups,
    }


# ── Routes ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    sid = session.get("dataset_id")
    ds = _get_dataset(sid) if sid else None
    return render_template("index.html", groups=ds["groups"] if ds else None)


@app.route("/api/upload", methods=["POST"])
def upload():
    """Save file, read it once, cache in memory. Return columns + months + preview."""
    file = request.files.get("file")
    if not file:
        return jsonify(error="No file provided"), 400

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify(error=f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"), 400

    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

    try:
        df, date_col = _load_file(path)
    except Exception as exc:
        return jsonify(error=str(exc)), 400

    sid = os.urandom(8).hex()
    session["dataset_id"] = sid

    # Cache full dataframe for fast ingest (no re-read)
    _file_cache[sid] = {"df": df, "date_col": date_col, "path": path}

    # Compute months quickly using numpy
    months = sorted(df[date_col].dt.to_period("M").unique())
    month_list = [str(m) for m in months]

    columns = [c for c in df.columns if c != date_col]

    # Preview: first 10 rows, convert to lists for fast JSON
    preview_df = df.head(10)
    preview_cols = list(preview_df.columns)
    preview_data = preview_df.values.tolist()
    # Convert timestamps to strings in preview
    for row in preview_data:
        for i, v in enumerate(row):
            if hasattr(v, 'isoformat'):
                row[i] = str(v)
            elif pd.isna(v):
                row[i] = None

    return Response(
        json.dumps({
            "sid": sid,
            "date_col": date_col,
            "columns": columns,
            "months": month_list,
            "row_count": len(df),
            "col_count": len(df.columns),
            "preview": {"columns": preview_cols, "data": preview_data},
        }, default=str),
        mimetype="application/json",
    )


@app.route("/api/ingest", methods=["POST"])
def ingest():
    """Filter cached dataframe by selected columns and months. No file re-read."""
    data = request.get_json(force=True)
    sid = data.get("sid") or session.get("dataset_id")
    cached = _file_cache.get(sid)
    if not cached:
        return jsonify(error="No file uploaded yet"), 400

    session["dataset_id"] = sid  # Sync session

    selected_cols = data.get("columns", [])
    selected_months = set(data.get("months", []))
    event_cols_input = data.get("event_cols", "")
    event_cols = set(c.strip() for c in event_cols_input.split(",") if c.strip())

    df = cached["df"]
    date_col = cached["date_col"]

    # Filter months using vectorized period comparison
    if selected_months:
        period_strs = df[date_col].dt.to_period("M").astype(str)
        df = df[period_strs.isin(selected_months)]

    # Select only requested columns
    keep_cols = [date_col] + [c for c in selected_cols if c in df.columns]
    df = df[keep_cols].reset_index(drop=True)

    _set_dataset(sid, df, date_col, event_cols)

    ds = _get_dataset(sid)
    return jsonify(groups=ds["groups"], row_count=len(df), col_count=len(df.columns))


@app.route("/api/check-cache", methods=["POST"])
def check_cache():
    """Check if a sid is still cached on the server (avoids re-upload)."""
    data = request.get_json(force=True)
    sid = data.get("sid")
    if sid and sid in _file_cache:
        cached = _file_cache[sid]
        df = cached["df"]
        date_col = cached["date_col"]
        months = sorted(df[date_col].dt.to_period("M").unique())
        columns = [c for c in df.columns if c != date_col]
        return jsonify(cached=True, sid=sid, date_col=date_col, columns=columns,
                       months=[str(m) for m in months],
                       row_count=len(df), col_count=len(df.columns))
    return jsonify(cached=False)


@app.route("/api/figure", methods=["POST"])
def figure():
    sid = session.get("dataset_id")
    ds = _get_dataset(sid) if sid else None
    if not ds:
        return jsonify(error="No dataset loaded"), 400

    data = request.get_json(force=True)
    period = data.get("period", "Yearly")
    normalised = bool(data.get("normalised", False))
    selected_cols = data.get("selected_cols", [])
    page = int(data.get("page", 1))
    page_size = int(data.get("page_size", 10))
    plot_height = int(data.get("plot_height", 200))

    fig, total_groups, n_pages, current_page = build_figure(
        ds["df"], ds["date_col"], ds["raw_series"], ds["event_cols"],
        ds["colors"], period, normalised, selected_cols, page, page_size, plot_height,
    )
    # Serialize figure and add pagination metadata
    fig_json = json.loads(plotly.io.to_json(fig))
    fig_json["_pagination"] = {
        "page": current_page,
        "n_pages": n_pages,
        "total_groups": total_groups,
        "page_size": page_size,
    }
    return Response(json.dumps(fig_json), mimetype="application/json")


if __name__ == "__main__":
    import os as _os
    debug = _os.environ.get("FLASK_DEBUG", "1") == "1"
    port = int(_os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=debug)
