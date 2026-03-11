import streamlit as st
from snowflake.snowpark.functions import col
import requests
 
st.title('My Parents New Healthy Diner')

# Write directly to the app

st.title(f":cup_with_straw: Customize Your Smoothie!:cup_with_straw:")
st.write(
 """Choose the fruits you want in your custome Smoothie!"""
)

name_on_order= st.text_input('Name on Smoothies:')
st.write ('The name on your Smoothie will be:', name_on_order)


cnx = st.connection("snowflake")
session = cnx.session()

my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'))
#st.dataframe(data=my_dataframe, use_container_width=True)
#st.stop()

#into pandas
#pd_df=my_dataframe.to_pandas()
#st.dataframe(pd_df)
#st.stop()

ingredients_list = st.multiselect(
'Choose up to 5 ingredients:'
, my_dataframe
, max_selections=5
)


if ingredients_list:

    ingredients_string = ''

    for fruit_chosen in ingredients_list:

        ingredients_string += fruit_chosen + ' '
 
        smoothiefroot_response = requests.get("[https://my.smoothiefroot.com/api/fruit/watermelon](https://my.smoothiefroot.com/api/fruit/watermelon)")  
        st.text(smoothiefroot_response)
           

  
 
    my_insert_stmt = (

        "INSERT INTO smoothies.public.orders(ingredients, name_on_order) "

        f"VALUES ('{ingredients_string}', '{name_on_order}')"

    )


    #st.write(my_insert_stmt)

    #st.stop()

    #st.write(my_insert_stmt)

    time_to_insert = st.button('Submit Order')

    if time_to_insert:

        session.sql(my_insert_stmt).collect()

        st.success(f"Your Smoothie is ordered, {name_on_order}!")
 my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'))
#st.dataframe(data=my_dataframe, use_container_width=True)
#st.stop()
#into pandas
pd_df=my_dataframe.to_pandas()
#st.dataframe(pd_df)
#st.stop()
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:'
    , my_dataframe
    , max_selections=5
)

if ingredients_list:
    ingredients_string = ''
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
      
 
 
  
 
    my_insert_stmt = (
        "INSERT INTO smoothies.public.orders(ingredients, name_on_order) "
        f"VALUES ('{ingredients_string}', '{name_on_order}')"
    )

    #st.write(my_insert_stmt)
    #st.stop()
    #st.write(my_insert_stmt)
    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success(f"Your Smoothie is ordered, {name_on_order}!")
