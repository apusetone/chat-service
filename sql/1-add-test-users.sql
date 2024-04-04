-- ユーザー1: is_name_visibleがtrue
INSERT INTO users (username, email, new_email, notification_type, first_name, last_name, is_name_visible, created_at, updated_at)
VALUES ('user1', 'user1@example.com', NULL, 0, 'Alice', 'Smith', true, now() at time zone 'utc', now() at time zone 'utc');

-- ユーザー2: is_name_visibleがtrue
INSERT INTO users (username, email, new_email, notification_type, first_name, last_name, is_name_visible, created_at, updated_at)
VALUES ('user2', 'user2@example.com', NULL, 1, 'Bob', 'Johnson', true, now() at time zone 'utc', now() at time zone 'utc');

-- ユーザー3: is_name_visibleがfalse
INSERT INTO users (username, email, new_email, notification_type, first_name, last_name, is_name_visible, created_at, updated_at)
VALUES ('user3', 'user3@example.com', NULL, 2, 'Charlie', 'Brown', false, now() at time zone 'utc', now() at time zone 'utc');

-- ユーザー4: is_name_visibleがfalse
INSERT INTO users (username, email, new_email, notification_type, first_name, last_name, is_name_visible, created_at, updated_at)
VALUES ('user4', 'user4@example.com', NULL, 0, 'David', 'Lee', false, now() at time zone 'utc', now() at time zone 'utc');

-- ユーザー5: is_name_visibleがtrue
INSERT INTO users (username, email, new_email, notification_type, first_name, last_name, is_name_visible, created_at, updated_at)
VALUES ('user5', 'user5@example.com', NULL, 1, 'Eva', 'Garcia', true, now() at time zone 'utc', now() at time zone 'utc');

-- ユーザー6: is_name_visibleがfalse
INSERT INTO users (username, email, new_email, notification_type, first_name, last_name, is_name_visible, created_at, updated_at)
VALUES ('user6', 'user6@example.com', NULL, 2, 'Frank', 'Martinez', false, now() at time zone 'utc', now() at time zone 'utc');
