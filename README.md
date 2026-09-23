# SIT720 8.1D — Sydney Housing Price Prediction and Decision Support System

Jason Hu (219220123)

Predicts the sale price of a residential property in **Bondi**, **Chatswood** or **Penrith** from its
suburb, physical characteristics and the agent's description, and serves the model as a web app.

## Contents

| Path | What it is |
|---|---|
| `8.1D.ipynb` | The full analysis, Parts 1-6 |
| `data/sydney_properties.csv` | The hand-collected dataset (100+ sold properties) |
| `data/llm_valuation_prompt.txt` | Prompt given to the LLM in Part 5 (written by the notebook) |
| `data/part5_estimates_blank.csv` | Template for the Part 5 human and LLM estimates |
| `data/part5_estimates_filled.csv` | Those estimates, filled in |
| `app/app.py` | Streamlit decision support application |
| `app/price_model.joblib` | Trained pipeline, written by Part 6 of the notebook |
| `app/requirements.txt` | Python dependencies |
| `COLLECTION_GUIDE.md` | How the dataset was collected and what each column means |

## Reproducing the analysis

```bash
pip install -r app/requirements.txt
jupyter notebook 8.1D.ipynb        # Run All, top to bottom
```

Run the notebook from **this folder**, so that the relative paths `data/` and `app/` resolve. Part 6
writes `app/price_model.joblib`, which the application needs — so run the notebook before the app.

## Running the application

```bash
python -m streamlit run app/app.py
```

(Use `python -m streamlit` rather than a bare `streamlit`; the console script is not
always on PATH after a `pip install`.)

It opens at `http://localhost:8501`.

**Estimate one property** — choose the suburb and property type, set bedrooms, bathrooms and car
spaces, tick the boxes for land or internal area if you know them, optionally paste the agent's
description, then select **Estimate price**. The app returns a predicted price and a likely range
based on the model's cross-validated error.

**Upload a CSV** — value many properties at once. The file needs `suburb`, `property_type`,
`bedrooms`, `bathrooms` and `car_spaces` as a minimum; `land_size_sqm`, `internal_area_sqm`,
`distance_to_station_km`, `sale_method` and `agent_description` are used when present. Predictions
can be downloaded as a CSV.

**About this model** — the model in use, what it was trained on, its typical error, and its
limitations.
