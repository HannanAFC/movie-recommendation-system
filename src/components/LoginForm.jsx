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
            const response = await axios.postForm( "/api/auth/login", formData )
            .catch( ( error ) =>
            {
                if ( error.response.status === 500 )
                {
                    alert( "Internal server error." );
                }
                else
                {
                    alert( error.response.data.error )
                }
            } );

            if ( response && response.data )
            {
                window.location.href = "/dashboard";
            }
        }

        e.preventDefault( );

        if ( username && password )
        {
            const formData = new FormData( );
            formData.append( "username", username );
            formData.append( "password", password );
            login( formData );
        }
        else
        {
            alert( `Please enter a ${ !username ? "username" : "password" }` );
        }
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