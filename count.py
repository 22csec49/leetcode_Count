import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime

# --- Function to Fetch LeetCode Data ---
def get_leetcode_data(username):
    """Fetch problem-solving stats from LeetCode using GraphQL."""
    
    url = "https://leetcode.com/graphql"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
    }
    
    graphql_query = {
        "operationName": "getUserProfile",
        "query": """query getUserProfile($username: String!) {
            matchedUser(username: $username) {
                username
                submitStatsGlobal {
                    acSubmissionNum {
                        difficulty
                        count
                    }
                }
            }
        }""",
        "variables": {"username": username},
    }
    
    response = requests.post(url, json=graphql_query, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data.get("data") and data["data"].get("matchedUser"):
            stats = data["data"]["matchedUser"]["submitStatsGlobal"]["acSubmissionNum"]
            return {
                "total": stats[0]["count"],
                "easy": stats[1]["count"],
                "medium": stats[2]["count"],
                "hard": stats[3]["count"],
            }
        else:
            return None  # User not found or profile private
    
    return None  # Failed request

# --- Streamlit UI ---
st.set_page_config(page_title="LeetCode Stats", layout="wide")

# Title and Instructions Section
st.title("📊 LeetCode Stats Tracker")
st.write("Upload a CSV file with names and LeetCode usernames to fetch problem-solving statistics.")
st.write("**Instructions:**")
st.write("- Ensure your file is in CSV format. If your file is in any other format, convert it to CSV before uploading.")
st.write("- Your CSV should have two columns: 'NAME' and 'USER NAME'.")

# File Upload Section
uploaded_file = st.file_uploader("Upload CSV File (with 'NAME' and 'USER NAME' columns)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if "NAME" not in df.columns or "USER NAME" not in df.columns:
        st.error("❌ Invalid CSV format! Ensure it has 'NAME' and 'USER NAME' columns.")
    else:
        st.success("✅ File uploaded successfully!")

        # Process usernames
        results = []
        invalid_users = []

        with st.spinner("Fetching LeetCode data..."):
            for _, row in df.iterrows():
                name, username = row["NAME"], row["USER NAME"].strip()
                data = get_leetcode_data(username)

                if data:
                    results.append({"name": name, "username": username, **data})
                else:
                    invalid_users.append({"name": name, "username": username})  # Store name + username

        # Display Results
        if results:
            results_df = pd.DataFrame(results)

            st.subheader("📜 LeetCode Stats")
            st.dataframe(results_df.style.format({"total": "{:,}", "easy": "{:,}", "medium": "{:,}", "hard": "{:,}"}))

            # Convert DataFrame to Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                results_df.to_excel(writer, index=False, sheet_name="LeetCode Stats")
            output.seek(0)

            # Generate Filename with Date
            current_date = datetime.now().strftime("%Y-%m-%d")
            filename = f"leetcode_results_{current_date}.xlsx"

            # Download Button
            st.download_button(
                label="📥 Download Excel File",
                data=output,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # Display Invalid Users
        if invalid_users:
            invalid_df = pd.DataFrame(invalid_users)
            st.subheader("⚠️ Invalid or Private Profiles")
            st.write("These users were not found or have private profiles:")
            st.dataframe(invalid_df)
