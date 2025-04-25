import streamlit as st  
import os 
import asyncio 

import utils.utils as utils  
import utils.fast_api_utils as fast_api_utils  
import utils.fe_utils as fe_utils 

def show_new_project_page():
    st.header('Create Project', anchor='create-project')
    
    # Store the current project name for later use
    current_project_name = st.session_state.get('project_name', '')
    
    with st.form("my_form", clear_on_submit=True):
        st.text_input('Enter your project name here', key='project_name')
        st.text_area('Enter your project description here', key='project_description')
        if st.form_submit_button("Create"):
            if utils.handle_project():
                # Set the selected project to the newly created one
                if project_name := current_project_name:
                    st.session_state.selected_project = project_name
                    # Navigate to project workspace
                    st.session_state.current_page = 'project_workspace'
                    st.rerun()
            else:
                st.error("Failed to create project. Please try again.")

def show_file_upload_popup():
    with st.form('Popup File Upload'):
        st.file_uploader('Please upload your files',type=['pdf', 'txt'], key='popup_submit_files' ) 
        st.form_submit_button('Submit', on_click=utils.submit_files)    
         
    with st.form('Popup Text Upload'):
        st.text_area('Please add supporting text ', key='popup_manual_text')
        st.form_submit_button('Submit', on_click=utils.submit_manual_text)

def show_project_workspace():
    if not st.session_state.get('projects'):
        st.write('No projects found. Please create a new project first.')
        if st.button('← Back to Home', key='workspace_back_to_home'):
            st.session_state.current_page = 'landing'
            st.rerun()
        return

    project_dict = {x[1]:{'id':x[0], 'name':x[1], 'description':x[2]} for x in st.session_state.projects}
    
    # Initialize selected_project if not present
    if 'selected_project' not in st.session_state and project_dict:
        st.session_state.selected_project = list(project_dict.keys())[0]

    # Ensure the selected project exists in the project dictionary
    if not st.session_state.get('selected_project') or st.session_state.selected_project not in project_dict:
        st.write('Please select a valid project.')
        if st.button('← Back to Projects', key='workspace_back_to_projects'):
            st.session_state.current_page = 'archived'
            st.rerun()
        return

    # Display project information
    st.header(f'Project: {st.session_state.selected_project}')
    st.write(f'Description: {project_dict[st.session_state.selected_project]["description"]}')
    
    st.header('Select what files you want to use', anchor='select-a-file')
    if st.session_state.get('files'):
        st.multiselect('Select your files that have been uploaded to use as your knowledge base',[x[1] for x in st.session_state.files],key='selected_files')
    else:
        st.write('No files found, please upload files. ')

    st.markdown("### Want more files to work with?")
    if st.button('Add New'):
        with st.expander("Add More Files", expanded=True):
            show_file_upload_popup()

    # Initialize questions for the selected project
    if not st.session_state.get('questions'):
        st.session_state['questions'] = fast_api_utils.get_questions(project_dict[st.session_state.selected_project]) 

    st.header('Current Prompts')
    if st.session_state.get('questions'):
        if st.session_state.get('selected_files'):
            fe_utils.render_questions(st.session_state.get('questions'), st.session_state.get('selected_files',[]), project_dict[st.session_state.selected_project])
        else:
            st.write('No source files selected. You can still view and edit questions, but they will not reference any source files.')
            fe_utils.render_questions(st.session_state.get('questions'), [], project_dict[st.session_state.selected_project])
    else: 
        st.write('No existing prompts found. Please add a prompt.')

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
        
        # Clear selected project if it was deleted
        if 'selected_project' in st.session_state and st.session_state.selected_project not in project_dict:
            st.session_state.selected_project = None
            
        st.selectbox('Select your project',project_dict.keys(),on_change=utils.handle_project_select_callback,key='selected_project')
        if selected_project := st.session_state.get('selected_project'):
            st.write(f'Project Description: \n\n  {project_dict.get(selected_project,{}).get("description","")}')
            if st.button('Open Project Workspace'):
                st.session_state.current_page = 'project_workspace'
                st.rerun()

        # Add Project Management Section
        st.markdown("---")
        st.header('Manage Projects')
        with st.expander("Project Management", expanded=False):
            # Initialize deletion state if not present
            if 'delete_confirmed' not in st.session_state:
                st.session_state.delete_confirmed = False
            if 'deletion_success' not in st.session_state:
                st.session_state.deletion_success = False
            if 'deleted_count' not in st.session_state:
                st.session_state.deleted_count = 0

            # Show success message if deletion was successful
            if st.session_state.deletion_success:
                st.success(f'Successfully deleted {st.session_state.deleted_count} project(s)!')
                st.session_state.deletion_success = False
                st.session_state.deleted_count = 0
                # Clear any selected projects for deletion
                if 'projects_to_delete' in st.session_state:
                    st.session_state.projects_to_delete = []

            # Multiselect for project deletion
            selected_projects = st.multiselect(
                'Select projects to delete',
                options=[x[1] for x in st.session_state.projects],
                key='projects_to_delete',
                help='Select one or more projects to delete. This action cannot be undone.'
            )

            if selected_projects:
                # Add a confirmation checkbox
                confirm_delete = st.checkbox(
                    'I understand that this action cannot be undone and I want to delete the selected projects',
                    key='confirm_delete',
                    on_change=lambda: setattr(st.session_state, 'delete_confirmed', True)
                )
                
                if st.session_state.delete_confirmed:
                    if st.button('Delete Selected Projects', key='delete_projects_button', type='primary'):
                        with st.spinner('Deleting projects...'):
                            success_count = 0
                            for project_name in selected_projects:
                                project_id = project_dict[project_name]['id']
                                if fast_api_utils.delete_project(project_id):
                                    success_count += 1
                                else:
                                    st.error(f'Failed to delete project "{project_name}"')
                            
                            # Set success state
                            if success_count > 0:
                                st.session_state.deletion_success = True
                                st.session_state.deleted_count = success_count
                                # Clear the selected project if it was deleted
                                if st.session_state.get('selected_project') in selected_projects:
                                    st.session_state.selected_project = None
                            
                            # Reset the deletion state
                            st.session_state.delete_confirmed = False
                            
                            # Refresh the projects data
                            utils.get_data_from_db(st.session_state.get('projects'),st.session_state.get('files'),st.session_state.get('credentials'))
                            st.rerun()
                else:
                    st.button('Delete Selected Projects', key='delete_projects_button', disabled=True)
            else:
                st.button('Delete Selected Projects', key='delete_projects_button', disabled=True)
    else:
        st.write('No projects found. Please create a new project first.')

def main():
    st.title('Sliverhand - Your Customized AI Essay Writer')

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
        if st.button('← Back to Home', key='new_project_back_to_home'):
            st.session_state.current_page = 'landing'
            st.rerun()
        show_new_project_page()
    
    elif st.session_state.current_page == 'archived':
        if st.button('← Back to Home', key='archived_back_to_home'):
            st.session_state.current_page = 'landing'
            st.rerun()
        show_archived_project_page()

    elif st.session_state.current_page == 'project_workspace':
        if st.button('← Back to Projects', key='workspace_back_to_projects_main'):
            st.session_state.current_page = 'archived'
            st.rerun()
        show_project_workspace()

if __name__ == '__main__':
    main()