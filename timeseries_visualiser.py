import pandas as pd
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output, State, ALL, ctx


CSV_PATH = "optimizer/2_Optimizer/Optimization_data/optimization_results.csv"

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)

optimization_output = pd.read_csv(CSV_PATH)
optimization_output["input_Date"] = pd.to_datetime(optimization_output["input_Date"])
optimization_output = optimization_output.sort_values("input_Date")

x_col = "input_Date"
event_cols = {"input_ToU_label", "input_Trade_signal", "window"}

raw_series = {}
plotly_colors = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52"]

for col in optimization_output.columns:
    if col == x_col:
        continue
    if col in event_cols:
        raw_series[col] = optimization_output[col]
    else:
        try:
            raw_series[col] = optimization_output[col].astype(float)
        except Exception:
            raw_series[col] = pd.Series(pd.factorize(optimization_output[col])[0], index=optimization_output.index).astype(float)

series_colors = {col: plotly_colors[i % len(plotly_colors)] for i, col in enumerate(raw_series.keys())}


def get_group_name(col):
    return "Window" if col in event_cols else str(col).split("_")[0]


column_groups = {}
for col in raw_series.keys():
    column_groups.setdefault(get_group_name(col), []).append(col)


def normalise_within_group(y):
    denom = y.max() - y.min()
    return (y - y.min()) / denom if denom != 0 else y * 0


def get_groups(period):
    df = optimization_output.copy()

    if period == "Weekly":
        year_start = pd.to_datetime(df[x_col].dt.year.astype(str) + "-01-01")
        week_num = ((df[x_col] - year_start).dt.days // 7) + 1
        df["_group"] = df[x_col].dt.year.astype(str) + "-W" + week_num.astype(str).str.zfill(2)
        df["_start"] = year_start + pd.to_timedelta((week_num - 1) * 7, unit="D")
        df["_end"] = df["_start"] + pd.Timedelta(days=7) - pd.Timedelta(seconds=1)

    elif period == "Monthly":
        month_period = df[x_col].dt.to_period("M")
        df["_group"] = month_period.astype(str)
        df["_start"] = month_period.dt.start_time
        df["_end"] = month_period.dt.end_time

    else:
        df["_group"] = df[x_col].dt.year.astype(str)
        df["_start"] = pd.to_datetime(df[x_col].dt.year.astype(str) + "-01-01")
        df["_end"] = pd.to_datetime(df[x_col].dt.year.astype(str) + "-12-31 23:59:59")

    groups = sorted(df["_group"].dropna().unique())
    return [(str(g), df[df["_group"] == g], df[df["_group"] == g]["_start"].iloc[0], df[df["_group"] == g]["_end"].iloc[0]) for g in groups]


def get_total_height(n_groups):
    if n_groups <= 4:
        return max(800, 320 * n_groups)
    if n_groups <= 12:
        return max(800, 230 * n_groups)
    return min(7500, max(800, 150 * n_groups))


def get_tick_settings(period):
    if period == "Monthly":
        return 24 * 60 * 60 * 1000, "%d"
    if period == "Weekly":
        return 24 * 60 * 60 * 1000, "%d %b"
    return None, "%b"


def get_y_range(df_part, selected_cols, normalised):
    vals = []

    for col in selected_cols:
        if col in event_cols:
            continue
        y = raw_series[col].loc[df_part.index]
        y = normalise_within_group(y) if normalised else y
        vals.append(y)

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


def add_event_lines(fig, col, df_part, period_start, period_end, axis_suffix, y_min, y_max, row_idx):
    event_df = df_part[[x_col, col]].dropna()
    event_df = event_df[event_df[col] != 0] if col != "input_ToU_label" else event_df

    if event_df.empty:
        return

    xs, ys = [], []

    for t in event_df[x_col]:
        if period_start <= t <= period_end:
            xs.extend([t, t, None])
            ys.extend([y_min, y_max, None])

    fig.add_trace(
        go.Scattergl(
            x=xs,
            y=ys,
            mode="lines",
            name=col,
            line=dict(color=series_colors[col], width=3),
            opacity=0.35,
            xaxis=f"x{axis_suffix}",
            yaxis=f"y{axis_suffix}",
            legendgroup=col,
            showlegend=(row_idx == 1)
        )
    )


def build_fig(period, normalised, selected_cols):
    fig = go.Figure()
    groups = get_groups(period)
    n_groups = max(1, len(groups))
    total_height = get_total_height(n_groups)
    dtick, tickformat = get_tick_settings(period)

    fig.update_layout(
        height=total_height,
        width=1700,
        margin=dict(l=55, r=40, t=80, b=90),
        autosize=False,
        title=dict(text=f"{period} - {'Normalised within each graph' if normalised else 'Raw'}", font=dict(size=15)),
        font=dict(size=11),
        grid=dict(rows=n_groups, columns=1, pattern="independent", ygap=0.22)
    )

    for row_idx, (title, df_part, period_start, period_end) in enumerate(groups, start=1):
        axis_suffix = "" if row_idx == 1 else str(row_idx)
        y_min, y_max = get_y_range(df_part, selected_cols, normalised)

        xaxis_settings = dict(
            anchor=f"y{axis_suffix}",
            title=dict(text=title, font=dict(size=13), standoff=12),
            tickfont=dict(size=11),
            tickangle=0,
            automargin=True,
            range=[period_start, period_end],
            tickformat=tickformat
        )

        if dtick is not None:
            xaxis_settings["dtick"] = dtick
            xaxis_settings["tick0"] = period_start

        fig.layout[f"xaxis{axis_suffix}"] = xaxis_settings
        fig.layout[f"yaxis{axis_suffix}"] = dict(anchor=f"x{axis_suffix}", tickfont=dict(size=11), automargin=True, range=[y_min, y_max])

        for col in selected_cols:
            if col in event_cols:
                add_event_lines(fig, col, df_part, period_start, period_end, axis_suffix, y_min, y_max, row_idx)
            else:
                y = raw_series[col].loc[df_part.index]
                y_plot = normalise_within_group(y) if normalised else y

                fig.add_trace(
                    go.Scattergl(
                        x=df_part[x_col],
                        y=y_plot,
                        mode="lines",
                        name=col,
                        line=dict(color=series_colors[col]),
                        xaxis=f"x{axis_suffix}",
                        yaxis=f"y{axis_suffix}",
                        legendgroup=col,
                        showlegend=(row_idx == 1)
                    )
                )

    return fig


app = Dash(__name__)

app.layout = html.Div(
    [
        dcc.Store(id="period-store", data="Yearly"),
        dcc.Store(id="normalised-store", data=False),

        html.Div(
            [
                html.Button("Weekly", id="weekly-button", n_clicks=0),
                html.Button("Monthly", id="monthly-button", n_clicks=0),
                html.Button("Yearly", id="yearly-button", n_clicks=0),
                html.Button("Show normalised", id="normalise-button", n_clicks=0),
                html.Button("Apply selection", id="apply-button", n_clicks=0)
            ],
            style={"display": "flex", "gap": "8px", "marginBottom": "10px"}
        ),

        html.Div(
            [
                html.Div(
                    [
                        html.Details(
                            [
                                html.Summary(group),
                                html.Button("Select all", id={"type": "select-group", "group": group}, n_clicks=0),
                                html.Button("Clear", id={"type": "clear-group", "group": group}, n_clicks=0),
                                dcc.Checklist(
                                    id={"type": "checklist", "group": group},
                                    options=[{"label": col, "value": col} for col in cols],
                                    value=[],
                                    style={"marginTop": "6px"}
                                )
                            ],
                            open=False,
                            style={"marginBottom": "10px"}
                        )
                        for group, cols in column_groups.items()
                    ],
                    style={"width": "470px", "maxHeight": "1000px", "overflowY": "auto", "border": "2px solid gray", "padding": "5px"}
                ),

                dcc.Graph(id="main-graph", figure=build_fig("Yearly", False, []), style={"width": "1700px"})
            ],
            style={"display": "flex", "alignItems": "flex-start", "gap": "10px"}
        )
    ]
)


@app.callback(
    Output("period-store", "data"),
    Input("weekly-button", "n_clicks"),
    Input("monthly-button", "n_clicks"),
    Input("yearly-button", "n_clicks"),
    State("period-store", "data")
)
def update_period(_, __, ___, current):
    trigger = ctx.triggered_id

    if trigger == "weekly-button":
        return "Weekly"
    if trigger == "monthly-button":
        return "Monthly"
    if trigger == "yearly-button":
        return "Yearly"

    return current


@app.callback(
    Output("normalised-store", "data"),
    Output("normalise-button", "children"),
    Input("normalise-button", "n_clicks"),
    State("normalised-store", "data")
)
def update_normalised(_, current):
    if not ctx.triggered_id:
        return current, "Show normalised"

    new_value = not current
    return new_value, "Show raw" if new_value else "Show normalised"


@app.callback(
    Output({"type": "checklist", "group": ALL}, "value"),
    Input({"type": "select-group", "group": ALL}, "n_clicks"),
    Input({"type": "clear-group", "group": ALL}, "n_clicks"),
    State({"type": "checklist", "group": ALL}, "value"),
    prevent_initial_call=True
)
def update_group_checks(_, __, current_values):
    trigger = ctx.triggered_id

    if not isinstance(trigger, dict):
        return current_values

    groups = list(column_groups.keys())
    output = list(current_values)
    idx = groups.index(trigger["group"])

    if trigger["type"] == "select-group":
        output[idx] = column_groups[trigger["group"]]
    elif trigger["type"] == "clear-group":
        output[idx] = []

    return output


@app.callback(
    Output("main-graph", "figure"),
    Input("apply-button", "n_clicks"),
    Input("period-store", "data"),
    Input("normalised-store", "data"),
    State({"type": "checklist", "group": ALL}, "value")
)
def update_graph(_, period, normalised, checklist_values):
    selected_cols = []

    for values in checklist_values:
        selected_cols.extend(values)

    return build_fig(period, normalised, selected_cols)


if __name__ == "__main__":
    app.run(debug=True)