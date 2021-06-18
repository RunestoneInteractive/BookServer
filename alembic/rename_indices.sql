-- Rename indices from web2py / rsmanage to sqlalchemy's convention.
alter index course_id_index rename to ix_useinfo_course_id;
alter index div_id_index rename to ix_useinfo_div_id;
alter index event_index rename to ix_useinfo_event;
alter index sid_index rename to ix_useinfo_sid;
alter index timestamp_idx rename to ix_useinfo_timestamp;
alter index assign_course_idx rename to ix_assignments_course;
alter index chapters_course_id_idx rename to ix_chapters_course_id;
alter index code_acid_idx rename to ix_code_acid;
alter index code_sid_idx rename to ix_code_sid;
alter index code_timestamp_idx rename to ix_code_timestamp;
alter index mchoice_answers_div_id_idx rename to ix_mchoice_answers_div_id;
alter index mchoice_answers_sid_idx rename to ix_mchoice_answers_sid;
alter index parsons_answers_div_id_idx rename to ix_parsons_answers_div_id;
alter index parsons_answers_sid_idx rename to ix_parsons_answers_sid;
alter index q_bc_idx rename to ix_questions_base_course;
alter index questions_chapter_idx rename to ix_questions_chapter;
alter index questions_name_idx rename to ix_questions_name;
alter index source_code_acid_idx rename to ix_source_code_acid;
alter index source_code_course_id_idx rename to ix_source_code_course_id;
alter index sub_chapters_chapter_id_idx rename to ix_sub_chapters_chapter_id;
alter index subchap_idx rename to ix_questions_subchapter;
alter index unittest_answers_div_id_idx rename to ix_unittest_answers_div_id;
alter index unittest_answers_sid_idx rename to ix_unittest_answers_sid;
alter index user_sub_chapter_progress_chapter_id_idx rename to ix_user_sub_chapter_progress_chapter_id;
alter index user_sub_chapter_progress_user_id_idx rename to ix_user_sub_chapter_progress_sub_chapter_id;
alter index chap_label_idx rename to ix_sub_chapters_sub_chapter_label;
alter index code_course_id_idx rename to ix_code_course_id;
alter index mchoice_answers_course_name_idx rename to ix_mchoice_answers_course_name;
alter index parsons_answers_course_name_idx rename to ix_parsons_answers_course_name;
alter index unittest_answers_course_name_idx rename to ix_unittest_answers_course_name;
alter index user_sub_chapter_progress_course_name_idx rename to ix_user_sub_chapter_progress_course_name;
alter index unique_user rename to ix_auth_user_username;
alter index courses_course_name_idx rename to courses_course_name_key;


begin;

update assignment_questions set activities_required=0 where activities_required is null;
update assignments set released='F' where released is null;
update assignments set visible='F' where visible is null;
update assignments set from_source='F' where from_source is null;
update auth_user set donated='F' where donated is null;
update auth_user set accept_tcp='F' where accept_tcp is null;
update chapters set chapter_num=999 where chapter_num is null;
update code set language='python' where language is null;
update courses set institution="" where institution is null;
-- TODO: default to downloads disabled?
update courses set downloads_enabled='F' where downloads_enabled is null;

update mchoice_answers set percent=0 where percent is null and correct='F';
update mchoice_answers set percent=1 where percent is null and correct='T';
update fitb_answers set percent=0 where percent is null and correct='F';
update fitb_answers set percent=1 where percent is null and correct='T';
update dragndrop_answers set percent=0 where percent is null and correct='F';
update dragndrop_answers set percent=1 where percent is null and correct='T';
update clickablarea_answers set percent=0 where percent is null and correct='F';
update clickablearea_answers set percent=1 where percent is null and correct='T';
update parsons_answers set percent=0 where percent is null and correct='F';
update parsons_answers set percent=1 where percent is null and correct='T';
update codelens_answers set percent=0 where percent is null and correct='F';
update codelens_answers set percent=1 where percent is null and correct='T';
update unittest_answers set percent=0 where percent is null and correct='F';
update unittest_answers set percent=1 where percent is null and correct='T';

delete from useinfo where div_id is null and course_id is null;
delete from courses where base_course is null;


rollback;
