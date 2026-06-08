"""Plotly cure-profile chart: measured temperature/pressure/vacuum vs. the
spec window. Rendering only — the deterministic pass/fail lives in window.py.
"""
import plotly.graph_objects as go

from .models import CureRun

_INK = "#1b1d22"
_GRID = "rgba(27,29,34,0.08)"
_TEMP = "#b91c1c"
_PRESSURE = "#1f6feb"
_VACUUM = "#2f7d4f"
_BAND = "rgba(47,125,79,0.12)"


def cure_profile_html(run: CureRun) -> str:
    points = sorted(run.profile, key=lambda p: p["minute"])
    minutes = [p["minute"] for p in points]
    spec = run.spec

    fig = go.Figure()
    # Acceptable soak-temperature band.
    fig.add_hrect(
        y0=spec.soak_temp_min,
        y1=spec.soak_temp_max,
        fillcolor=_BAND,
        line_width=0,
        layer="below",
        annotation_text="soak window",
        annotation_position="top left",
    )
    fig.add_trace(
        go.Scatter(
            x=minutes,
            y=[p["temperature"] for p in points],
            name="Temp °C",
            line={"color": _TEMP, "width": 3},
            mode="lines+markers",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=minutes,
            y=[p["pressure"] for p in points],
            name="Pressure psi",
            line={"color": _PRESSURE, "width": 1.5, "dash": "dot"},
            yaxis="y2",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=minutes,
            y=[p["vacuum"] for p in points],
            name="Vacuum inHg",
            line={"color": _VACUUM, "width": 1.5, "dash": "dash"},
            yaxis="y2",
        )
    )
    fig.update_layout(
        height=420,
        margin={"l": 56, "r": 56, "t": 24, "b": 48},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "IBM Plex Mono, monospace", "size": 12, "color": _INK},
        xaxis={"title": "elapsed (min)", "gridcolor": _GRID, "zeroline": False},
        yaxis={"title": "temperature °C", "gridcolor": _GRID, "zeroline": False},
        yaxis2={
            "title": "pressure / vacuum",
            "overlaying": "y",
            "side": "right",
            "showgrid": False,
        },
        legend={"orientation": "h", "y": -0.2},
        hovermode="x unified",
    )
    return fig.to_html(
        full_html=False, include_plotlyjs="cdn", config={"displayModeBar": False}
    )
