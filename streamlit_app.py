
# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests
from urllib.parse import quote   # <-- required for spaces & parentheses

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

# Load fruit list
my_dataframe = session.table("smoothies.public.fruit_options").select(
    col('FRUIT_NAME'),
    col('SEARCH_ON')
)

# Convert to pandas to allow .loc usage
pd_df = my_dataframe.to_pandas()

# Fruit multiselect
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    my_dataframe,
    max_selections=5
)

# If fruits selected
if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:

        ingredients_string += fruit_chosen + ' '

        # Pull correct API name from SEARCH_ON
        search_on = pd_df.loc[
            pd_df['FRUIT_NAME'] == fruit_chosen,
            'SEARCH_ON'
        ].iloc[0]

        st.write('The search value for ', fruit_chosen, ' is ', search_on, '.')

        st.subheader(f"{fruit_chosen} Nutrition Information")

        # -----------------------------
        # FIX: URL encode names like "Ximenia (Hog Plum)"
        encoded_name = quote(str(search_on))
        url = f"https://my.smoothiefroot.com/api/fruit/{encoded_name}"
        # -----------------------------

        # Call API
        resp = requests.get(url, timeout=10)

        # Safe JSON parse
        try:
            data = resp.json()
        except Exception:
            st.error("Could not parse response from SmoothieFroot.")
            st.caption(f"URL attempted: {url}")
            st.code(resp.text[:500], language="text")
            continue

        # API returned message like {"error": "..."}
        if isinstance(data, dict) and "error" in data:
            st.warning(data["error"])
            st.caption(f"URL attempted: {url}")
            continue

        # -----------------------------
        # FIX: Always display a clean horizontal table
        row = {}

        # Copy non-nutrition fields
        for key, value in data.items():
            if key != "nutrition":
                row[key] = value

        # Flatten nutrition dict
        nutrition = data.get("nutrition", {})
        if isinstance(nutrition, dict):
            for k, v in nutrition.items():
                row[k] = v

        # Display flat row table
        st.dataframe([row], use_container_width=True)
        # -----------------------------

    # Insert order into Snowflake
    my_insert_stmt = (
        "INSERT INTO smoothies.public.orders(ingredients, name_on_order) "
        f"VALUES ('{ingredients_string}', '{name_on_order}')"
    )

    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success(f"Your Smoothie is ordered, {name_on_order}!")
