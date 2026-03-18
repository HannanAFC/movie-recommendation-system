export function DashboardPage({ user })
{
    return (
        <div>
            <h1>Welcome to the Dashboard, {user.username}</h1>
        </div>
    );
}