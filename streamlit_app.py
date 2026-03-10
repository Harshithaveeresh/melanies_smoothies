
# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests
from urllib.parse import quote  # Needed for spaces and parentheses

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

# Load fruit table
my_dataframe = session.table("smoothies.public.fruit_options").select(
    col('FRUIT_NAME'),
    col('SEARCH_ON')
)
pd_df = my_dataframe.to_pandas()

# Fruit picker
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    my_dataframe,
    max_selections=5
)

if ingredients_list:
    ingredients_string = ""

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + " "

        search_on = pd_df.loc[
            pd_df["FRUIT_NAME"] == fruit_chosen,
            "SEARCH_ON"
        ].iloc[0]

        st.write("The search value for ", fruit_chosen, " is ", search_on, ".")

        st.subheader(f"{fruit_chosen} Nutrition Information")

        # ---------------------------------------------------------
        # URL encode names like "Ximenia (Hog Plum)"
        encoded = quote(str(search_on))
        url = f"https://my.smoothiefroot.com/api/fruit/{encoded}"
        # ---------------------------------------------------------

        resp = requests.get(url, timeout=10)

        # Try to parse JSON safely
        try:
            data = resp.json()
        except Exception:
            st.error("Could not parse SmoothieFroot response.")
            st.caption(f"URL attempted: {url}")
            continue

        # If API says fruit is not in the database
        if isinstance(data, dict) and "error" in data:
            st.info(f"No nutrition data available for {fruit_chosen}.")
            st.caption(f"URL attempted: {url}")
            continue

        # ---------------------------------------------------------
        # Flatten JSON so table is always horizontal
        row = {}

        # Add top-level fields
        for key, value in data.items():
            if key != "nutrition":
                row[key] = value

        # Add nutrition fields
        nutrition = data.get("nutrition", {})
        if isinstance(nutrition, dict):
            for k, v in nutrition.items():
                row[k] = v

        # Show the clean one-row horizontal table
        st.dataframe([row], use_container_width=True)
        # ---------------------------------------------------------

    # Insert order in Snowflake
    my_insert_stmt = (
        "INSERT INTO smoothies.public.orders(ingredients, name_on_order) "
        f"VALUES ('{ingredients_string}', '{name_on_order}')"
    )

    time_to_insert = st.button("Submit Order")

    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success(f"Your Smoothie is ordered, {name_on_order}!")
