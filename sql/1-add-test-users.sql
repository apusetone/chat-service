-- ユーザー1: is_name_visibleがtrue
INSERT INTO
    users (username, email, new_email, notification_type, first_name, last_name, is_name_visible, created_at, updated_at)
VALUES
    ('user1', 'user1@example.com', NULL, 0, 'Alice', 'Smith', TRUE, NOW() AT TIME ZONE 'utc', NOW() AT TIME ZONE 'utc');

-- ユーザー2: is_name_visibleがtrue
INSERT INTO
    users (username, email, new_email, notification_type, first_name, last_name, is_name_visible, created_at, updated_at)
VALUES
    ('user2', 'user2@example.com', NULL, 1, 'Bob', 'Johnson', TRUE, NOW() AT TIME ZONE 'utc', NOW() AT TIME ZONE 'utc');

-- ユーザー3: is_name_visibleがfalse
INSERT INTO
    users (username, email, new_email, notification_type, first_name, last_name, is_name_visible, created_at, updated_at)
VALUES
    ('user3', 'user3@example.com', NULL, 2, 'Charlie', 'Brown', FALSE, NOW() AT TIME ZONE 'utc', NOW() AT TIME ZONE 'utc');

-- ユーザー4: is_name_visibleがfalse
INSERT INTO
    users (username, email, new_email, notification_type, first_name, last_name, is_name_visible, created_at, updated_at)
VALUES
    ('user4', 'user4@example.com', NULL, 0, 'David', 'Lee', FALSE, NOW() AT TIME ZONE 'utc', NOW() AT TIME ZONE 'utc');

-- ユーザー5: is_name_visibleがtrue
INSERT INTO
    users (username, email, new_email, notification_type, first_name, last_name, is_name_visible, created_at, updated_at)
VALUES
    ('user5', 'user5@example.com', NULL, 1, 'Eva', 'Garcia', TRUE, NOW() AT TIME ZONE 'utc', NOW() AT TIME ZONE 'utc');

-- ユーザー6: is_name_visibleがfalse
INSERT INTO
    users (username, email, new_email, notification_type, first_name, last_name, is_name_visible, created_at, updated_at)
VALUES
    ('user6', 'user6@example.com', NULL, 2, 'Frank', 'Martinez', FALSE, NOW() AT TIME ZONE 'utc', NOW() AT TIME ZONE 'utc');