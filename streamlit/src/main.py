import streamlit as st  
import os 
import asyncio 

import utils.utils as utils  
import utils.fast_api_utils as fast_api_utils  
import utils.fe_utils as fe_utils 

def show_new_project_page():
    st.header('Create project', anchor='create-project')
    with st.form("my_form"):
        st.text_input('Add your project name here', key='project_name')
        st.text_area('Add your project description here', key='project_description')
        if st.form_submit_button("Submit"):
            utils.handle_project() 

def show_file_upload_popup():
    with st.form('Popup File Upload'):
        st.file_uploader('Please upload your files',type=['pdf', 'txt'], key='popup_submit_files' ) 
        st.form_submit_button('Submit', on_click=utils.submit_files)    
         
    with st.form('Popup Text Upload'):
        st.text_area('Please add supporting text ', key='popup_manual_text')
        st.form_submit_button('Submit', on_click=utils.submit_manual_text)

def show_project_workspace():
    tab1, tab2 = st.tabs(['Upload Supporting Files/ Text', 'Generate Text'])

    with tab1: 
        st.header('Upload a file', anchor='upload-a-file')
        with st.form('Manual File Upload'):
            st.file_uploader('Please upload your files',type=['pdf', 'txt'], key='submit_files' ) 
            st.form_submit_button('Submit', on_click=utils.submit_files)    
             
        st.header('Manual text upload ')
        with st.form('Manual Text Upload'):
            st.text_area('Please add supporting text ', key='manual_text')
            st.form_submit_button('Submit', on_click=utils.submit_manual_text)

    with tab2:
        project_dict = {x[1]:{'id':x[0], 'name':x[1], 'description':x[2]} for x in st.session_state.projects}
        
        st.header('Select what files you want to use', anchor='select-a-file')
        if st.session_state.get('files'):
            st.multiselect('Select your files that have been uploaded to use as your knowledge base',[x[1] for x in st.session_state.files],key='selected_files')
        else:
            st.write('No files found, please upload files". ')

        st.markdown("### Want more files to work with?")
        if st.button('Add New'):
            with st.expander("Add More Files", expanded=True):
                show_file_upload_popup()

        # Initialize selected_project if not present
        if 'selected_project' not in st.session_state and project_dict:
            st.session_state.selected_project = list(project_dict.keys())[0]

        if st.session_state.get('selected_project') and project_dict and (not st.session_state.get('questions')):
            st.session_state['questions'] = fast_api_utils.get_questions(project_dict[st.session_state.selected_project]) 

        st.header('Input Questions ')
        if st.session_state.get('questions'):
            if st.session_state.get('selected_project') in project_dict:
                if st.session_state.get('selected_files'):
                    fe_utils.render_questions(st.session_state.get('questions'), st.session_state.get('selected_files',[]), project_dict[st.session_state.selected_project])
                else:
                    st.write('No source files selected. You can still view and edit questions, but they will not reference any source files.')
                    fe_utils.render_questions(st.session_state.get('questions'), [], project_dict[st.session_state.selected_project])
            else:
                st.write('Please select a project first.')
        else: 
            st.write('No questions found. Please add a question.')

        st.header('Add New Prompts')
        with st.form("add_question_form"):
            new_question = st.text_area('Add new prompts to Sliverhand here', height=200)
            if st.form_submit_button("Submit"):
                utils.add_question_helper(project_dict, new_question)

        if st.session_state.get('questions'):
            st.header('Save to Database')
            if st.button('Save prompts to DB'):
                with st.spinner(text="In progress..."):
                    parsed_questions = utils.format_questions(st.session_state.questions)
                    if (response := fast_api_utils.save_questions(parsed_questions,project_dict[st.session_state.selected_project])) and response.get('result'):
                        st.toast('Prompts saved!')

def show_archived_project_page():
    if st.session_state.get('projects'):
        st.header('Select project')
        project_dict = {x[1]:{'id':x[0], 'name':x[1], 'description':x[2]} for x in st.session_state.projects}
        st.selectbox('Select your project',project_dict.keys(),on_change=utils.handle_project_select_callback,key='selected_project')
        if selected_project := st.session_state.get('selected_project'):
            st.write(f'Project Description: \n\n  {project_dict.get(selected_project,{}).get("description","")}')
            if st.button('Open Project Workspace'):
                st.session_state.current_page = 'project_workspace'
                st.rerun()
    else:
        st.write('No projects found. Please create a new project first.')

def main():
    st.title('Sliverhand - Your customized AI Essay Writer')

    utils.get_data_from_db(st.session_state.get('projects'),st.session_state.get('files'),st.session_state.get('credentials'))
    fe_utils.check_credentials()

    # Initialize session state for page navigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'landing'

    if st.session_state.current_page == 'landing':
        # Center the buttons using columns
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)  # Add some spacing
            if st.button('New Project', use_container_width=True):
                st.session_state.current_page = 'new_project'
                st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)  # Add spacing between buttons
            
            if st.button('Work on an Archived Project', use_container_width=True):
                st.session_state.current_page = 'archived'
                st.rerun()
    
    elif st.session_state.current_page == 'new_project':
        if st.button('← Back to Home'):
            st.session_state.current_page = 'landing'
            st.rerun()
        show_new_project_page()
    
    elif st.session_state.current_page == 'archived':
        if st.button('← Back to Home'):
            st.session_state.current_page = 'landing'
            st.rerun()
        show_archived_project_page()

    elif st.session_state.current_page == 'project_workspace':
        if st.button('← Back to Projects'):
            st.session_state.current_page = 'archived'
            st.rerun()
        show_project_workspace()

if __name__ == '__main__':
    main()