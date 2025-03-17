import streamlit as st
import pandas as pd
from azure.identity import ClientSecretCredential
from azure.storage.filedatalake import DataLakeServiceClient
import io
import gzip

storage_account = "jonoaoedlext"
container = "dev"
file_path = "consumption/vw_opponent_civ_analysis.csv.gz"  # Path to the file in ADLS2

# Title of the Streamlit app
st.title("Age of Empires 2 Analysis")

# Retrieve secrets from Streamlit's secrets.toml
my_db_name = st.secrets["DB_USERNAME"]
client_id = st.secrets["azure_client_id"]
tenant_id = st.secrets["azure_tenant_id"]
client_secret = st.secrets["azure_client_secret"]

# Create a credential object for Azure authentication
adls2_credential = ClientSecretCredential(
    tenant_id=tenant_id,
    client_id=client_id,
    client_secret=client_secret
)

# Function to download a file from ADLS2 and load it into a pandas DataFrame
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


def create_unique_field_list(df, field):
    result = st.multiselect(
    f"{field.title()}:"
    ,options=df[field].sort_values().unique()
    ,default=df[field].sort_values().unique() #Selects all by default
    )
    return result


tab1, tab2, tab3 = st.tabs(["Player Leaderboard", "Civ Counter-picker", "Civ Performance"])

with tab1:
    st.write('Hello')
with tab2:
    filter_col1, _, filter_col2 = st.columns([5,1,5])
    # Download the file and load it into a DataFrame
    df = download_file_from_adls2(adls2_credential, storage_account, container, file_path)
    
    if df is not None:
        # Display the DataFrame in Streamlit
        st.write("File downloaded successfully!")
        st.dataframe(df)
    else:
        st.write("Failed to download the file.")


    with filter_col1:
        V_STATUS = create_unique_field_list(df, "civ")
    with filter_col2:
        subject_search = st.text_input("Player Search").lower()

with tab3:
    st.title('Feedback Requests Status')
    st.warning("#### View your Submitted Feedback Requests here and track their status!")
    st.markdown("#### 📬 Add your own requests in the 'Feedback' Tab above")

