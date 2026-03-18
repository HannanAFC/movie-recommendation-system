import { useState } from 'react';
import axios from 'axios';

export function LoginForm( )
{
    const [ username, setUsername ] = useState( "" );
    const [ password, setPassword ] = useState( "" );

    function handleUsernameChange( e )
    {
        setUsername( e.target.value );
    }

    function handlePasswordChange( e )
    {
        setPassword( e.target.value );
    }

    function handleFormSubmit( e )
    {
        async function login( formData )
        {
            const response = await axios.postForm( "/api/auth/login", formData );
            if ( response.data.error )
            {
                alert( response.data.error );
            }
            else if ( response.data.access_token )
            {
                sessionStorage.setItem( "access_token", response.data.access_token );
                window.location.href = "/dashboard";
            }
        }

        e.preventDefault( );

        const formData = new FormData( );
        formData.append( "username", username );
        formData.append( "password", password );
        login( formData );
    }
    
    return (
        <form onSubmit={handleFormSubmit}>
            <input
                id="username"
                type="text"
                placeholder="Username"
                onChange={handleUsernameChange}
                value={username}
            />
            <input
                id="password"
                type="password"
                placeholder="Password"
                onChange={handlePasswordChange}
                value={password}
            />
            <button
                type="submit"
            >
                Login
            </button>
        </form>
    );
}