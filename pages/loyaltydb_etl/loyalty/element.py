from dash import Dash, html, dash_table, dcc, callback, Output, Input


class FilterComponent:
    def __init__(self, id: str, col, data, default=None, clearable=True, values=[]):
        self.id = id
        self.data = data
        self.col = col
        self.default = (
            data[col].sort_values().unique().tolist() if default is None else default
        )
        self.clearable = clearable
        self.values = values


class Dropdown(FilterComponent):
    @property
    def elem(self):
        return dcc.Dropdown(
            id=self.id,
            options=[{"label": grp, "value": grp} for grp in self.values],
            value=self.values,
            default=self.default,
            multi=True,
            clearable=self.clearable,
            style={"font-family": "Helvetica"},
        )


class Checklist(FilterComponent):
    def __init__(self, horizontal=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.horizontal = horizontal

    @property
    def elem(self):
        return dcc.Checklist(
            id=self.id,
            options=[{"label": grp, "value": grp} for grp in self.values],
            value=self.default,
            style={"marginTop": 5, "marginBottom": 10, "font-family": "Helvetica"},
            inline=self.horizontal,
        )


class DataTable:
    def __init__(self, id: str, cols, kwargs={}):
        self.id = id
        self.cols = cols
        self.kwargs = kwargs

    @property
    def elem(self):
        return dash_table.DataTable(
            id=self.id,
            columns=[{"name": col, "id": col} for col in self.cols],
            style_header={
                "backgroundColor": "rgb(204, 229, 255)",
                "color": "black",
                "fontWeight": "bold",
                "textAlign": "center",
            },
            style_cell={
                "textAlign": "center",
                "whiteSpace": "normal",
                "font-family": "Helvetica",
                "font-size": "14px",
            },
            **self.kwargs
        )
