
# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests
from urllib.parse import quote  # <-- ADDED

st.title('My Parents New Healthy Diner')
st.title(":cup_with_straw: Customize Your Smoothie!:cup_with_straw:")
st.write(
  """Choose the fruits you want in your custome Smoothie!
  """
)

name_on_order = st.text_input('Name on Smoothies:')
st.write('The name on your Smoothie will be:', name_on_order)

# Snowflake connection
cnx = st.connection("snowflake")
session = cnx.session()

# Load Snowflake fruit table
my_dataframe = session.table("smoothies.public.fruit_options").select(
    col('FRUIT_NAME'),
    col('SEARCH_ON')
)

# Convert to pandas
pd_df = my_dataframe.to_pandas()

# Fruit selector
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    my_dataframe,
    max_selections=5
)

# If user selected fruits
if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        # Get the API-compatible name
        search_on = pd_df.loc[
            pd_df['FRUIT_NAME'] == fruit_chosen,
            'SEARCH_ON'
        ].iloc[0]

        st.write('The search value for ', fruit_chosen, ' is ', search_on, '.')

        st.subheader(f"{fruit_chosen} Nutrition Information")

        # ------------------------------------------
        # FIX 1 — Encode search_on safely
        encoded = quote(str(search_on))

        # Build API URL
        url = f"https://my.smoothiefroot.com/api/fruit/{encoded}"

        # Make request
        resp = requests.get(url, timeout=10)

        # FIX 2 — Safe JSON parse
        try:
            data = resp.json()
        except Exception:
            st.error("Could not parse response from SmoothieFroot.")
            st.caption(f"URL: {url}")
            st.code(resp.text[:500], language="text")
            continue

        # FIX 3 — Handle API error messages
        if isinstance(data, dict) and "error" in data:
            st.warning(data["error"])
            st.caption(f"URL attempted: {url}")
            continue

        # ------------------------------------------
        # FIX 4 — Normalize JSON so table is ALWAYS horizontal
        row = {}

        # Top-level fields (except nutrition)
        for key, value in data.items():
            if key != "nutrition":
                row[key] = value

        # Nutrition flattened into columns
        nutrition = data.get("nutrition", {})
        if isinstance(nutrition, dict):
            for k, v in nutrition.items():
                row[k] = v

        # Show clean table
        st.dataframe([row], use_container_width=True)
        # ------------------------------------------

    # Insert order into Snowflake
    my_insert_stmt = (
        "INSERT INTO smoothies.public.orders(ingredients, name_on_order) "
        f"VALUES ('{ingredients_string}', '{name_on_order}')"
    )

    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success(f"Your Smoothie is ordered, {name_on_order}!")
