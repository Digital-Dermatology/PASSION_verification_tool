import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os
import pandas as pd

######################################################################################
# Authentication
######################################################################################

with open('./config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    # config['pre-authorized']
)

# Store the initial value of widgets in session state
if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False

authenticator.login()

######################################################################################
# Main
######################################################################################

st.title('PASSION project cleaning tool')

if st.session_state["authentication_status"]:
    authenticator.logout()

    csv_path = r"C:\Users\philippe-navarinilab\Downloads\actual_merged_passion (1).csv"
    df = pd.read_csv(csv_path)

    # Drop duplicate subject_id rows to keep only one row per subject_id
    df_unique = df.groupby('subject_id').agg({
        'img_path': list,
        'country': 'first',
        'Subject': 'first',
        'age': 'first',
        'sex': 'first',
        'fitzpatrick': 'first',
        'body_loc': 'first',
        'impetig': 'first',
        'diagnosis': 'first',
        'icd10': 'first',
        'icd11': 'first',
        'conditions_PASSION': 'first',
        'Split': 'first',
        'lbl_conditions_PASSION': 'first'
    }).reset_index()  # Reset index to make 'subject_id' a column again

    # Function to save data to CSV
    def save_data():
        user = st.session_state["username"]
        user_file = f"{user}_data.csv"
        df_user.to_csv(user_file, index=False)
        # Save the current index
        with open(f"{user}_progress.txt", 'w') as f:
            f.write(str(st.session_state.index))

    # Function to load data from CSV
    def load_data():
        user = st.session_state["username"]
        user_file = f"{user}_data.csv"
        if os.path.exists(user_file):
            return pd.read_csv(user_file)
        else:
            return pd.DataFrame(columns=["subject_id", "img_path", "diags", "descr", "anonym"])

    # Load user data if exists, otherwise create new
    df_user = load_data()

    # Load the user's last progress
    user = st.session_state["username"]
    progress_file = f"{user}_progress.txt"
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            st.session_state.index = int(f.read())
    else:
        st.session_state.index = 0

    if 'navigate' not in st.session_state:
        st.session_state.navigate = False

    PASSION_diags = sorted(list(set(df["conditions_PASSION"].dropna().tolist())))
    diagnoses = sorted(list(set(df["diagnosis"].dropna().tolist())))
    diagnoses.append("Other")
    diagnoses.append("Impetigo")

    st.subheader(f"Case {df_unique.loc[st.session_state.index, 'subject_id']}")

    impetig_encoded = df_unique.loc[st.session_state.index, 'impetig'] == "impetiginized"

    images = df_unique.loc[st.session_state.index, 'img_path']
    key = 1
    for image in images:
        st.write(f"# Image n°{key}")
        image = "D:/PASSION/PASSION_collection_2020_2023/" + image.split("/PASSION_collection_2020_2023/")[-1]
        try:
            st.image(image, use_column_width=True)
        except Exception as e:
            st.error(f"Error loading image: {e}")
            # TODO handle error

        subject_id = df_unique.loc[st.session_state.index, 'subject_id']

        # Extract current description and diagnosis
        current_row = df_user[(df_user["subject_id"] == subject_id) & (df_user["img_path"].apply(lambda x: image in x))]
        if current_row.empty:
            current_desc = ""
            current_diag = []
            anonym = False
        else:
            current_desc = current_row["descr"].values[0] if pd.notna(current_row["descr"].values[0]) else ""
            current_diag = current_row["diags"].values[0].split(",") if pd.notna(current_row["diags"].values[0]) else []
            anonym = True if str(current_row["anonym"].values[0]).lower() == "true" else False

        diagnosis = st.multiselect(f"**If the provided diagnosis is not plausible given the image, add the correct ones.**",
                                   diagnoses, default=current_diag,
                                   key="multiselect" + str(st.session_state.index) + str(key))
        description = st.text_input("**Please, describe the lesion:**", current_desc if current_desc else "The image features...", key="slidebar" + str(st.session_state.index) + str(key))
        problematic = st.checkbox("The image is not correctly anonymized", value=anonym, key="checkbox" + str(st.session_state.index) + str(key))

        # Save the input data
        if current_row.empty:
            new_data = {"subject_id": subject_id, "img_path": image, "diags": ",".join(diagnosis), "descr": description, "anonym": str(problematic)}
            df_user = df_user.append(new_data, ignore_index=True)
        else:
            df_user.loc[current_row.index, "diags"] = ",".join(diagnosis)
            df_user.loc[current_row.index, "descr"] = description
            df_user.loc[current_row.index, "anonym"] = str(problematic)

        key += 1

    st.sidebar.title(f"Case {df_unique.loc[st.session_state.index, 'subject_id']}")
    st.sidebar.text(df_unique.loc[st.session_state.index, 'diagnosis'])
    if impetig_encoded:
        st.sidebar.text("The lesion is impetigenized")
    else:
        st.sidebar.text("The lesion is not impetigenized")

    # Progression bar
    progress = (st.session_state.index + 1) / len(df_unique)
    st.sidebar.progress(progress)
    st.sidebar.text(f"Progress: {st.session_state.index + 1}/{len(df_unique)}")

    col1, col2 = st.sidebar.columns(2)

    if col1.button('Previous'):
        st.session_state.index = (st.session_state.index - 1) % len(df_unique)
        st.session_state.navigate = True
    if col2.button('Next'):
        st.session_state.index = (st.session_state.index + 1) % len(df_unique)
        st.session_state.navigate = True

    # Check if navigation buttons were clicked and set the navigate flag
    if st.session_state.navigate:
        st.session_state.navigate = False
        save_data()

        st.experimental_rerun()

    # Save data before closing the app
    st.button('Save', on_click=save_data)
