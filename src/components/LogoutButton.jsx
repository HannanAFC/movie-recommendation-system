import { useState } from 'react';
import { useNavigate } from 'react-router';
import { apiClient } from '../utils/apiClient';
import { FormError } from '../components/FormError';

export function LogoutButton({ setUser })
{
    const [ error, setError ] = useState( null );
    let navigate = useNavigate( );

    async function handleButtonClick( )
    {
        const response = await apiClient.post( "/api/auth/logout" )
        .catch( ( error ) =>              
        {
            if ( error.response.status === 500 )
            {
                setError( "Internal server error." );
            }
            else
            {
                setError( error.response.data.error );
            }
        } );

        if ( response && response.data )
        {
            setUser( null );
            navigate( "/" );
        }
    }

    return (
        <>
            <button
                className="active:scale-95 cursor-pointer justify-center bg-willow-green-600 hover:bg-willow-green-700 active:bg-willow-green-800 dark:active:bg-willow-green-200 dark:hover:bg-willow-green-300 dark:bg-willow-green-400 text-white dark:text-black py-1 px-4 text-sm font-semibold rounded-md flex items-center shadow-md transition-[background-color,scale]"
                onClick={handleButtonClick}
            >
                Logout
            </button>
            <FormError error={error} />
        </>
    );
}