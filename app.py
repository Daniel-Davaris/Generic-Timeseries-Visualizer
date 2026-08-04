import os
import json
import csv
import io

import pandas as pd
import plotly
import plotly.graph_objs as go
from flask import Flask, render_template, request, jsonify, session, Response
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://tsapp:ts1ntel2024!@localhost:5432/timeseries_db")

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


def _get_page_groups(df, date_col, period, page, page_size, sort_desc=False):
    """Group rows by period and materialize ONLY the requested page of groups."""
    d = df[date_col]
    if period == "Weekly":
        year_start = pd.to_datetime(d.dt.year.astype(str) + "-01-01")
        week_num = ((d - year_start).dt.days // 7) + 1
        labels = d.dt.year.astype(str) + "-W" + week_num.astype(str).str.zfill(2)
        starts = year_start + pd.to_timedelta((week_num - 1) * 7, unit="D")
        ends = starts + pd.Timedelta(days=7) - pd.Timedelta(seconds=1)
    elif period == "Monthly":
        month_period = d.dt.to_period("M")
        labels = month_period.astype(str)
        starts = month_period.dt.start_time
        ends = month_period.dt.end_time
    else:
        labels = d.dt.year.astype(str)
        starts = pd.to_datetime(labels + "-01-01")
        ends = pd.to_datetime(labels + "-12-31 23:59:59")

    # Integer codes per row; uniques come back sorted. No sub-frame is built here.
    codes, uniques = pd.factorize(labels, sort=True)
    total_groups = len(uniques)
    n_pages = max(1, -(-total_groups // page_size))  # ceil division
    page = max(1, min(page, n_pages))
    start = (page - 1) * page_size

    order = list(range(total_groups))
    if sort_desc:
        order.reverse()

    page_groups = []
    for gi in order[start:start + page_size]:
        mask = codes == gi
        page_groups.append((str(uniques[gi]), df.loc[mask],
                            starts.loc[mask].iloc[0], ends.loc[mask].iloc[0]))
    return page_groups, total_groups, n_pages, page


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
                 period, normalised, selected_cols, page=1, page_size=10, plot_height=200,
                 sort_desc=False):
    fig = go.Figure()
    page_groups, total_groups, n_pages, page = _get_page_groups(df, date_col, period, page, page_size, sort_desc)
    n_groups = max(1, len(page_groups))
    total_height = max(400, plot_height * n_groups)
    dtick, tickformat = _get_tick_settings(period)

    fig.update_layout(
        height=total_height,
        margin=dict(l=2, r=5, t=30, b=20), autosize=True,
        font=dict(size=11),
        grid=dict(rows=n_groups, columns=1, pattern="independent", ygap=0.06),
        legend=dict(orientation="h", x=0, y=1, xanchor="left", yanchor="bottom",
                    font=dict(size=10), bgcolor="rgba(0,0,0,0)",
                    xref="container", yref="container"),
    )

    annotations = []
    # Tight left gutter: title text + room for y tick labels, no extra padding.
    max_label = max((len(t) for t, _, _, _ in page_groups), default=4)
    title_frac = min(0.11, 0.0045 * max_label + 0.03)

    for row_idx, (title, df_part, period_start, period_end) in enumerate(page_groups, start=1):
        axis_suffix = "" if row_idx == 1 else str(row_idx)
        y_min, y_max = _y_range(df_part, selected_cols, raw_series, event_cols, normalised)

        xaxis_settings = dict(
            anchor=f"y{axis_suffix}",
            tickfont=dict(size=10), tickangle=0, automargin=True,
            range=[period_start, period_end], tickformat=tickformat,
            domain=[title_frac, 1.0],
        )
        if dtick is not None:
            xaxis_settings["dtick"] = dtick
            xaxis_settings["tick0"] = period_start

        fig.layout[f"xaxis{axis_suffix}"] = xaxis_settings
        fig.layout[f"yaxis{axis_suffix}"] = dict(
            anchor=f"x{axis_suffix}", tickfont=dict(size=10),
            automargin=True, range=[y_min, y_max],
        )

        # Title annotation in the left gutter, vertically centered on its subplot
        annotations.append(dict(
            text=f"<b>{title}</b>",
            xref="paper", yref=f"y{axis_suffix} domain",
            x=0, y=0.5, xanchor="left", yanchor="middle",
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
    return jsonify(groups=ds["groups"], colors=ds["colors"], row_count=len(df), col_count=len(df.columns))


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
    sort_desc = bool(data.get("sort_desc", False))

    fig, total_groups, n_pages, current_page = build_figure(
        ds["df"], ds["date_col"], ds["raw_series"], ds["event_cols"],
        ds["colors"], period, normalised, selected_cols, page, page_size, plot_height,
        sort_desc,
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


# ══════════════════════════════════════════════════════════════════════
# DATABASE EXPLORER API
# ══════════════════════════════════════════════════════════════════════

def _get_db_conn():
    """Get a database connection."""
    import psycopg2
    return psycopg2.connect(DATABASE_URL)


@app.route("/db")
def db_explorer():
    return render_template("db_explorer.html")


@app.route("/info")
def info_page():
    return render_template("info.html")

@app.route("/api/catalogue")
def serve_catalogue():
    """Serve the AEMO data catalogue markdown with explicit UTF-8 encoding."""
    import os
    md_path = os.path.join(app.static_folder, "aemo_data_catalogue.md")
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    return content, 200, {"Content-Type": "text/plain; charset=utf-8"}

def _ensure_groups_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS _table_groups (
            table_name TEXT PRIMARY KEY,
            group_name TEXT NOT NULL
        )
    """)


@app.route("/api/db/tables", methods=["GET"])
def db_tables():
    """List all tables with row counts and group assignments."""
    conn = _get_db_conn()
    try:
        cur = conn.cursor()
        _ensure_groups_table(cur)
        conn.commit()
        cur.execute("""
            SELECT t.table_name,
                   pg_stat_user_tables.n_live_tup as row_count,
                   g.group_name
            FROM information_schema.tables t
            LEFT JOIN pg_stat_user_tables ON pg_stat_user_tables.relname = t.table_name
            LEFT JOIN _table_groups g ON g.table_name = t.table_name
            WHERE t.table_schema = 'public' AND t.table_type = 'BASE TABLE'
              AND t.table_name <> '_table_groups'
            ORDER BY t.table_name;
        """)
        tables = []
        for row in cur.fetchall():
            tables.append({"name": row[0], "row_count": row[1] or 0, "group": row[2]})
        return jsonify(tables=tables)
    finally:
        conn.close()


@app.route("/api/db/table-group", methods=["POST"])
def db_set_table_group():
    """Assign a table to a group (empty/null group removes the assignment)."""
    data = request.get_json(force=True)
    table = (data.get("table") or "").strip()
    group = (data.get("group") or "").strip()
    if not table:
        return jsonify(error="No table specified"), 400

    conn = _get_db_conn()
    try:
        cur = conn.cursor()
        _ensure_groups_table(cur)
        cur.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name=%s",
            (table,),
        )
        if not cur.fetchone():
            return jsonify(error="Table not found"), 404
        if group:
            cur.execute("""
                INSERT INTO _table_groups (table_name, group_name) VALUES (%s, %s)
                ON CONFLICT (table_name) DO UPDATE SET group_name = EXCLUDED.group_name
            """, (table, group))
        else:
            cur.execute("DELETE FROM _table_groups WHERE table_name = %s", (table,))
        conn.commit()
        return jsonify(table=table, group=group or None)
    except Exception as exc:
        conn.rollback()
        return jsonify(error=str(exc)), 400
    finally:
        conn.close()


@app.route("/api/db/schema/<table_name>", methods=["GET"])
def db_schema(table_name):
    """Get column info for a table."""
    conn = _get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position;
        """, (table_name,))
        columns = []
        for row in cur.fetchall():
            columns.append({
                "name": row[0], "type": row[1],
                "nullable": row[2] == "YES", "default": row[3]
            })
        return jsonify(table=table_name, columns=columns)
    finally:
        conn.close()


@app.route("/api/db/preview/<table_name>", methods=["GET"])
def db_preview(table_name):
    """Preview first N rows of a table."""
    limit = min(int(request.args.get("limit", 100)), 1000)
    conn = _get_db_conn()
    try:
        cur = conn.cursor()
        # Validate table name to prevent SQL injection
        cur.execute("SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name=%s", (table_name,))
        if not cur.fetchone():
            return jsonify(error="Table not found"), 404
        cur.execute(f'SELECT * FROM "{table_name}" LIMIT %s;', (limit,))
        cols = [desc[0] for desc in cur.description]
        rows = []
        for row in cur.fetchall():
            rows.append([str(v) if v is not None else None for v in row])
        return jsonify(columns=cols, rows=rows, total_shown=len(rows))
    finally:
        conn.close()


@app.route("/api/db/query", methods=["POST"])
def db_query():
    """Execute a read-only SQL query."""
    data = request.get_json(force=True)
    sql = data.get("sql", "").strip()
    if not sql:
        return jsonify(error="No SQL provided"), 400

    # Block dangerous statements
    sql_upper = sql.upper().lstrip()
    allowed_starts = ("SELECT", "WITH", "EXPLAIN")
    if not any(sql_upper.startswith(s) for s in allowed_starts):
        return jsonify(error="Only SELECT/WITH/EXPLAIN queries are allowed"), 403

    conn = _get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql)
        cols = [desc[0] for desc in cur.description] if cur.description else []
        rows = []
        if cols:
            for row in cur.fetchmany(5000):
                rows.append([str(v) if v is not None else None for v in row])
        return jsonify(columns=cols, rows=rows, row_count=len(rows))
    except Exception as e:
        conn.rollback()
        return jsonify(error=str(e)), 400
    finally:
        conn.close()


import re as _re

def _pg_ident(name, prefix="col"):
    """Sanitize an identifier for PostgreSQL: lowercase, alnum + underscore."""
    s = _re.sub(r"[^a-zA-Z0-9]+", "_", str(name)).strip("_").lower()
    if not s or s[0].isdigit():
        s = f"{prefix}_{s}"
    return s[:63]


def _pg_type_for_dtype(dtype):
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"
    if pd.api.types.is_integer_dtype(dtype):
        return "BIGINT"
    if pd.api.types.is_float_dtype(dtype):
        return "DOUBLE PRECISION"
    if pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"
    return "TEXT"


@app.route("/api/db/upload", methods=["POST"])
def db_upload():
    """Create a new table from an uploaded file (CSV / Excel / Parquet / JSON)."""
    file = request.files.get("file")
    if not file:
        return jsonify(error="No file provided"), 400

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    allowed = {".csv", ".tsv", ".txt", ".parquet", ".parq", ".xlsx", ".xls", ".json"}
    if ext not in allowed:
        return jsonify(error=f"Unsupported file type. Allowed: {', '.join(sorted(allowed))}"), 400

    mode = request.form.get("mode", "fail")  # fail | replace | append
    if mode not in ("fail", "replace", "append"):
        return jsonify(error="mode must be fail, replace or append"), 400

    raw_name = request.form.get("table_name") or os.path.splitext(filename)[0]
    table = _pg_ident(raw_name, prefix="t")
    if not table:
        return jsonify(error="Invalid table name"), 400

    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

    try:
        if ext in (".csv", ".txt"):
            df = pd.read_csv(path)
        elif ext == ".tsv":
            df = pd.read_csv(path, sep="\t")
        elif ext in (".parquet", ".parq"):
            df = pd.read_parquet(path)
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(path)
        else:  # .json
            df = pd.read_json(path)
    except Exception as exc:
        return jsonify(error=f"Could not read file: {exc}"), 400
    finally:
        try:
            os.remove(path)
        except OSError:
            pass

    if df.empty or len(df.columns) == 0:
        return jsonify(error="File contains no data"), 400
    if len(df.columns) > 1500:
        return jsonify(error=f"Too many columns ({len(df.columns)}). Max 1500."), 400

    # Try to parse object columns that look like dates
    for c in df.columns:
        if df[c].dtype == object:
            try:
                parsed = pd.to_datetime(df[c], errors="raise", format="mixed")
                df[c] = parsed
            except Exception:
                pass

    # Sanitized, deduped column names
    cols, seen = [], {}
    for c in df.columns:
        s = _pg_ident(c)
        if s in seen:
            seen[s] += 1
            s = f"{s}_{seen[s]}"
        else:
            seen[s] = 0
        cols.append(s)
    df.columns = cols

    conn = _get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name=%s",
            (table,),
        )
        exists = cur.fetchone() is not None

        if exists and mode == "fail":
            return jsonify(error=f'Table "{table}" already exists. Choose replace or append.'), 409
        if exists and mode == "replace":
            cur.execute(f'DROP TABLE "{table}" CASCADE')
            exists = False

        if not exists:
            cols_sql = ", ".join(
                f'"{c}" {_pg_type_for_dtype(df[c].dtype)}' for c in df.columns
            )
            cur.execute(f'CREATE TABLE "{table}" ({cols_sql})')

        buf = io.StringIO()
        df.to_csv(buf, sep="\t", header=False, index=False, na_rep="\\N")
        buf.seek(0)
        quoted = ", ".join(f'"{c}"' for c in df.columns)
        cur.copy_expert(
            f"COPY \"{table}\" ({quoted}) FROM STDIN WITH (FORMAT csv, DELIMITER E'\t', NULL '\\N')",
            buf,
        )
        conn.commit()
        return jsonify(
            table=table,
            rows=len(df),
            columns=len(df.columns),
            mode="appended" if (exists and mode == "append") else "created",
        )
    except Exception as exc:
        conn.rollback()
        return jsonify(error=str(exc)), 400
    finally:
        conn.close()


@app.route("/api/db/table-meta/<table_name>", methods=["GET"])
def db_table_meta(table_name):
    """Metadata for the visualizer wizard: date column, columns, months, preview.
    Everything is computed in SQL — no bulk data leaves the database."""
    conn = _get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT column_name, data_type FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position;
        """, (table_name,))
        cols = cur.fetchall()
        if not cols:
            return jsonify(error="Table not found"), 404

        date_col = None
        for name, dtype in cols:
            if dtype.startswith("timestamp") or dtype == "date":
                date_col = name
                break
        if date_col is None:
            return jsonify(error="No date/time column found in this table"), 400

        columns = [c for c, _ in cols if c != date_col]

        cur.execute(
            f'SELECT DISTINCT to_char("{date_col}", \'YYYY-MM\') FROM "{table_name}" '
            f'WHERE "{date_col}" IS NOT NULL ORDER BY 1'
        )
        months = [r[0] for r in cur.fetchall()]

        cur.execute(f'SELECT count(*) FROM "{table_name}"')
        row_count = cur.fetchone()[0]

        cur.execute(f'SELECT * FROM "{table_name}" ORDER BY "{date_col}" LIMIT 10')
        prev_cols = [d[0] for d in cur.description]
        prev_rows = [
            [str(v) if v is not None else None for v in row] for row in cur.fetchall()
        ]

        return jsonify(
            table=table_name, date_col=date_col, columns=columns, months=months,
            row_count=row_count, col_count=len(cols),
            preview={"columns": prev_cols, "data": prev_rows},
        )
    finally:
        conn.close()


@app.route("/api/db/ingest", methods=["POST"])
def db_ingest():
    """Load selected columns/months of a DB table into the visualizer dataset.
    Streams straight from PostgreSQL COPY into pandas — only the requested
    subset ever leaves the database."""
    data = request.get_json(force=True)
    table = (data.get("table") or "").strip()
    selected_cols = data.get("columns", [])
    selected_months = data.get("months", [])
    event_cols_input = data.get("event_cols", "")
    event_cols = set(c.strip() for c in event_cols_input.split(",") if c.strip())

    if not table:
        return jsonify(error="No table specified"), 400
    if not selected_cols:
        return jsonify(error="No columns selected"), 400

    conn = _get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT column_name, data_type FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
        """, (table,))
        col_types = dict(cur.fetchall())
        if not col_types:
            return jsonify(error="Table not found"), 404

        date_col = None
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
              AND (data_type LIKE 'timestamp%%' OR data_type = 'date')
            ORDER BY ordinal_position LIMIT 1
        """, (table,))
        row = cur.fetchone()
        if row:
            date_col = row[0]
        if date_col is None:
            return jsonify(error="No date/time column found"), 400

        # Only keep columns that really exist (prevents injection)
        keep = [c for c in selected_cols if c in col_types and c != date_col]
        if not keep:
            return jsonify(error="No valid columns selected"), 400

        col_sql = ", ".join(f'"{c}"' for c in [date_col] + keep)
        where = f'"{date_col}" IS NOT NULL'
        params = []
        if selected_months:
            where += f' AND to_char("{date_col}", \'YYYY-MM\') = ANY(%s)'
            params.append(list(selected_months))

        query = (
            f'SELECT {col_sql} FROM "{table}" WHERE {where} ORDER BY "{date_col}"'
        )
        # COPY → CSV buffer → pandas C parser: fastest path out of Postgres
        buf = io.StringIO()
        copy_sql = cur.mogrify(query, params).decode()
        cur.copy_expert(f"COPY ({copy_sql}) TO STDOUT WITH (FORMAT csv, HEADER)", buf)
        buf.seek(0)
        df = pd.read_csv(buf, parse_dates=[date_col])
        del buf

        sid = "db_" + os.urandom(6).hex()
        session["dataset_id"] = sid
        _set_dataset(sid, df, date_col, event_cols)

        ds = _get_dataset(sid)
        return jsonify(
            sid=sid, groups=ds["groups"], colors=ds["colors"], row_count=len(df), col_count=len(df.columns)
        )
    except Exception as exc:
        return jsonify(error=str(exc)), 400
    finally:
        conn.close()


@app.route("/api/db/export/<table_name>", methods=["GET"])
def db_export(table_name):
    """Export a table as CSV."""
    conn = _get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name=%s", (table_name,))
        if not cur.fetchone():
            return jsonify(error="Table not found"), 404
        cur.execute(f'SELECT * FROM "{table_name}";')
        cols = [desc[0] for desc in cur.description]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(cols)
        for row in cur:
            writer.writerow(row)

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={table_name}.csv"}
        )
    finally:
        conn.close()


if __name__ == "__main__":
    import os as _os
    debug = _os.environ.get("FLASK_DEBUG", "1") == "1"
    port = int(_os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=debug)
