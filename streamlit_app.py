
# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests
from urllib.parse import quote   # <-- ADDED

st.title('My Parents New Healthy Diner')
st.title(f":cup_with_straw: Customize Your Smoothie!:cup_with_straw:")
st.write(
  """Choose the fruits you want in your custome Smoothie!
  """
)

name_on_order= st.text_input('Name on Smoothies:')
st.write ('The name on your Smoothie will be:', name_on_order)

cnx = st.connection("snowflake")
session = cnx.session()

my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'),col('SEARCH_ON'))
pd_df=my_dataframe.to_pandas()

ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    my_dataframe,
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        st.write('The search value for ', fruit_chosen,' is ', search_on, '.')

        st.subheader(fruit_chosen + ' Nutrition Information')

        # -----------------------------------------
        # FIX 1 — URL encode the exact API name
        encoded = quote(str(search_on))

        # FIX 2 — Make the API request
        url = f"https://my.smoothiefroot.com/api/fruit/{encoded}"
        resp = requests.get(url, timeout=10)

        # FIX 3 — Safe JSON parse so NameError never happens
        try:
            data = resp.json()
        except Exception:
            st.error("Could not read nutrition data from SmoothieFroot.")
            st.caption(f"URL attempted: {url}")
            st.code(resp.text[:500], language="text")
            continue   # <-- prevents NameError

        # FIX 4 — Handle {"error": "..."} payloads
        if isinstance(data, dict) and "error" in data:
            st.warning(data["error"])
            st.caption(f"URL attempted: {url}")
            continue

        # FIX 5 — Display clean results
        st.dataframe(data, use_container_width=True)
        # -----------------------------------------

    my_insert_stmt = (
        "INSERT INTO smoothies.public.orders(ingredients, name_on_order) "
        f"VALUES ('{ingredients_string}', '{name_on_order}')"
    )

    time_to_insert = st.button('Submit Order')
    
    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success(f"Your Smoothie is ordered, {name_on_order}!")
