import axios from 'axios';
import { NotFoundPage } from './NotFoundPage';

export function DashboardPage({ user })
{
    function logout( )
    {
        async function sendLogoutRequest( )
        {
            const response = await axios.get(
                "/api/auth/logout"
            );

            if ( response.data.error )
            {
                alert(response.data.error);
            }
            else
            {
                window.location.href = "/";
            }
        }

        sendLogoutRequest( );
    }   

    return (
        <div>
            <h1>Welcome to the Dashboard, {user.username}</h1>
            <button
                onClick={logout}
            >
                Logout
            </button>
        </div>
    );
}