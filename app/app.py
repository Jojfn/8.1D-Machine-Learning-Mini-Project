"""Sydney Housing Price Decision Support System.

Streamlit front end for the model trained in 8.1D.ipynb.

Run with:   python -m streamlit run app/app.py

The model file app/price_model.joblib is produced by Part 6 of the notebook. joblib is the
standard format for a scikit-learn pipeline and this file is generated locally by the notebook
in this same project, so it is not untrusted input.
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

MODEL_PATH = Path(__file__).parent / "price_model.joblib"
HOUSE_LIKE = ["House", "Duplex", "Semi", "Townhouse"]

st.set_page_config(page_title="Sydney Housing Price Estimator", page_icon="🏠", layout="wide")


@st.cache_resource
def load_model():
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)


bundle = load_model()
if bundle is None:
    st.error(
        "Model file not found. Run Part 6 of `8.1D.ipynb` first — it writes "
        "`app/price_model.joblib`."
    )
    st.stop()

PIPE = bundle["pipeline"]
NUMERIC, CATEGORICAL = bundle["numeric"], bundle["categorical"]
DEFAULTS = bundle["defaults"]


def build_features(row: dict) -> pd.DataFrame:
    """Recreate exactly the engineered features the notebook built during training."""
    d = dict(row)
    land = d.get("land_size_sqm")
    internal = d.get("internal_area_sqm")

    d["is_house"] = int(d["property_type"] in HOUSE_LIKE)
    d["total_rooms"] = d["bedrooms"] + d["bathrooms"]
    d["bath_per_bed"] = d["bathrooms"] / d["bedrooms"] if d["bedrooms"] else np.nan
    d["has_land"] = int(pd.notna(land))
    d["has_internal"] = int(pd.notna(internal))
    d["sold_at_auction"] = int(d.get("sale_method") == "Auction")
    d["sale_month_index"] = DEFAULTS["sale_month_index"]

    for col in NUMERIC:
        d.setdefault(col, np.nan)
    return pd.DataFrame([d])[NUMERIC + CATEGORICAL]


def predict(frame: pd.DataFrame) -> np.ndarray:
    return np.exp(PIPE.predict(frame))


st.title("🏠 Sydney Housing Price Estimator")
st.caption(
    f"{bundle['model_name']} trained on {bundle['trained_on']} sold properties in "
    f"{', '.join(bundle['suburbs'])} — sales from {bundle['date_min']} to {bundle['date_max']}."
)

single, batch, about = st.tabs(["Estimate one property", "Upload a CSV", "About this model"])

# ----------------------------------------------------------------- single property
with single:
    left, right = st.columns([1, 1])

    with left:
        st.subheader("Property details")
        suburb = st.selectbox("Suburb", bundle["suburbs"])
        property_type = st.selectbox("Property type", bundle["property_types"])
        is_house = property_type in HOUSE_LIKE

        c1, c2, c3 = st.columns(3)
        bedrooms = c1.number_input("Bedrooms", 0, 10, 3,
                                   help="0 for a studio")
        bathrooms = c2.number_input("Bathrooms", 1, 8, 2)
        car_spaces = c3.number_input("Car spaces", 0, 6, 1)

        land = internal = np.nan
        if is_house:
            if st.checkbox("Land size is known", value=True):
                land = st.number_input("Land size (sqm)", 50.0, 3000.0, 550.0, step=10.0)
        else:
            if st.checkbox("Internal area is known", value=False):
                internal = st.number_input("Internal area (sqm)", 20.0, 300.0, 100.0, step=5.0)

        sale_method = st.radio("Sale method", ["Private treaty", "Auction"], horizontal=True)

    with right:
        st.subheader("Estimated sale price")
        if st.button("Estimate price", type="primary", use_container_width=True):
            features = build_features({
                "suburb": suburb, "property_type": property_type, "bedrooms": bedrooms,
                "bathrooms": bathrooms, "car_spaces": car_spaces, "land_size_sqm": land,
                "internal_area_sqm": internal, "sale_method": sale_method})

            price = float(predict(features)[0])
            mape = bundle["cv_mape"] / 100
            st.metric("Predicted sale price", f"${price:,.0f}")
            st.write(rf"**Likely range:** \${price * (1 - mape):,.0f} — \${price * (1 + mape):,.0f}")
            st.caption(
                f"The range is the model's cross-validated mean absolute percentage error "
                f"(±{bundle['cv_mape']:.1f}%). It describes typical error, not a guarantee — "
                f"about half of properties fall outside a band this wide."
            )
            if price > 4_000_000:
                st.warning(
                    "Above about $4M this model reads low. Every one of its five largest "
                    "errors was an expensive house it under-priced, by up to 49%. Treat this "
                    "number as a floor, not an estimate."
                )
        else:
            st.info("Enter the property details and select **Estimate price**.")

# ----------------------------------------------------------------- batch
with batch:
    st.subheader("Value several properties at once")
    st.write(
        "Upload a CSV with the columns `suburb`, `property_type`, `bedrooms`, `bathrooms` "
        "and `car_spaces`. `land_size_sqm`, `internal_area_sqm` and `sale_method` are used "
        "when present."
    )
    upload = st.file_uploader("CSV file", type="csv")

    if upload is not None:
        raw = pd.read_csv(upload)
        required = {"suburb", "property_type", "bedrooms", "bathrooms", "car_spaces"}
        missing = required - set(raw.columns)
        if missing:
            st.error(f"Missing required column(s): {', '.join(sorted(missing))}")
        else:
            frames = pd.concat([build_features(r) for r in raw.to_dict("records")],
                               ignore_index=True)
            out = raw.copy()
            out["predicted_price"] = predict(frames).round(-3)
            st.success(f"Valued {len(out)} properties.")
            st.dataframe(out.style.format({"predicted_price": "${:,.0f}"}),
                         use_container_width=True)
            st.download_button("Download predictions",
                               out.to_csv(index=False).encode("utf-8"),
                               "predicted_prices.csv", "text/csv")

# ----------------------------------------------------------------- about
with about:
    st.subheader("About this model")
    st.markdown(rf"""
**Model.** {bundle['model_name']}, selected by five-fold cross-validated mean absolute error on
the training set. The test set was held out and used only for the final evaluation.

**Training data.** {bundle['trained_on']} properties sold in {', '.join(bundle['suburbs'])}
between {bundle['date_min']} and {bundle['date_max']}, collected manually from Domain listings.

**Typical error.** ±{bundle['cv_mape']:.1f}% (cross-validated MAPE), about
\${bundle['cv_mae']:,.0f} in absolute terms.

**What it predicts.** The model predicts the logarithm of sale price and the result is converted
back to dollars, because prices are strongly right-skewed across these three suburbs.

### Limitations — please read before relying on a number

- It knows **only these three suburbs**. A prediction for anywhere else is meaningless.
- **It under-prices the top of the market.** All five of its largest errors were expensive
  houses, under-predicted by 29% to 49%. Above roughly \$4M, treat its number as a floor.
- **It is least reliable in Chatswood** (29% average error, against 16% in Bondi and 13% in
  Penrith), because three quarters of Chatswood sales are advertised without a price and so
  could not be collected.
- It cannot see condition, renovation quality, aspect, outlook, noise or strata levies. None of
  that is published on the results pages the data came from.
- It was trained on roughly two hundred sales in a single seven-month window, so it cannot
  see a changing market and it will age.

This is a student project. It is not a valuation, and it should not be used to make a financial
decision.
""")
