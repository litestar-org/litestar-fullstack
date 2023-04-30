--name: users-by-week
select a.week, count(a.user_id) as new_users
from (
    select date_trunc('week', user_account.created) as week, user_account.id as user_id
    from user_account
) a
group by a.week
order by a.week
