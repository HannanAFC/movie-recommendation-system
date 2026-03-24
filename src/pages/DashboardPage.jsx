import axios from 'axios';
import { NotFoundPage } from './NotFoundPage';

export function DashboardPage({ user, setUser })
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
                setUser( null );
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