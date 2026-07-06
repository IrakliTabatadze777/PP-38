import streamlit as st

# st.title('Streamlit App')
#
# st.header('Welcome to Streamlit')
# st.button('Click me')
#
# st.subheader("Subheader")
#
# st.text("Plain text")
#
# st.markdown("**Bold** and *italic*")
#
# st.markdown("""
# ```python
# import random
# random_number = random.randint(1, 100)
# """)


# name  = st.text_input("Enter your name")
# age   = st.slider("Your age", 0, 100, 25)
# color = st.selectbox("Favorite color",
#           ["Red", "Green", "Blue"])
# agree = st.checkbox("I agree")
# file  = st.file_uploader("Upload a CSV")
# clicked = st.button("Click me")
# date  = st.date_input("Pick a date")


# col1, col2, col3, col4, col5 = st.columns(5)
#
# with col1:
#     st.write("Left")
#
# with col2:
#     st.write("Right")
#
# with col3:
#     st.write("Left")
#
# with col4:
#     st.write("Right")
#
# with col5:
#     st.write("Left")


# st.sidebar.title("Settings")
#
# option = st.sidebar.radio(
#   "View", ["Home","About",'about us', 'contact', 'subscription'])
#
# inp = st.sidebar.text_input("Enter your name")


# tab1, tab2 = st.tabs(
#     ["Data", "Chart"])
# with tab1:
#     st.write("Data view")


# with st.expander("Details"):
#     st.write("Hidden content revealed on click")
#     st.write("Hidden content revealed on click")
#     st.write("Hidden content revealed on click")
#     st.write("Hidden content revealed on click")
#     st.write("Hidden content revealed on click")
    # st.write("Hidden content revealed on click")



# import pandas as pd
# df = pd.DataFrame({
#     "x": range(10),
#     "y": range(10, 20)
# })
#
#
# st.dataframe(df)  # interactive
# # st.table(df)      # static
#
# st.line_chart(df)
# st.bar_chart(df)
# st.area_chart(df)


# st.metric(
#     label="Bitcoin",
#     value="$1.2M",
#     delta="-5%"
# )


# if "counter" not in st.session_state:
#     st.session_state.counter = 0
#
# if st.button("Increment"):
#     st.session_state.counter += 1
#
# st.write("Count:", st.session_state.counter)



import pandas as pd

st.title("CSV Explorer")

uploaded_file = st.file_uploader(
    "Upload CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.dataframe(df)

    column = st.selectbox(
        "Choose a column",
        df.columns)
    #
    st.line_chart(df[column])
    st.write(df[column].describe())