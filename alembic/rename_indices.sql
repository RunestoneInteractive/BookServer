-- *********
-- |docname|
-- *********
-- This should be run before generating the first web2py to BookServer migration.
--
-- TODO:
--
-- -    Should we allow xxx_answers.correct to be NULL? What about xxx_answers.answer? (For example, mchoice_answers.correct or mchoice_answers.answer)?



-- For now, just test these; roll them back at the end.
begin;

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
alter index code_course_id_idx rename to ix_code_course_id;
alter index mchoice_answers_course_name_idx rename to ix_mchoice_answers_course_name;
alter index parsons_answers_course_name_idx rename to ix_parsons_answers_course_name;
alter index unittest_answers_course_name_idx rename to ix_unittest_answers_course_name;
alter index unique_user rename to ix_auth_user_username;


-- Provide reasonable default values where those were lacking.
update assignment_questions set activities_required=0 where activities_required is null;
update assignments set released='F' where released is null;
update assignments set visible='F' where visible is null;
update assignments set from_source='F' where from_source is null;
update auth_user set donated='F' where donated is null;
update auth_user set accept_tcp='F' where accept_tcp is null;
update chapters set chapter_num=999 where chapter_num is null;
update code set language='python' where language is null;
update courses set institution='' where institution is null;
update courses set downloads_enabled='F' where downloads_enabled is null;
update courses set allow_pairs='F' where allow_pairs is null;
update course_instructor set verified='F' where verified is null;
update course_instructor set paid='F' where paid is null;
update questions set from_source='F' where from_source is null;
update grades set manual_total='F' where manual_total is null;
update sub_chapters set sub_chapter_num=999 where sub_chapter_num is null;
update selected_questions set points = 0 where points is null;
update sub_chapters set skipreading = 'F' where skipreading is null;

-- Fix old JS producing NULL, probably when clicking on "check me" before providing an answer.
update mchoice_answers set correct='F' where correct is null;
update mchoice_answers set answer='' where answer is null;
update fitb_answers set correct='F' where correct is null;
update fitb_answers set answer='' where answer is null;
delete from assignment_questions where autograde is null;
delete from assignment_questions where which_to_grade is null;
delete  from clickablearea_answers where course_name not in (select course_name from courses);
delete  from codelens_answers where course_name not in (select course_name from courses);
delete  from dragndrop_answers where course_name not in (select course_name from courses);
delete  from fitb_answers where course_name not in (select course_name from courses);
delete  from mchoice_answers where course_name not in (select course_name from courses);
delete  from unittest_answers where course_name not in (select course_name from courses);
delete  from parsons_answers where course_name not in (select course_name from courses);
delete from timed_exam where course_name not in (select course_name from courses);
delete from code where course_id is null;
delete from dragndrop_answers where min_height is null;
delete from dragndrop_answers where correct is null;
delete from questions where subchapter is null;
delete from useinfo where event is null or act is null or div_id is null or course_id is null;
delete from useinfo where course_id not in (select course_name from courses);
delete from user_state where course_name is null;
delete from user_state where id in (select id from user_state except (select user_state.id from auth_user join user_state on auth_user.id = user_id ) );
-- Delete junk from the database.
delete from courses where base_course is null;

commit;
