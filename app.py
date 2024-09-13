import streamlit as st
import pandas as pd
from openai_api import generate_content
from image_generator import generate_image
from seo_generator import generate_seo
from wordpress_api import publish_post, edit_post, delete_post
from process_websites import process_websites
from utils import load_website_credentials
from config import *

st.set_page_config(
    page_title="WordFlow: Advanced WordPress Content Orchestrator", layout="wide"
)

st.title("WordFlow: Advanced WordPress Content Orchestrator")

# Sidebar for global settings
st.sidebar.header("Global Settings")
language = st.sidebar.selectbox("Language", ["English", "Spanish", "French", "German"])
ai_model = st.sidebar.selectbox("AI Model", ["GPT-3.5", "GPT-4"])
scheduling_option = st.sidebar.selectbox("Scheduling", ["Publish Now", "Schedule"])

# Main content area with tabs
tab1, tab2, tab3, tab4 = st.tabs(
    ["Content Generation", "Post Editing", "Post Deletion", "Bulk Operations"]
)

with tab1:
    st.header("Content Generation")

    keyword = st.text_input("Enter keyword for content generation")

    if st.button("Generate Content"):
        with st.spinner("Generating content..."):
            content = generate_content(keyword, ai_model, language)
            st.write(content)

        with st.spinner("Generating image..."):
            image_url = generate_image(keyword)
            st.image(image_url)

        with st.spinner("Generating SEO metadata..."):
            seo_data = generate_seo(content)
            st.write(seo_data)

        if st.button("Publish to WordPress"):
            website_credentials = load_website_credentials()
            selected_site = st.selectbox(
                "Select WordPress site", list(website_credentials.keys())
            )

            if scheduling_option == "Schedule":
                scheduled_date = st.date_input("Select publication date")
                scheduled_time = st.time_input("Select publication time")
            else:
                scheduled_date = None
                scheduled_time = None

            with st.spinner("Publishing to WordPress..."):
                publish_result = publish_post(
                    website_credentials[selected_site],
                    content,
                    seo_data,
                    image_url,
                    scheduled_date,
                    scheduled_time,
                )
                st.success(f"Published to {selected_site}: {publish_result}")

with tab2:
    st.header("Post Editing")

    website_credentials = load_website_credentials()
    selected_site = st.selectbox(
        "Select WordPress site", list(website_credentials.keys())
    )

    post_id = st.number_input("Enter post ID to edit", min_value=1)

    if st.button("Fetch Post"):
        # Implement logic to fetch post content
        st.info("Fetching post...")
        # Display fetched post content for editing

    edited_content = st.text_area("Edit post content", height=300)

    if st.button("Update Post"):
        with st.spinner("Updating post..."):
            update_result = edit_post(
                website_credentials[selected_site], post_id, edited_content
            )
            st.success(f"Post updated: {update_result}")

with tab3:
    st.header("Post Deletion")

    website_credentials = load_website_credentials()
    selected_site = st.selectbox(
        "Select WordPress site", list(website_credentials.keys())
    )

    post_id = st.number_input("Enter post ID to delete", min_value=1)

    if st.button("Delete Post"):
        confirm = st.checkbox("I confirm that I want to delete this post")
        if confirm:
            with st.spinner("Deleting post..."):
                delete_result = delete_post(website_credentials[selected_site], post_id)
                st.success(f"Post deleted: {delete_result}")
        else:
            st.warning("Please confirm deletion")

with tab4:
    st.header("Bulk Operations")

    uploaded_file = st.file_uploader("Upload CSV file", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write(df)

        if st.button("Process Bulk Operations"):
            with st.spinner("Processing bulk operations..."):
                results = process_websites(df)
                st.success("Bulk operations completed successfully")
                st.write(results)

# Footer
st.markdown("---")
st.write("WordFlow v1.0")
