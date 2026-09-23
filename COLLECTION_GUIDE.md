# 8.1D - Property Data Collection Guide

Fill in `data/sydney_properties_template.csv`. Target: **at least 100 properties, minimum 30 per suburb**
(Bondi, Chatswood, Penrith). Aim for ~40 each = 120 total, so you have slack if some rows turn out unusable.

Delete the three `EXAMPLE - ` rows when you start. (The notebook drops them automatically if you forget.)

## Where to get the data

Domain is easier to collect from than realestate.com.au:

1. Go to `domain.com.au` -> **Sold** tab
2. Search the suburb, e.g. "Bondi NSW 2026"
3. Filter: **Sold in the last 12 months** (keeps the time trend meaningful and the market comparable)
4. Each card shows price, beds, baths, car, and property type. Click through for land size and the agent blurb.

Collect a **mix of property types and sizes** in each suburb. If you only take 4-bedroom houses in Penrith
and 2-bedroom units in Bondi, the model cannot separate "suburb" from "property size" - that confound will
show up in Part 4 and weaken the whole report.

## Columns

| Column | Required | Notes |
|---|---|---|
| `property_id` | yes | 1, 2, 3, ... just number the rows |
| `suburb` | yes | Exactly `Bondi`, `Chatswood`, or `Penrith` - consistent spelling matters |
| `address` | yes | Street address. Provenance for your tutor; not used as a model feature |
| `property_type` | yes | `House`, `Apartment`, `Townhouse`, `Villa`, `Semi`, or `Duplex` |
| `bedrooms` | yes | Whole number |
| `bathrooms` | yes | `1.5` is fine |
| `car_spaces` | yes | `0` if none - leave blank only if genuinely not stated |
| `land_size_sqm` | if shown | Houses usually show it; apartments usually do not. Blank is fine |
| `internal_area_sqm` | if shown | Often given for apartments |
| `sale_price` | yes | **Digits only** - `1850000`, not `$1,850,000`. Skip "price withheld" listings |
| `sale_date` | yes | `YYYY-MM-DD` |
| `sale_method` | if shown | `Auction` or `Private treaty` |
| `days_on_market` | if shown | Blank if not listed |
| `distance_to_station_km` | optional | Google Maps, walking distance to nearest train station, 1 decimal |
| `agent_description` | worth it | First 2-3 sentences of the blurb. **Wrap in "double quotes"** |
| `listing_url` | yes | Link to the sold listing |

## Three things that will cost you marks if you get them wrong

1. **Blank, never zero, for unknown.** A blank means "not stated"; a `0` means "genuinely none". Writing `0`
   for an unknown land size tells the model an apartment sits on zero square metres of land, which is a
   fabricated fact. `car_spaces` is the one place `0` is usually real.
2. **Do not skip the expensive or odd properties.** It is tempting to leave out the $8M Bondi penthouse
   because it looks like an outlier. Those properties are exactly what Part 4 is about.
3. **Keep the URL.** The task is marked partly on reproducibility, and a Viva may ask you to open one.

`agent_description` is the highest-value optional column - the task explicitly rewards using the text.
It costs you one copy-paste per property and it gives you real feature engineering to write about
(renovation and view keywords, description length as a proxy for how hard the agent is selling).

## When you are done

Save as CSV (**not** .xlsx) and tell me. Everything else is already built and will run against it.
