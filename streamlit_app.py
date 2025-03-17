import streamlit as st
import pandas as pd
from azure.identity import ClientSecretCredential
from azure.storage.filedatalake import DataLakeServiceClient
import io
import gzip
from streamlit import session_state as ss


# ----------------------------------------------------------------------------------------------------------------------
def download_file_from_adls2(adls2_credential, storage_account, container, file_path):
    try:
        # Create a DataLakeServiceClient
        adls2_client = DataLakeServiceClient(
            account_url=f'https://{storage_account}.dfs.core.windows.net',
            credential=adls2_credential
        )
        
        # Get the file system client (container)
        file_system_client = adls2_client.get_file_system_client(file_system=container)
        
        # Get the file client (FIX: use get_file_client() instead of get_path_client())
        file_client = file_system_client.get_file_client(file_path)
        
        # Download the file content
        download = file_client.download_file()
        file_content = download.readall()
        
        # Decompress the file content
        with gzip.GzipFile(fileobj=io.BytesIO(file_content)) as f:
            decompressed_content = f.read()
        
        # Load the decompressed file content into a pandas DataFrame
        df = pd.read_csv(io.StringIO(decompressed_content.decode('utf-8')))
        return df
    except Exception as e:
        st.error(f"Error downloading file: {e}")
        return None



# @st.cache_data
def get_data():
    
    # Adls2 file location
    storage_account = "jonoaoedlext"
    container = "dev"
    file_path = "consumption/vw_opponent_civ_analysis.csv.gz"  

    # Retrieve secrets from Streamlit's secrets.toml
    client_id = st.secrets["azure_client_id"]
    tenant_id = st.secrets["azure_tenant_id"]
    client_secret = st.secrets["azure_client_secret"]

    # Create a credential object for Azure authentication
    adls2_credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )
    
    
    # Download the file and load it into a DataFrame
    df = download_file_from_adls2(adls2_credential, storage_account, container, file_path)
    df['selected'] = True
    if df is not None:
        pass
        # st.toast("Successfuly read data!")
    else:
        st.error("Unable to read data.")
    return df
# ----------------------------------------------------------------------------------------------------------------------




def initialize_state():
    '''Set session_state for filter variables and counter.'''
    for col in categorical_filters:
        if f"{col}_query" not in st.session_state:
            st.session_state[f"{col}_query"] = []

    if "counter" not in st.session_state:
        st.session_state.counter = 0


def reset_state_callback():
    '''Reset session_date for filter variables and counter when button clicked.'''
    st.session_state.counter = 1 + st.session_state.counter
    for col in categorical_filters:
        st.session_state[f"{col}_query"] = []


def query_data(df: pd.DataFrame) -> pd.DataFrame:
    '''For each filtering query, checks each row in the df's corresponding column if it 
        contains the value that is in the session states filter list.
       If there is no match, that row's `selected` value is changed to False.
    '''
    for col in categorical_filters:
        if st.session_state[f"{col}_query"]:
            df.loc[~df[col].isin(st.session_state[f"{col}_query"]), "selected"] = False
    return df


def get_filters(transformed_df: pd.DataFrame):
    '''Splits the page into 2 for both multiselect filters.
        Saves the selection into a dictionary which is used to update session_state filters later.
        Reset button can be used as a shortcut which will reset all filters.    
    '''
    filter1, gap, filter2, gap2, filter3 = st.columns([5,1,5,1,5])
    with filter1:
        opponent_civ_select = st.multiselect(
            label='Select the opponent civ to counter against'
            ,options=sorted(set(transformed_df['opponent_civ'].tolist()))
            ,key=f"opponent_civ_{st.session_state.counter}"
            ,placeholder="ALL - (All values are applied)"
        )

    with filter2:
        map_select = st.multiselect(
            label='Select a map'
            ,options=sorted(set(transformed_df['map'].tolist()))
            ,key=f"map_{st.session_state.counter}"
            ,placeholder="ALL - (All values are applied)"
        )
    
    with filter3:
        match_elo_bucket_select = st.multiselect(
            label='Select the elo range to analyse'
            ,options=sorted(set(transformed_df['match_elo_bucket'].tolist()))
            ,key=f"match_elo_bucket_{st.session_state.counter}"
            ,placeholder="ALL - (All values are applied)"
        )

    

    current_query = {}
    current_query['opponent_civ_query'] = [el for el in opponent_civ_select]
    current_query['map_query'] = [el for el in map_select]
    current_query['match_elo_bucket_query'] = [el for el in match_elo_bucket_select]

    return current_query


def build_graphs(transformed_df):
    '''Filters the dataframe to only retain selected rows.
        Utilising some containserisation, create the graphs and data preview objects.
    '''
    filtered_df = transformed_df[transformed_df['selected'] == True]
    

        # Group and aggregate the data
    df_updated = (
        filtered_df.groupby(['civ', 'opponent_civ'])
        .agg(
            Matches_Played=('matches_played', 'sum'),
            Wins_against_Opponent=('wins', 'sum')
        )
        .reset_index()
    )

    # Calculate the win percentage
    df_updated['Win Percentage against Opponent Civ'] = (
        df_updated['Wins_against_Opponent'] / df_updated['Matches_Played'] * 100
    ).round(2)

    # Rename columns
    df_updated = df_updated.rename(columns={
        'civ': 'Civ',
        'opponent_civ': 'Opponent Civ',
        'Matches_Played': 'Matches Played',
        'Wins_against_Opponent': 'Wins against Opponent Civ'
    })

    
    # Optional: Round the win percentage to a desired number of decimals
    # df_updated['Win Percentage against Opponent Civ'] = df_updated['Win Percentage against Opponent Civ'].round(2)

    # # Reorder columns if necessary
    # df_updated = df_updated[[
    #     'Civ', 'Opponent Civ', 'Matches Played',
    #     'Wins against Opponent Civ', 'Win Percentage against Opponent Civ'
    # ]]




    tab1, tab2 = st.tabs(['Graphs', 'Data'])

    with tab1:
        st.write('This is tab1')
        st.dataframe(df_updated)
        # left, right = st.columns(2)
        # with left:
        #     opponent_civ_bar_chart = st.bar_chart(
        #         data=filtered_df
        #         ,x='opponent_civ'
        #         ,y='kwh'
        #         )

        # with right:
        #     map_bar_chart = st.bar_chart(
        #         data=filtered_df
        #         ,x='map'
        #         ,y='kwh'
        #         )
    with tab2:
        left, right = st.columns(2)
        with left:
            st.write(transformed_df)
        with right:
            st.session_state


def update_state(current_query):
    '''Checks to see if the multi-select options are different to session_state filters.
        If so, then update them accordenly and re-run the script, else do nothing.
    '''
    rerun = False
    for col in categorical_filters:
        if current_query[f'{col}_query'] != st.session_state[f'{col}_query']:
            st.session_state[f'{col}_query'] = current_query[f'{col}_query']
            rerun = True
    if rerun:
        st.rerun()


# tab1, tab2, tab3 = st.tabs(["Player Leaderboard", "Civ Counter-picker", "Civ Performance"])

# with tab1:
#     st.write('Hello')
# with tab2:
#     filter_col1, _, filter_col2 = st.columns([5,1,5])
#     df = get_df()
#     st.dataframe(df)
#     with filter_col1:
#         V_STATUS = create_unique_field_list(df, "opponent_civ")
#     with filter_col2:
#         subject_search = st.text_input("Player Search").lower()

# with tab3:
#     st.title('Feedback Requests Status')
#     st.warning("#### View your Submitted Feedback Requests here and track their status!")
#     st.markdown("#### 📬 Add your own requests in the 'Feedback' Tab above")


st.set_page_config(layout='wide')
categorical_filters = ['opponent_civ', 'map', 'match_elo_bucket']

# Title of the Streamlit app
blank1, main_title, blank2 = st.columns([2,5,2])
top1, gap, main_gap, gap2, top3 = st.columns([1,1,5,1,1])

with top1:
    with st.container(height=75,border=True):
        st.write("Last Updated: Today!")
    # st.button("Last Updated: Today!", use_container_width=True, disabled=True)
with main_gap:
    with st.container(height=75,border=True):
            st.markdown(":blue-background[Age of Empires 2 Analysis]")
    # st.button("Age of Empires 2 Analysis", use_container_width=True)
with top3:
    with st.container(height=75,border=False):
        st.button("Reset All filters", on_click=reset_state_callback, use_container_width=True)



def main():
    initialize_state()
    df = get_data()
    current_query = get_filters(df)
    transformed_df = query_data(df)
    build_graphs(transformed_df)
    update_state(current_query)

main()
